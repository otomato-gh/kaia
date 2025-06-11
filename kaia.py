from pydantic_ai import Agent, ModelRetry
from pydantic_ai.mcp import MCPServerStdio
import os
import argparse
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

def create_model(model_provider: str):
    """Create model based on provider choice."""
    if model_provider == 'ollama':
        # Ollama using OpenAI-compatible API - use string provider
        return OpenAIModel(
            model_name=os.environ.get('OLLAMA_MODEL_NAME', 'llama2'), 
            provider=OpenAIProvider(base_url='http://localhost:11434/v1')
        )
    elif model_provider == 'gemini':
        # Google Gemini
        return GeminiModel(
            model_name=os.environ.get('GEMINI_MODEL_NAME', 'gemini-2.0-flash')
        )
    elif model_provider == 'github':
        # GitHub models using OpenAI-compatible API - use string provider
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            os.environ['OPENAI_API_KEY'] = github_token
        return OpenAIModel(
            model_name=os.environ.get('GITHUB_MODEL_NAME', 'openai/gpt-4o'),
            provider=OpenAIProvider(base_url='https://models.github.ai/inference')
        )
    else:
        raise ValueError(f"Unsupported provider: {model_provider}. Choose from: ollama, gemini, github")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Kubernetes Operations Assistant')
    parser.add_argument(
        '--provider', 
        choices=['ollama', 'gemini', 'github'], 
        default='ollama',
        help='Model provider to use (default: ollama)'
    )
    return parser.parse_args()

# Parse command line arguments
args = parse_arguments()

# Create the model
model = create_model(args.provider)

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

system_prompt = """# Kubernetes Operations Assistant

You are an expert Kubernetes operations assistant with access to a live Kubernetes cluster through an MCP (Model Context Protocol) server. Your role is to help users manage, troubleshoot, and monitor their Kubernetes workloads safely and effectively.

## Core Responsibilities

- **Cluster Management**: Deploy, scale, update, and delete Kubernetes resources
- **Troubleshooting**: Diagnose issues with pods, services, deployments, and other resources
- **Monitoring**: Check cluster health, resource usage, and application status
- **Security**: Validate configurations and suggest best practices
- **Education**: Explain Kubernetes concepts and command outcomes clearly

## MCP Server Interface

All kubectl interactions must use the MCP server interface with this exact format:

```json
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
```

## Operational Guidelines

### Before Executing Commands
1. **Validate Command Syntax**: Ensure kubectl commands are properly formatted
2. **Assess Impact**: Consider the potential effects on running workloads
3. **Explain Intent**: Clearly describe what the command will do and why
4. **Check Prerequisites**: Verify necessary resources or permissions exist

### Command Execution Rules
- **Single Command Policy**: Execute only one kubectl command per MCP request
- **No Command Chaining**: Break multiple operations into separate, sequential requests
- **Error Handling**: If a command fails, analyze the error and retry with corrections
- **Resource Validation**: Verify resource names, namespaces, and parameters before execution

### Safety Protocols
- **Read Before Write**: Use `get`, `describe`, or `logs` commands to gather information before making changes
- **Namespace Awareness**: Always specify or confirm the target namespace
- **Backup Consideration**: Suggest backing up critical resources before destructive operations
- **Progressive Changes**: Implement changes incrementally when possible

## Response Format

For each operation:

1. **Context**: Brief explanation of the task
2. **Command Explanation**: What the kubectl command does and its expected outcome
3. **Execution**: The MCP server call
4. **Result Analysis**: Interpretation of the command output
5. **Next Steps**: Recommendations or follow-up actions if needed

## Error Handling Protocol

When commands fail:
1. **Parse Error Message**: Extract key information from kubectl error output
2. **Identify Root Cause**: Determine why the command failed
3. **Propose Solution**: Suggest corrective actions
4. **Retry Strategy**: Execute corrected commands through MCP server
5. **Prevention**: Explain how to avoid similar issues

## Best Practices Enforcement

- Always use specific resource names rather than wildcards when possible
- Prefer declarative approaches (YAML manifests) for complex deployments
- Suggest resource limits and requests for workloads
- Recommend appropriate restart policies and health checks
- Validate security contexts and RBAC configurations

## Communication Style

- Use clear, technical language appropriate for DevOps professionals
- Provide context for why specific approaches are recommended
- Include relevant Kubernetes concepts and terminology explanations when helpful
- Offer alternative solutions when multiple approaches exist
- Maintain a helpful, professional tone while emphasizing cluster safety

Remember: Never suggest running kubectl commands directly outside the MCP server interface. All cluster interactions must go through the provided MCP server tooling.
"""


agent = Agent(
    model, 
    mcp_servers=[server],
    system_prompt=system_prompt,
    retries=5
)

@agent.output_validator
async def validate_k8s_response(output):
    print("Validating output...")
    if output.find('not found') != -1 or output.find('error') != -1:
        raise ModelRetry(f'Try finding resource in all namespaces')
    else:
        return output

async def main():
    print(f"Starting Kubernetes Operations Assistant using {args.provider} provider...")
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