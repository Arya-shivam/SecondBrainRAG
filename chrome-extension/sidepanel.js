const API_BASE = "http://127.0.0.1:8000";
const API_ASK_ENDPOINT = `${API_BASE}/ask`;
const API_INGEST_ENDPOINT = `${API_BASE}/api/ingest`;

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const queryInput = document.getElementById("query-input");
    const chatContainer = document.getElementById("chat-container");
    const loadingIndicator = document.getElementById("loading-indicator");
    const savePageBtn = document.getElementById("save-page-btn");
    const settingsBtn = document.getElementById("settings-btn");
    const settingsPanel = document.getElementById("settings-panel");
    const folderInput = document.getElementById("default-folder-input");
    const saveSettingsBtn = document.getElementById("save-settings-btn");

    // ── Load saved settings ────────────────────────────────────────────────
    chrome.storage.local.get(["defaultFolder"], (result) => {
        if (result.defaultFolder) {
            folderInput.value = result.defaultFolder;
        }
    });

    // ── Settings toggle ────────────────────────────────────────────────────
    settingsBtn.addEventListener("click", () => {
        settingsPanel.classList.toggle("hidden");
    });

    saveSettingsBtn.addEventListener("click", () => {
        const folder = folderInput.value.trim().replace(/^\/|\/$/g, ""); // strip leading/trailing slashes
        chrome.storage.local.set({ defaultFolder: folder }, () => {
            saveSettingsBtn.textContent = "Saved!";
            saveSettingsBtn.style.background = "#22c55e";
            setTimeout(() => {
                saveSettingsBtn.textContent = "Save Settings";
                saveSettingsBtn.style.background = "";
                settingsPanel.classList.add("hidden");
            }, 1200);
        });
    });

    // ── Save current page ──────────────────────────────────────────────────
    savePageBtn.addEventListener("click", () => {
        chrome.tabs.query({ active: true, lastFocusedWindow: true }, (tabs) => {
            if (tabs[0] && tabs[0].url) {
                const url = tabs[0].url;

                // Get folder preference, then send
                chrome.storage.local.get(["defaultFolder"], (result) => {
                    const folder = result.defaultFolder || null;
                    sendToIngest(url, folder);
                });
            } else {
                addMessage("Error: Could not capture the page URL. Make sure you are on a valid webpage.", "assistant error-msg");
            }
        });
    });

    function sendToIngest(url, folder) {
        const folderLabel = folder ? ` → vault/${folder}` : "";
        addMessage(`Saving page to Second Brain${folderLabel}...`, "assistant");

        const body = { url, tags: ["extension-capture"] };
        if (folder) body.folder = folder;

        fetch(API_INGEST_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                addMessage(`Saved! Indexing in the background...`, "assistant");
            } else {
                addMessage(`Error: ${data.detail || "Unknown error"}`, "assistant error-msg");
            }
        })
        .catch(err => {
            console.error("Ingest error:", err);
            addMessage("Error: Could not reach the backend. Is Docker running?", "assistant error-msg");
        });
    }

    // ── Chat submit ────────────────────────────────────────────────────────
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;

        addMessage(query, "user");
        queryInput.value = "";
        
        loadingIndicator.classList.remove("hidden");
        scrollToBottom();

        try {
            const response = await fetch(API_ASK_ENDPOINT, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: query, top_k: 5 })
            });

            if (!response.ok) throw new Error(`Server returned ${response.status}`);

            const data = await response.json();
            loadingIndicator.classList.add("hidden");
            addMessageWithSources(data.answer, data.sources, data.latency_ms);
            
        } catch (error) {
            console.error("Error asking Dhi:", error);
            loadingIndicator.classList.add("hidden");
            addMessage("Error: Could not connect to the local Dhi backend. Make sure Docker is running on port 8000.", "assistant error-msg");
        }
    });

    // ── UI helpers ─────────────────────────────────────────────────────────
    function addMessage(text, type) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${type}-msg`;
        msgDiv.textContent = text;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function addMessageWithSources(answer, sources, latency) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message assistant-msg";
        
        const textNode = document.createElement("div");
        textNode.textContent = answer;
        msgDiv.appendChild(textNode);

        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement("div");
            sourcesDiv.className = "sources-container";
            
            const uniqueSources = [...new Set(sources.map(s => s.title))];
            
            uniqueSources.forEach((title, idx) => {
                const pill = document.createElement("span");
                pill.className = "source-pill";
                pill.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg> [${idx + 1}] ${title.length > 30 ? title.substring(0, 30) + '...' : title}`;
                sourcesDiv.appendChild(pill);
            });
            
            if (latency) {
                const latencyPill = document.createElement("span");
                latencyPill.className = "source-pill";
                latencyPill.style.cssText = "color:#9CA3AF;border-color:transparent;background:transparent";
                latencyPill.textContent = `${(latency/1000).toFixed(1)}s`;
                sourcesDiv.appendChild(latencyPill);
            }

            msgDiv.appendChild(sourcesDiv);
        }

        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
