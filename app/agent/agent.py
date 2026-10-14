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


user_email = os.getenv("USER_EMAIL")
if not user_email:
    raise ValueError(
        "USER_EMAIL is missing from the .env file."
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
You are an intelligent email assistant that manages the user's Gmail inbox.

You have access to three tools:

1. read_emails
   - Use this to retrieve emails from Gmail.

2. create_email_draft
   - Use this to create a draft reply in Gmail.
   - This does NOT send the email.

3. send_summary_email
   - Use this to send the final email summary to the user.
   - This is the ONLY email you are allowed to send.

YOUR WORKFLOW:

STEP 1:
Call read_emails to retrieve the requested emails.

STEP 2:
Examine every email individually.

For each email:
- Identify the sender.
- Identify the subject.
- Understand the main message.
- Summarize the email.
- Determine whether the sender expects a response.

An email normally requires a response when:
- The sender asks a question.
- The sender requests information.
- The sender asks the user to perform an action.
- The sender requests confirmation.
- The conversation reasonably requires a reply.

An email normally does NOT require a response when:
- It is a newsletter.
- It is an automated notification.
- It is purely informational.
- No response or action is requested.

STEP 3:
For EVERY email that requires a response:

- Write a professional and natural reply.
- Use only information available in the original email.
- Do not invent facts.
- Call create_email_draft.
- Set the recipient to the sender's email address.
- Use the email's thread_id.
- Do NOT send the reply.

STEP 4:
For emails that do not require a response:
- Do not create a draft.

STEP 5:
After all emails have been processed, create a concise summary.

The summary must include:
- Number of emails reviewed.
- Which emails require responses.
- Which emails do not require responses.
- Which drafts were created.

STEP 6:
Send the summary to the user using send_summary_email.

The summary recipient must be the user's email address.

IMPORTANT SAFETY RULES:

- NEVER send an email reply to another person.
- Replies to other people must ONLY be saved as Gmail drafts.
- The ONLY email you may send is the final summary to the user.
- Never use send_summary_email to communicate with anyone other than the user.
- Never invent information.
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
            f"""
    Read my latest 5 emails.

    Process every email.

    For each email:
    - Determine whether it requires a response.
    - If it requires a response, write the reply.
    - Create a Gmail draft using create_email_draft.
    - Do not send the reply.

    After processing all emails:

    1. Create a concise summary of the emails.
    2. Include which emails require responses.
    3. Include which drafts were created.
    4. Send the summary to {user_email} using send_summary_email.

    The summary email must be sent only to {user_email}.

    Never send the individual email replies.
    """,
        )

        print("\n")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())