
function handleMethuEvent(data) {
    if (!data || typeof data !== "object") return;

    const event = data.event;
    const payload = data.payload || {};

    if (event === "methu_connected") {
        console.log("METHU connected:", payload.message);
        return;
    }

    if (event === "methu_thinking") {
        console.log("METHU thinking:", payload.message);
        return;
    }

    if (event === "methu_approval_required") {
        const panel = document.getElementById("approval-panel");
        const description = document.getElementById("approval-description");
        const file = document.getElementById("approval-file");
        const code = document.getElementById("approval-code");

        if (!panel || !description || !file || !code) return;

        description.textContent =
            `METHU requires approval. Intent: ${payload.intent || "Unknown"}. Risk: ${payload.risk_level || "medium"}.`;

        file.textContent = "No file proposal attached.";
        code.textContent = "Execution paused. No action was performed.";

        panel.hidden = false;
        return;
    }

    if (data.response) {
        addChatMessage("METHU", String(data.response));
        return;
    }

    console.log("METHU event:", event, data);
}


let methuSocket = null;

function connectMethu() {
    if (methuSocket && (
        methuSocket.readyState === WebSocket.OPEN ||
        methuSocket.readyState === WebSocket.CONNECTING
    )) {
        return;
    }

    methuSocket = new WebSocket("ws://127.0.0.1:8000/ws/methu");

    methuSocket.addEventListener("open", () => {
        console.log("METHU WebSocket connected");
        document.getElementById("system-status").textContent = "SYSTEM ONLINE";
    });

    methuSocket.addEventListener("message", (event) => {
        try {
            handleMethuEvent(JSON.parse(event.data));
        } catch (error) {
            console.error("METHU event error:", error);
        }
    });

    methuSocket.addEventListener("close", () => {
        console.log("METHU WebSocket disconnected");
        document.getElementById("system-status").textContent = "SYSTEM OFFLINE";
    });

    methuSocket.addEventListener("error", () => {
        console.error("METHU WebSocket connection failed");
    });
}

connectMethu();
