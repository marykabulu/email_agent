import os
import asyncio

from dotenv import load_dotenv

from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)

from agents.mcp import MCPServerStdio


# Load our .env file
load_dotenv()


# Get the Grok API key
xai_api_key = os.getenv("XAI_API_KEY")

if not xai_api_key:
    raise ValueError(
        "XAI_API_KEY is missing from the .env file."
    )


# Create a connection to Grok
xai_client = AsyncOpenAI(
    api_key=xai_api_key,
    base_url="https://api.x.ai/v1",
)


# Create the Grok model
grok_model = OpenAIChatCompletionsModel(
    model="grok-4.7",
    openai_client=xai_client,
)


# Disable OpenAI tracing because we are using Grok
set_tracing_disabled(True)


# Create our AI agent
email_agent = Agent(
    name="Email Assistant",

    instructions="""
    You are an email assistant.

    Your job is to help the user understand their emails.

    When reading emails:

    1. Identify the sender.
    2. Identify the subject.
    3. Summarize the important information.
    4. Decide whether the email appears to require a response.
    5. Explain why a response is or is not needed.

    Do not send emails.
    Do not create drafts yet.
    Do not invent information that is not present in the email.
    """,

    model=grok_model,
)


async def main():

    # Start our MCP server
    async with MCPServerStdio(
        name="Email MCP Server",

        params={
            "command": "uv",
            "args": [
                "run",
                "python",
                "app/mcp/email_server.py"
            ],
        },
    ) as server:

        # Give the AI agent access to our MCP server
        email_agent.mcp_servers = [server]

        # Ask the agent to read our emails
        result = await Runner.run(
            email_agent,
            "Read my latest 5 emails and summarize them. "
            "Tell me which ones appear to need a reply."
        )

        print("\n")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())