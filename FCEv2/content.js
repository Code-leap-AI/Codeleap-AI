// content.js
console.log("Flash Card Generator content script loaded");

// Tell the background script that this content script is ready to receive messages
chrome.runtime.sendMessage({ action: "contentScriptReady" }, () => {
  // Ignore any response or error
  if (chrome.runtime.lastError) {
    console.log("No response from background script, which is fine");
  }
});

// Listen for notification messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("Content script received message:", request);
  
  if (request.action === "showNotification") {
    showNotification(request.message, request.type || "info");
    // Always send a response even if it's empty to avoid errors
    sendResponse({ status: "success" });
  } else {
    // Still send a response for any unhandled message to avoid hanging promises
    sendResponse({ status: "unhandled" });
  }
  
  // Return true to indicate you wish to send a response asynchronously
  return true;
});

// Show a notification on the page
function showNotification(message, type = "info", duration = 3000) {
  try {
    // Create notification element
    const notification = document.createElement("div");
    notification.textContent = message;
    
    // Set color based on type
    let color = "#2196F3"; // info (blue)
    if (type === "success") color = "#4CAF50"; // success (green)
    if (type === "error") color = "#F44336"; // error (red)
    
    // Set styles
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 16px;
      background-color: ${color};
      color: white;
      border-radius: 4px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
      z-index: 10000;
      font-family: Arial, sans-serif;
      font-size: 14px;
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after duration
    setTimeout(() => {
      if (document.body.contains(notification)) {
        document.body.removeChild(notification);
      }
    }, duration);
    
    return true;
  } catch (err) {
    console.error("Error showing notification:", err);
    return false;
  }
}
