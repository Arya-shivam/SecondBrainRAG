const API_ASK_ENDPOINT = "http://127.0.0.1:8000/ask";

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const queryInput = document.getElementById("query-input");
    const chatContainer = document.getElementById("chat-container");
    const loadingIndicator = document.getElementById("loading-indicator");
    const savePageBtn = document.getElementById("save-page-btn");

    // Handle pressing "Save Page" button in the header
    savePageBtn.addEventListener("click", () => {
        chrome.tabs.query({ active: true, lastFocusedWindow: true }, (tabs) => {
            if (tabs[0] && tabs[0].url) {
                chrome.runtime.sendMessage({ action: "sendToDhi", url: tabs[0].url });
                addMessage("Sending current page to Second Brain...", "assistant");
            } else {
                addMessage("Error: Could not capture the page URL. Make sure you are on a valid webpage.", "assistant error-msg");
            }
        });
    });

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;

        // 1. Add user message to UI
        addMessage(query, "user");
        queryInput.value = "";
        
        // 2. Show loading
        loadingIndicator.classList.remove("hidden");
        scrollToBottom();

        // 3. Fetch from backend
        try {
            const response = await fetch(API_ASK_ENDPOINT, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ question: query, top_k: 5 })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const data = await response.json();
            
            // Hide loading
            loadingIndicator.classList.add("hidden");

            // 4. Add AI response with sources
            addMessageWithSources(data.answer, data.sources, data.latency_ms);
            
        } catch (error) {
            console.error("Error asking Dhi:", error);
            loadingIndicator.classList.add("hidden");
            addMessage("Error: Could not connect to the local Dhi backend. Make sure Docker is running on port 8000.", "assistant error-msg");
        }
    });

    function addMessage(text, type) {
        const msgDiv = document.createElement("div");
        // type can be "user" or "assistant" (or "assistant error-msg")
        msgDiv.className = `message ${type}-msg`;
        msgDiv.textContent = text;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function addMessageWithSources(answer, sources, latency) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message assistant-msg";
        
        // Add answer text
        const textNode = document.createElement("div");
        textNode.textContent = answer;
        msgDiv.appendChild(textNode);

        // Add sources if any
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement("div");
            sourcesDiv.className = "sources-container";
            
            // Only show unique titles
            const uniqueSources = [...new Set(sources.map(s => s.title))];
            
            uniqueSources.forEach((title, idx) => {
                const pill = document.createElement("span");
                pill.className = "source-pill";
                pill.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg> [${idx + 1}] ${title.length > 30 ? title.substring(0, 30) + '...' : title}`;
                sourcesDiv.appendChild(pill);
            });
            
            // Add latency pill
            const latencyPill = document.createElement("span");
            latencyPill.className = "source-pill";
            latencyPill.style.color = "#9CA3AF";
            latencyPill.style.borderColor = "transparent";
            latencyPill.style.background = "transparent";
            latencyPill.innerHTML = `⏱️ ${(latency/1000).toFixed(1)}s`;
            sourcesDiv.appendChild(latencyPill);

            msgDiv.appendChild(sourcesDiv);
        }

        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
