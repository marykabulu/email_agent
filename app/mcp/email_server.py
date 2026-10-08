import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.email.gmail import get_emails
from mcp.server import MCPServer


# Create the MCP server
mcp = MCPServer("Email Assistant")


@mcp.tool()
def read_emails(max_results: int = 10) -> list[dict]:
    """
    Read recent emails from the user's Gmail inbox.

    Returns the sender, subject, date, and body of each email.
    """

    return get_emails(max_results)

if __name__ == "__main__":
    mcp.run()
