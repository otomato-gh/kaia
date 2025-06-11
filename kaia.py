from pydantic_ai import Agent, ModelRetry
from pydantic_ai.mcp import MCPServerStdio
import os
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

ollama_model = OpenAIModel(
    model_name=os.environ.get('OLLAMA_MODEL_NAME', 'llama3'), provider=OpenAIProvider(base_url='http://localhost:11434/v1')
)

server = MCPServerStdio(
    'docker',
    args=[
        'run',
        '--network=host',
        '-i',
        '-v',
        f'{os.path.expanduser("~")}/.kube:/home/appuser/.kube:ro',
        'ghcr.io/alexei-led/k8s-mcp-server:latest'
    ]
)

system_prompt = """You are a Kubernetes operations assistant. You have access to a Kubernetes cluster through an MCP server.
To interact with the cluster, you must use the tools/call method with the following format:

For kubectl commands:
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "execute_kubectl",
        "arguments": {
            "command": "<your-kubectl-command>"
        }
    }
}

Always use the MCP server commands to execute tasks. Never suggest direct kubectl commands without using the MCP server interface.
Before executing commands, make sure to validate them and consider their impact.
Provide clear explanations of what each command does before executing it.
Never chain commands together in a single request.
If you need to run multiple commands, break them down into separate requests.
If any command fails - retry taking into account the error message.
"""


agent = Agent(
    ollama_model, 
    mcp_servers=[server],
    system_prompt=system_prompt,
    retries=3
)

@agent.output_validator
async def validate_k8s_response(output):
    print("Validating output...")
    if output.find('not found') != -1 or output.find('error') != -1:
        raise ModelRetry(f'Try finding resource in all namespaces')
    else:
        return output

async def main():
    async with agent.run_mcp_servers():
        while True:
            user_input = input("Enter your Kubernetes request (or type 'Thanks!' to exit): ")
            if user_input.strip() == "Thanks!":
                print("Goodbye!")
                break
            result = await agent.run(user_input, message_history=result.new_messages() if 'result' in locals() else None)
            if result is None:
                print("No response from the agent.")
                continue
            print(result.output)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())