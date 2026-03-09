// Genio Browser Extension - Background Service Worker

const API_BASE_URL = 'https://api.genio.ai';
// const API_BASE_URL = 'http://localhost:8000'; // For development

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  // Create context menu items
  chrome.contextMenus.create({
    id: 'saveToGenio',
    title: 'Save to Genio Library',
    contexts: ['page', 'link', 'selection']
  });

  chrome.contextMenus.create({
    id: 'saveHighlight',
    title: 'Save Highlight to Genio',
    contexts: ['selection']
  });

  console.log('Genio Clipper extension installed');
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const token = await getAuthToken();
  
  if (!token) {
    notify('Please log in to Genio first', 'error');
    return;
  }

  switch (info.menuItemId) {
    case 'saveToGenio':
      if (info.linkUrl) {
        saveLink(info.linkUrl, info.selectionText || '', token);
      } else {
        savePage(tab.url, tab.title, token);
      }
      break;

    case 'saveHighlight':
      saveHighlight(tab.url, info.selectionText, token);
      break;
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener(async (tab) => {
  const token = await getAuthToken();
  
  if (!token) {
    chrome.runtime.openOptionsPage();
    return;
  }

  // Toggle quick save panel
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    function: toggleQuickSavePanel
  });
});

// Listen for messages from content script and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  handleMessage(request, sender).then(sendResponse).catch(error => {
    sendResponse({ error: error.message });
  });
  return true; // Keep message channel open for async
});

async function handleMessage(request, sender) {
  const token = await getAuthToken();

  switch (request.action) {
    case 'savePage':
      return savePage(request.url, request.title, token, request.content);
    
    case 'saveHighlight':
      return saveHighlight(request.url, request.text, token, request.note);
    
    case 'getAuthToken':
      return { token };
    
    case 'setAuthToken':
      await chrome.storage.local.set({ genioToken: request.token });
      return { success: true };
    
    case 'checkAuth':
      return { isAuthenticated: !!token };
    
    case 'extractContent':
      return extractContent(sender.tab.id);
    
    default:
      throw new Error('Unknown action');
  }
}

// Save page/article to Genio
async function savePage(url, title, token, content = null) {
  try {
    notify('Saving to Genio...', 'info');

    // If content not provided, extract from page
    if (!content) {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const extracted = await extractContent(tabs[0].id);
      content = extracted.content;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/stream/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        url,
        title,
        content,
        source: 'browser_extension'
      })
    });

    if (response.ok) {
      notify('Saved to Genio Library!', 'success');
      return { success: true };
    } else {
      throw new Error('Failed to save');
    }
  } catch (error) {
    notify('Error saving to Genio', 'error');
    return { error: error.message };
  }
}

// Save link to Genio
async function saveLink(url, note, token) {
  try {
    notify('Fetching and saving...', 'info');

    const response = await fetch(`${API_BASE_URL}/api/v1/stream/fetch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        url,
        note,
        source: 'browser_extension'
      })
    });

    if (response.ok) {
      notify('Saved to Genio!', 'success');
      return { success: true };
    } else {
      throw new Error('Failed to fetch');
    }
  } catch (error) {
    notify('Error saving link', 'error');
    return { error: error.message };
  }
}

// Save highlight
async function saveHighlight(url, text, token, note = '') {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/library/highlights`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        url,
        text,
        note,
        color: 'yellow',
        created_at: new Date().toISOString()
      })
    });

    if (response.ok) {
      notify('Highlight saved!', 'success');
      return { success: true };
    } else {
      throw new Error('Failed to save highlight');
    }
  } catch (error) {
    notify('Error saving highlight', 'error');
    return { error: error.message };
  }
}

// Extract readable content from page
async function extractContent(tabId) {
  const results = await chrome.scripting.executeScript({
    target: { tabId },
    function: () => {
      // Simple readability extraction
      const article = document.querySelector('article') || 
                     document.querySelector('[role="main"]') ||
                     document.querySelector('main') ||
                     document.body;
      
      const title = document.title;
      const content = article.innerText;
      
      return {
        title,
        content: content.substring(0, 50000), // Limit to 50KB
        url: window.location.href,
        excerpt: content.substring(0, 200) + '...'
      };
    }
  });

  return results[0].result;
}

// Get stored auth token
async function getAuthToken() {
  const result = await chrome.storage.local.get('genioToken');
  return result.genioToken;
}

// Show notification
function notify(message, type = 'info') {
  const icons = {
    success: '✅',
    error: '❌',
    info: 'ℹ️'
  };

  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: 'Genio Clipper',
    message: `${icons[type]} ${message}`
  });
}

// Toggle quick save panel (injected into page)
function toggleQuickSavePanel() {
  if (window.genioPanel) {
    window.genioPanel.remove();
    window.genioPanel = null;
    return;
  }

  const panel = document.createElement('div');
  panel.id = 'genio-quick-save';
  panel.innerHTML = `
    <div style="
      position: fixed;
      top: 20px;
      right: 20px;
      width: 350px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
      z-index: 2147483647;
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      padding: 20px;
    ">
      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
        <img src="${chrome.runtime.getURL('icons/icon48.png')}" width="24" height="24">
        <span style="font-weight: 600; font-size: 16px;">Save to Genio</span>
      </div>
      <input type="text" id="genio-title" style="
        width: 100%;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 14px;
      " placeholder="Title" value="${document.title}">
      <textarea id="genio-note" style="
        width: 100%;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 8px;
        margin-bottom: 10px;
        font-size: 14px;
        height: 80px;
        resize: vertical;
      " placeholder="Add a note..."></textarea>
      <div style="display: flex; gap: 10px;">
        <button id="genio-save" style="
          flex: 1;
          padding: 12px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
        ">Save Page</button>
        <button id="genio-cancel" style="
          padding: 12px 20px;
          background: #f3f4f6;
          border: none;
          border-radius: 8px;
          cursor: pointer;
        ">Cancel</button>
      </div>
    </div>
  `;

  document.body.appendChild(panel);
  window.genioPanel = panel;

  panel.querySelector('#genio-cancel').onclick = () => {
    panel.remove();
    window.genioPanel = null;
  };

  panel.querySelector('#genio-save').onclick = async () => {
    const title = panel.querySelector('#genio-title').value;
    const note = panel.querySelector('#genio-note').value;
    
    chrome.runtime.sendMessage({
      action: 'savePage',
      url: window.location.href,
      title,
      note
    });
    
    panel.remove();
    window.genioPanel = null;
  };
}
