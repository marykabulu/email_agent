import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)

from agents.mcp import MCPServerStdio


PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load the project .env regardless of the caller's working directory.
load_dotenv(PROJECT_ROOT / ".env")


# Get the Grok API key
xai_api_key = os.getenv("XAI_API_KEY")

if not xai_api_key:
    raise ValueError(
        "XAI_API_KEY is missing from the .env file."
    )


# Connect to the xAI API
xai_client = AsyncOpenAI(
    api_key=xai_api_key,
    base_url="https://api.x.ai/v1",
)


# Create the Grok model
grok_model = OpenAIChatCompletionsModel(
    model="grok-4.7",
    openai_client=xai_client,
)


# We are using Grok instead of OpenAI
set_tracing_disabled(True)


# Create the AI agent
email_agent = Agent(
    name="Email Assistant",

    instructions="""
You are an email assistant that manages the user's Gmail inbox.

You have access to two tools:

1. read_emails
   - Use this to retrieve emails from Gmail.

2. create_email_draft
   - Use this to create a draft reply in Gmail.
   - This tool does NOT send the email.

Your job is to process the user's emails.

IMPORTANT WORKFLOW:

STEP 1:
Call the read_emails tool to retrieve the requested emails.

STEP 2:
Examine each email individually.

For each email, determine whether the sender expects a response.

An email normally requires a response when:
- The sender asks a question.
- The sender asks the user to provide information.
- The sender asks the user to perform an action.
- The sender requests confirmation.
- The sender is continuing a conversation that reasonably requires a reply.

An email normally does NOT require a response when:
- It is a newsletter.
- It is an automated notification.
- It is purely informational.
- No response or action is requested.

STEP 3:
For EVERY email that requires a response, you MUST call
the create_email_draft tool.

Do NOT merely say that you will create a draft.

Actually call the create_email_draft tool.

When calling create_email_draft:

- to = the sender's email address
- subject = an appropriate reply subject
- body = the complete reply you wrote
- thread_id = the email's thread_id

The reply should:
- Be professional.
- Be natural.
- Directly address the sender's request.
- Use only information available from the original email.
- Never invent facts.
- Never claim that an action has been completed if the user has not provided that information.

STEP 4:
For emails that do not require a response, DO NOT create a draft.

STEP 5:
After processing all emails, report:
- Which emails were reviewed.
- Which emails require a response.
- Which drafts were successfully created.

CRITICAL SAFETY RULE:

You are NEVER allowed to send an email.

You may ONLY create Gmail drafts.

The user must review and manually send every draft.
""",

    model=grok_model,
)


async def main():

    # Start the MCP server
    async with MCPServerStdio(
        name="Email MCP Server",

        params={
            "command": "uv",
            "args": [
                "run",
                "python",
                "app/mcp/email_server.py",
            ],
            "cwd": str(PROJECT_ROOT),
        },
    ) as server:

        print("\nMCP SERVER CONNECTED")
        print("Available tools:")

        tools = await server.list_tools()

        for tool in tools:
            print(f"- {tool.name}")

        # Give the AI agent access to our MCP tools
        email_agent.mcp_servers = [server]

        # Tell the agent what we want it to do
        result = await Runner.run(
            email_agent,
            """
            Read my latest 5 emails.

            For each email:

            1. Determine whether it requires a response.
            2. If it requires a response, write the reply.
            3. You MUST call create_email_draft to save that reply
            as a Gmail draft.
            4. Do not send the email.

            After processing all emails, tell me which drafts you created.
            """,
        )

        print("\n")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())