/* ===================================================================
   BBHS AI ASSISTANT - Frontend JavaScript Application Logic
   =================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const messagesContainer = document.getElementById("messages-container");
    const typingIndicator = document.getElementById("typing-indicator");
    const chatMain = document.querySelector(".chat-main");

    // Configure Marked.js options
    if (window.marked) {
        marked.setOptions({
            breaks: true,
            gfm: true
        });
    }

    // Auto-resize input textarea
    userInput.addEventListener("input", () => {
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 160) + "px";
    });

    // Handle Enter to submit (Shift+Enter for newline)
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Form submit
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;
        sendMessage(text);
    });

    // Send message workflow
    async function sendMessage(queryText) {
        // Append user message
        appendUserMessage(queryText);
        userInput.value = "";
        userInput.style.height = "auto";
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Show typing indicator
        showTypingIndicator();
        scrollToBottom();

        const startTime = performance.now();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ query: queryText })
            });

            const latencySec = ((performance.now() - startTime) / 1000).toFixed(2);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            hideTypingIndicator();
            appendAssistantMessage(data.answer, data.sources || [], data.refusal, latencySec);
        } catch (error) {
            hideTypingIndicator();
            appendErrorMessage(`Unable to get answer: ${error.message}`);
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
            scrollToBottom();
        }
    }

    function appendUserMessage(text) {
        const row = document.createElement("div");
        row.className = "message-row user";
        row.innerHTML = `
            <div class="message-bubble">
                <p>${escapeHtml(text)}</p>
            </div>
            <div class="user-avatar" title="You">
                <i class="fa-solid fa-user"></i>
            </div>
        `;
        messagesContainer.appendChild(row);
    }

    function appendAssistantMessage(answer, sources, refusal, latencySec) {
        const row = document.createElement("div");
        row.className = "message-row assistant";

        // Parse markdown or fallback
        const formattedHtml = window.marked ? marked.parse(answer) : `<p>${escapeHtml(answer)}</p>`;

        // Unique ID for copy
        const copyId = "copy-" + Math.random().toString(36).substring(2, 9);

        row.innerHTML = `
            <div class="assistant-avatar" title="BBHS AI Assistant">
                <i class="fa-solid fa-graduation-cap"></i>
            </div>
            <div class="message-bubble">
                <div class="assistant-text" id="${copyId}">
                    ${formattedHtml}
                </div>
                <div class="message-meta">
                    <button class="btn-copy" data-target="${copyId}" title="Copy response">
                        <i class="fa-regular fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        `;

        // Add copy button listener
        const copyBtn = row.querySelector(".btn-copy");
        copyBtn.addEventListener("click", () => {
            navigator.clipboard.writeText(answer).then(() => {
                copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                }, 2000);
            });
        });

        messagesContainer.appendChild(row);
    }

    function appendErrorMessage(errorText) {
        const row = document.createElement("div");
        row.className = "message-row assistant";
        row.innerHTML = `
            <div class="assistant-avatar" style="background:#dc2626;">
                <i class="fa-solid fa-triangle-exclamation"></i>
            </div>
            <div class="message-bubble" style="border-color: rgba(220, 38, 38, 0.4);">
                <p style="color:#fca5a5;"><strong>Error:</strong> ${escapeHtml(errorText)}</p>
            </div>
        `;
        messagesContainer.appendChild(row);
    }

    function showTypingIndicator() {
        typingIndicator.classList.remove("hidden");
    }

    function hideTypingIndicator() {
        typingIndicator.classList.add("hidden");
    }

    function scrollToBottom() {
        setTimeout(() => {
            chatMain.scrollTop = chatMain.scrollHeight;
        }, 50);
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
