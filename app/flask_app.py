
import subprocess
from pathlib import Path

from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Find the main email-agent project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/run-agent", methods=["POST"])
def run_agent():
    try:
        # Run the existing Python agent.
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-u",
                "app/agent/agent.py",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

        # Collect anything printed to the terminal.
        output = result.stdout or ""

        if result.stderr:
            output += "\n\nERROR / DIAGNOSTIC OUTPUT:\n"
            output += result.stderr

        # Send the result back to the browser.
        return jsonify({
            "success": result.returncode == 0,
            "output": output or "The agent finished without producing output.",
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "output": "The agent took longer than five minutes and timed out.",
        }), 504

    except Exception as error:
        app.logger.exception("Could not run the email agent")

        return jsonify({
            "success": False,
            "output": f"Could not run the agent: {error}",
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
