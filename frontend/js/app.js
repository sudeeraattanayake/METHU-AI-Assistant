
const approvalPanel = document.getElementById("approval-panel");
const approvalDescription = document.getElementById("approval-description");
const approvalFile = document.getElementById("approval-file");
const approvalCode = document.getElementById("approval-code");
const approveButton = document.getElementById("approve-button");
const rejectButton = document.getElementById("reject-button");

let currentApproval = null;

function showApprovalRequest(request) {
    if (!request || !request.approval_id) {
        throw new Error("Invalid approval request");
    }

    currentApproval = request;
    approvalDescription.textContent = request.description || "File modification requested";
    approvalFile.textContent = `File: ${request.path || "Unknown"}`;
    approvalCode.textContent = request.code || "No code preview available";

    approvalPanel.hidden = false;
}

function hideApprovalRequest() {
    currentApproval = null;
    approvalPanel.hidden = true;
}

approveButton.addEventListener("click", () => {
    if (!currentApproval) return;
    alert("Approval preview only. Backend authorization is not connected yet.");
});

rejectButton.addEventListener("click", () => {
    hideApprovalRequest();
});

hideApprovalRequest();


const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");

function addChatMessage(sender, message) {
    const item = document.createElement("p");
    const name = document.createElement("strong");

    name.textContent = `${sender}: `;
    item.appendChild(name);
    item.appendChild(document.createTextNode(message));

    chatMessages.appendChild(item);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    if (!methuSocket || methuSocket.readyState !== WebSocket.OPEN) {
        addChatMessage("System", "METHU is not connected.");
        return;
    }

    methuSocket.send(JSON.stringify({
        message: message,
        session_id: "frontend-session"
    }));

    addChatMessage("You", message);
    chatInput.value = "";
});
