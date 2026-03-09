// src/auth.js (Refactored for Manifest V3 - Message Passing)
// This script's only job is to open the hosted authentication page.

document.addEventListener('DOMContentLoaded', () => {
    // This page is now just a trigger. It should open the hosted page and close itself.
    const extensionId = chrome.runtime.id;
    const authUrl = `https://genio-f9386.web.app/auth.html?extensionId=${extensionId}`;
    
    // Open the hosted authentication page in a new tab.
    chrome.tabs.create({ url: authUrl });

    // Close the extension's auth.html page immediately.
    window.close();
});