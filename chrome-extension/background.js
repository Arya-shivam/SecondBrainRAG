const API_ENDPOINT = "http://127.0.0.1:8000/api/ingest";

async function sendToDhi(url, source) {
  console.log(`Sending ${url} to Dhi...`);
  
  // Show "Sending..." notification
  chrome.notifications.create({
    type: "basic",
    iconUrl: "data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='50' fill='%234285F4'/%3E%3Ctext x='50' y='65' font-size='40' text-anchor='middle' fill='white'%3ED%3C/text%3E%3C/svg%3E",
    title: "Dhi Second Brain",
    message: `Sending to local backend...`
  });

  try {
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        url: url,
        tags: ["extension-capture", source]
      })
    });
    
    if (response.ok) {
      console.log("Successfully sent to Dhi");
      chrome.notifications.create({
        type: "basic",
        iconUrl: "data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='50' fill='%2334A853'/%3E%3Ctext x='50' y='65' font-size='40' text-anchor='middle' fill='white'%3E✓%3C/text%3E%3C/svg%3E",
        title: "Ingestion Started",
        message: `Successfully sent URL to Dhi.`
      });
    } else {
      const errText = await response.text();
      console.error("Failed to send:", errText);
      chrome.notifications.create({
        type: "basic",
        iconUrl: "data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='50' fill='%23EA4335'/%3E%3Ctext x='50' y='65' font-size='40' text-anchor='middle' fill='white'%3E✗%3C/text%3E%3C/svg%3E",
        title: "Ingestion Failed",
        message: `Backend Error: ${response.status} ${errText}`
      });
    }
  } catch (error) {
    console.error("Error communicating with local Dhi backend:", error);
    chrome.notifications.create({
      type: "basic",
      iconUrl: "data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='50' fill='%23EA4335'/%3E%3Ctext x='50' y='65' font-size='40' text-anchor='middle' fill='white'%3E✗%3C/text%3E%3C/svg%3E",
      title: "Connection Error",
      message: `Could not reach Dhi backend. Is Docker running?`
    });
  }
}

// 1. Handle clicking the extension icon (saves current page)
chrome.action.onClicked.addListener((tab) => {
  if (tab.url && tab.url.startsWith("http")) {
    sendToDhi(tab.url, "icon-click");
  }
});

// 2. Set up Right-Click Context Menu
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "send-to-dhi",
    title: "Send to Dhi (Second Brain)",
    contexts: ["link", "page"] // Shows up when right-clicking links OR the page background
  });
});

// Handle clicking the context menu item
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "send-to-dhi") {
    // If they right-clicked a specific link, use that. Otherwise use the page URL.
    const urlToSave = info.linkUrl || info.pageUrl;
    if (urlToSave && urlToSave.startsWith("http")) {
      sendToDhi(urlToSave, "context-menu");
    }
  }
});
