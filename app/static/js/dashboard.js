
const runButton = document.getElementById("runButton");
const runStatus = document.getElementById("runStatus");
const consoleOutput = document.getElementById("consoleOutput");
const outputBadge = document.getElementById("outputBadge");

runButton.addEventListener("click", async function () {
    // Prevent the user from starting another run immediately.
    runButton.disabled = true;
    runButton.textContent = "Processing emails...";
    runStatus.textContent = "The AI agent is running.";
    outputBadge.textContent = "Running";

    consoleOutput.textContent =
        "Starting the email agent...\nPlease wait.";

    try {
        // Ask Flask to run the Python agent.
        const response = await fetch("/run-agent", {
            method: "POST"
        });

        // Convert Flask's JSON response into a JavaScript object.
        const data = await response.json();

        // Display the real Python output.
        consoleOutput.textContent = data.output;

        // Update the status shown on the page.
        if (response.ok && data.success) {
            runStatus.textContent = "Processing completed.";
            outputBadge.textContent = "Completed";
        } else {
            runStatus.textContent = "Processing failed. Check the output.";
            outputBadge.textContent = "Failed";
        }

    } catch (error) {
        consoleOutput.textContent =
            "Could not communicate with Flask.\n" + error.message;

        runStatus.textContent = "Could not contact the server.";
        outputBadge.textContent = "Connection Error";

    } finally {
        // Allow the user to run the agent again.
        runButton.disabled = false;
        runButton.textContent = "▶ Run Email Agent";
    }
});
