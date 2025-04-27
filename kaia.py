import warnings
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools, create_mcp_server_session

from llm import get_llm
#from k8s_tools import call_kubectl, call_shell
import asyncio
import sys
import os
from autogen_core.tools import FunctionTool



async def ainput(string: str) -> str:
    await asyncio.to_thread(sys.stdout.write, f'{string}')
    return await asyncio.to_thread(sys.stdin.readline)

async def main():
  # Define the model client. 
  model_client=get_llm()


  k8s_mcp_server = StdioServerParams(command="docker", 
                                     args=['run',
                                          '--network=host',
                                          '-i',
                                          '-v',
                                          f'{os.path.expanduser("~")}/.kube:/home/appuser/.kube:ro',
                                          'k8s-mcp-server:latest'
                                        ],
                                        read_timeout_seconds=60)

  print("MCP server started. Waiting for it to be ready...")
  tools = await mcp_server_tools(k8s_mcp_server)

  # Define an AssistantAgent with the model, tool, system message, and reflection enabled.
  # The system message instructs the agent via natural language.
  agent = AssistantAgent(
      name="k8s_agent",
      model_client=model_client,
      tools=tools,
      system_message="""You are a Kubernetes troubleshooting agent.
        When asked about a resource but no namespace is specified - you can use all available tools to find the correct namespace.
        If the resource is a pod -  you MUST inspect the pod's logs for issues.
        The correct command to do that is: kubectl logs <pod_name> -n <namespace>.
        If a resource is not found in any namespace, inform me that the pod was not found.
      """,
      reflect_on_tool_use=True
      )

  user_proxy = UserProxyAgent("user_proxy", input_func=input)

  termination_condition = TextMentionTermination("Thanks!")
  team = RoundRobinGroupChat(
      [agent, user_proxy],
      termination_condition=termination_condition,
  #    max_turns=8
  )
  print("What do you want to know?"); 
  prompt = await ainput("Prompt:\n")
  # Ignoring warnings to clean up the output. 
  with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    async for message in team.run_stream(task=prompt):  # type: ignore
      if type(message).__name__ == "TextMessage" or type(message).__name__ == "UserInputRequestedEvent":
        if message.source not in ["user_proxy", "user"]:
          print(message.content)
          print("Type 'Thanks!' if you're done.\n")


asyncio.run(main())
