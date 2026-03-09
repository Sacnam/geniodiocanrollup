// FILE: src/popup/popup.js
import { convertHtmlToMarkdown } from '../libs/markdown-converter.js';

let currentUser = null;
let currentTab = null;

// --- State Persistence ---
function saveState(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}
function loadState(key, defaultValue) {
    const val = localStorage.getItem(key);
    return val ? JSON.parse(val) : defaultValue;
}

function updateUIVisibility(isLoggedIn) {
    const authBlock = document.getElementById('auth-block');
    const controlsContainer = document.getElementById('controls-container');
    const loadingIndicator = document.getElementById('loading-indicator');
    const saveReaderButton = document.getElementById('save-reader-button');

    loadingIndicator.style.display = 'none';

    if (isLoggedIn) {
        authBlock.style.display = 'none';
        controlsContainer.style.display = 'flex';
        if (saveReaderButton) saveReaderButton.disabled = false;
    } else {
        authBlock.style.display = 'block';
        controlsContainer.style.display = 'none';
        if (saveReaderButton) saveReaderButton.disabled = true;
    }
}

async function initializePopup() {
    // Restore Drawer States
    const mdDrawer = document.getElementById('markdown-drawer');
    const rssDrawer = document.getElementById('rss-manual-drawer');

    if (mdDrawer) {
        mdDrawer.open = loadState('mdDrawerOpen', true);
        mdDrawer.addEventListener('toggle', () => saveState('mdDrawerOpen', mdDrawer.open));
    }
    if (rssDrawer) {
        rssDrawer.open = loadState('rssDrawerOpen', true);
        rssDrawer.addEventListener('toggle', () => saveState('rssDrawerOpen', rssDrawer.open));
    }

    const pageTitleElement = document.getElementById('page-title');
    const pageUrlElement = document.getElementById('page-url');
    const markdownContentElement = document.getElementById('markdown-content');
    const saveReaderButton = document.getElementById('save-reader-button');
    const downloadMdButton = document.getElementById('download-md-button');

    chrome.runtime.sendMessage({ command: 'getAuthState' }, (response) => {
        if (response && response.success) {
            currentUser = response.user;
            updateUIVisibility(response.isLoggedIn);
            loadPageData();
        } else {
            updateUIVisibility(false);
        }
    });

    async function loadPageData() {
        try {
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tabs || tabs.length === 0) return;
            currentTab = tabs[0];

            const { title, url } = currentTab;

            if (!url || !url.startsWith('http')) {
                pageTitleElement.textContent = "Unsupported Page";
                saveReaderButton.disabled = true;
                return;
            }

            pageTitleElement.textContent = title;
            pageUrlElement.textContent = url;

            try {
                const injectionResults = await chrome.scripting.executeScript({
                    target: { tabId: currentTab.id },
                    func: () => document.documentElement.outerHTML
                });
                if (injectionResults?.[0]?.result) {
                    const markdown = convertHtmlToMarkdown(injectionResults[0].result, url);
                    markdownContentElement.value = `# ${title}\n\n${markdown.substring(0, 500)}...`;
                    downloadMdButton.disabled = false;
                    downloadMdButton.onclick = () => downloadMarkdown(markdown, title);
                }
            } catch (e) { console.warn("Preview failed", e); }

            await checkForRSSFeeds();
        } catch (error) { console.error("Popup error:", error); }
    }
}

function downloadMarkdown(content, title) {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    chrome.downloads.download({ url: url, filename: `${title.replace(/[^a-z0-9]/gi, '_').substring(0, 50)}.md`, saveAs: true });
}

async function handleSaveButtonClick() {
    if (!currentTab || !currentTab.url) return;
    const saveButton = document.getElementById('save-reader-button');
    const originalText = saveButton.innerHTML;
    saveButton.disabled = true;
    saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
        const response = await chrome.runtime.sendMessage({ command: 'saveArticle', payload: { url: currentTab.url } });
        if (response && response.success) showToastNotification("Saved!", 'success');
        else throw new Error(response?.error || "Save failed");
    } catch (error) {
        showToastNotification(`Error: ${error.message}`, 'error');
    } finally {
        saveButton.disabled = false;
        saveButton.innerHTML = originalText;
    }
}

function showToastNotification(message, type = 'success') {
    let toast = document.getElementById('toast-notification');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast-notification';
        document.body.appendChild(toast);
        toast.style.cssText = `position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); padding: 10px 20px; background: #333; color: white; border-radius: 5px; z-index: 1000; font-size: 14px;`;
    }
    toast.textContent = message;
    toast.style.backgroundColor = type === 'error' ? '#e74c3c' : '#2ecc71';
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

async function checkForRSSFeeds() {
    const detectedRssDiv = document.getElementById('detected-rss-outside');
    if (!detectedRssDiv) return;
    detectedRssDiv.innerHTML = '<p class="info">Searching for feeds...</p>';

    try {
        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: currentTab.id },
            func: () => Array.from(document.querySelectorAll('link[rel="alternate"][type="application/rss+xml"], link[rel="alternate"][type="application/atom+xml"]')).map(l => ({ title: l.title, url: l.href }))
        });

        const feeds = injectionResults?.[0]?.result || [];
        if (feeds.length > 0) {
            detectedRssDiv.innerHTML = feeds.map(f => `
                <div class="rss-feed-item">
                    <span>${f.title || 'Feed'}</span>
                    <button class="subscribe-btn" data-url="${f.url}">Subscribe</button>
                </div>
            `).join('');
            detectedRssDiv.querySelectorAll('.subscribe-btn').forEach(btn => {
                btn.addEventListener('click', () => subscribeTo(btn.dataset.url, 'Feed'));
            });
        } else {
            detectedRssDiv.innerHTML = '<p class="info">No feeds found.</p>';
        }
    } catch (e) {
        detectedRssDiv.innerHTML = '<p class="info">Error detecting feeds.</p>';
    }
}

function subscribeTo(url, title) {
    chrome.runtime.sendMessage({ command: 'subscribeToFeed', payload: { url, title } }, (res) => {
        if (res && res.success) showToastNotification("Subscribed!", 'success');
        else showToastNotification("Error", 'error');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('open-manager-btn').addEventListener('click', () => chrome.tabs.create({ url: chrome.runtime.getURL('reader/reader.html') }));
    document.getElementById('save-reader-button').addEventListener('click', handleSaveButtonClick);
    document.getElementById('open-auth-page-btn').addEventListener('click', () => {
        chrome.tabs.create({ url: `https://genio-f9386.web.app/auth.html?extensionId=${chrome.runtime.id}` });
        window.close();
    });
    document.getElementById('add-custom-feed').addEventListener('click', () => {
        const url = document.getElementById('custom-feed-url').value;
        if (url) subscribeTo(url, 'Manual Feed');
    });
    initializePopup();
});