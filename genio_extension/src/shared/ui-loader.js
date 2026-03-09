// FILE: src/shared/ui-loader.js
// src/shared/ui-loader.js
// Questo modulo contiene la logica condivisa per creare la UI fluttuante e la sidebar.

// --- Storage Keys & Constants ---
const STORAGE_KEY_FLOATING_UI_WIDTH = 'floatingUIWidth';
const DEFAULT_UI_WIDTH = 225;
const ACTION_TOOLBAR_HEIGHT = 30;
const CUSTOM_PROMPT_BUTTON_HEIGHT = 38;
const PANEL_VERTICAL_PADDING = 5;
const CUSTOM_PROMPT_AREA_HEIGHT = CUSTOM_PROMPT_BUTTON_HEIGHT + (PANEL_VERTICAL_PADDING * 2);
const BASE_UI_HEIGHT = ACTION_TOOLBAR_HEIGHT + CUSTOM_PROMPT_AREA_HEIGHT;
const MIN_FLOATING_UI_WIDTH = 150;
const MAX_FLOATING_UI_WIDTH = 400;
const TRANSLATE_MODE_UI_HEIGHT = 180;

// --- Variabili di stato globali per questo modulo ---
let floatingUI = null;
let currentSelection = '';
let isUIInteraction = false;
let isResizingFloatingUI = false;
let currentButtonsContainerMousedownListener = null;
let currentButtonsContainerMouseOverListener = null;
let currentButtonsContainerMouseOutListener = null;
let currentButtonsContainerMouseUpListener = null;
let currentButtonsContainerWheelListener = null;
let globalAudioPlayer = null; // Player audio per TTS

// --- Funzioni Helper ---
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') { unsafe = String(unsafe || ''); }
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&")
        .replace(/</g, "<")
        .replace(/>/g, ">")
        .replace(/"/g, "")
        .replace(/'/g, "'");
}

function hexToRgb(hex) { if (!hex || typeof hex !== 'string') return null; const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i; hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b); const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex); return result ? { r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16) } : null; }
function rgbToHex(r, g, b) { r = Math.max(0, Math.min(255, Math.round(r))); g = Math.max(0, Math.min(255, Math.round(g))); b = Math.max(0, Math.min(255, Math.round(b))); return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase(); }
function lightenHexColor(hex, percent) { const rgb = hexToRgb(hex); if (!rgb) return hex; const newR = rgb.r + (255 - rgb.r) * percent; const newG = rgb.g + (255 - rgb.g) * percent; const newB = rgb.b + (255 - rgb.b) * percent; return rgbToHex(newR, newG, newB); }
function darkenHexColor(hex, percent) { const rgb = hexToRgb(hex); if (!rgb) return hex; const newR = rgb.r * (1 - percent); const newG = rgb.g * (1 - percent); const newB = rgb.b * (1 - percent); return rgbToHex(newR, newG, newB); }

const getStorageValue = async (key, defaultValue) => {
    const result = await chrome.storage.local.get([key]);
    return result[key] ?? defaultValue;
};

const setStorageValue = (key, value) => {
    return chrome.storage.local.set({ [key]: value });
};

const getPreferredLanguage = () => getStorageValue('preferredLanguage', 'en');
const setPreferredLanguage = (lang) => setStorageValue('preferredLanguage', lang);
const setFloatingUIWidth = (widthPx) => setStorageValue(STORAGE_KEY_FLOATING_UI_WIDTH, widthPx);

// --- Funzioni della UI Fluttuante ---
function removeFloatingUI() {
    if (floatingUI && floatingUI.parentNode) {
        floatingUI.parentNode.removeChild(floatingUI);
        floatingUI = null;
    }
}

function generateCustomPromptsAreaHtml(customPrompts) {
    let areaHtml = '';
    let useCustomPrompts = Array.isArray(customPrompts) && customPrompts.length > 0;

    if (useCustomPrompts) {
        let buttonsHtml = '';
        const defaultVibrant = '#1a73e8'; const defaultLight = '#e8f0fe';
        const defaultHoverBg = '#d6e4ff'; const defaultHoverBorder = '#1557b0'; const defaultHoverText = '#1557b0';
        const defaultActiveBg = '#c2d7ff'; const defaultActiveBorder = '#124a99'; const defaultActiveText = defaultActiveBorder;

        customPrompts.forEach(prompt => {
            let finalVibrant = defaultVibrant; let finalLight = defaultLight;
            let hoverBgColor = defaultHoverBg; let hoverBorderColor = defaultHoverBorder; let hoverTextColor = defaultHoverText;
            let activeBgColor = defaultActiveBg; let activeBorderColor = defaultActiveBorder; let activeTextColor = activeBorderColor;
            const userColor = prompt.color;

            if (userColor && userColor.match(/^#[0-9A-F]{6}$/i) && userColor !== '#ffffff' && userColor !== '#000000') {
                try {
                    const lightBg = lightenHexColor(userColor, 0.85);
                    if (lightBg) {
                        finalVibrant = userColor; finalLight = lightBg;
                        hoverBgColor = darkenHexColor(finalLight, 0.1); hoverBorderColor = darkenHexColor(finalVibrant, 0.15); hoverTextColor = hoverBorderColor;
                        activeBgColor = darkenHexColor(finalLight, 0.2); activeBorderColor = darkenHexColor(finalVibrant, 0.25); activeTextColor = activeBorderColor;
                    }
                } catch (e) { console.error("Error processing dynamic colors for prompt:", prompt.title, e); }
            }

            let iconHtml = '';
            if (prompt.iconName && typeof prompt.iconName === 'string' && prompt.iconName.trim() !== '') {
                const iconUrl = chrome.runtime.getURL(`icons/img/${prompt.iconName}.png`);
                iconHtml = `<span class="custom-prompt-icon-mask" style="--icon-url: url('${iconUrl}'); background-color: ${finalVibrant};"></span>`;
            }

            buttonsHtml += `
                <button class="action-btn custom-prompt-btn" data-prompt="${escapeHtml(prompt.prompt)}" title="${escapeHtml(prompt.title)}"
                        style="background-color: ${finalLight}; border-color: ${finalVibrant}; color: ${finalVibrant};"
                        data-base-bg="${finalLight}" data-base-border="${finalVibrant}" data-base-text="${finalVibrant}"
                        data-hover-bg="${hoverBgColor}" data-hover-border="${hoverBorderColor}" data-hover-text="${hoverTextColor}"
                        data-active-bg="${activeBgColor}" data-active-border="${activeBorderColor}" data-active-text="${activeTextColor}">
                    ${iconHtml}
                    <span>${escapeHtml(prompt.title)}</span>
                </button>
            `;
        });
        buttonsHtml += `
            <button class="action-btn add-new-prompt-inline-btn" title="Gestisci Prompt">
                ${SVG_ICONS.add}
            </button>
        `;
        areaHtml = `<div class="buttons-container">${buttonsHtml}</div>`;
    } else {
        areaHtml = `
            <button class="action-btn add-prompts-placeholder-btn" title="Crea i tuoi prompt personalizzati">
                ${SVG_ICONS.construction}
                <span>Build your prompt</span>
            </button>
        `;
    }
    return { html: areaHtml, useCustom: useCustomPrompts };
}

function attachButtonListeners(shadowRoot, useCustomPrompts) {
    const buttonsContainer = shadowRoot.querySelector('.buttons-container');
    if (buttonsContainer) {
        if (currentButtonsContainerMousedownListener) buttonsContainer.removeEventListener('mousedown', currentButtonsContainerMousedownListener);
        if (currentButtonsContainerMouseOverListener) buttonsContainer.removeEventListener('mouseover', currentButtonsContainerMouseOverListener);
        if (currentButtonsContainerMouseOutListener) buttonsContainer.removeEventListener('mouseout', currentButtonsContainerMouseOutListener);
        if (currentButtonsContainerMouseUpListener) buttonsContainer.removeEventListener('mouseup', currentButtonsContainerMouseUpListener);
        if (currentButtonsContainerWheelListener) buttonsContainer.removeEventListener('wheel', currentButtonsContainerWheelListener);
    }

    if (useCustomPrompts && buttonsContainer) {
        const defaultVibrant = '#1a73e8'; const defaultLight = '#e8f0fe';
        const defaultHoverBg = '#d6e4ff'; const defaultHoverBorder = '#1557b0'; const defaultHoverText = '#1557b0';
        const defaultActiveBg = '#c2d7ff'; const defaultActiveBorder = '#124a99'; const defaultActiveText = '#124a99';

        currentButtonsContainerMousedownListener = (e) => {
            if (e.button !== 0) return;
            const clickedButton = e.target.closest('.custom-prompt-btn');
            if (!clickedButton) return;
            clickedButton.classList.add('active-state');
            clickedButton.style.backgroundColor = clickedButton.dataset.activeBg || defaultActiveBg;
            clickedButton.style.borderColor = clickedButton.dataset.activeBorder || defaultActiveBorder;
            clickedButton.style.color = clickedButton.dataset.activeText || defaultActiveText;
            const iconMask = clickedButton.querySelector('.custom-prompt-icon-mask');
            if (iconMask) iconMask.style.backgroundColor = clickedButton.dataset.activeText || defaultActiveText;
            clickedButton.style.transform = 'scale(0.97)';
        };
        currentButtonsContainerMouseOverListener = (e) => {
            const btn = e.target.closest('.custom-prompt-btn');
            if (btn && !btn.classList.contains('active-state')) {
                btn.style.backgroundColor = btn.dataset.hoverBg || defaultHoverBg;
                btn.style.borderColor = btn.dataset.hoverBorder || defaultHoverBorder;
                btn.style.color = btn.dataset.hoverText || defaultHoverText;
                const iconMask = btn.querySelector('.custom-prompt-icon-mask');
                if (iconMask) iconMask.style.backgroundColor = btn.dataset.hoverText || defaultHoverText;
            }
        };
        currentButtonsContainerMouseOutListener = (e) => {
            const btn = e.target.closest('.custom-prompt-btn');
            if (btn && !btn.contains(e.relatedTarget) && !btn.classList.contains('active-state')) {
                btn.style.transform = 'scale(1)';
                btn.style.backgroundColor = btn.dataset.baseBg || defaultLight;
                btn.style.borderColor = btn.dataset.baseBorder || defaultVibrant;
                btn.style.color = btn.dataset.baseText || defaultVibrant;
                const iconMask = btn.querySelector('.custom-prompt-icon-mask');
                if (iconMask) iconMask.style.backgroundColor = btn.dataset.baseText || defaultVibrant;
            }
        };
        currentButtonsContainerMouseUpListener = (e) => {
            const clickedButton = e.target.closest('.custom-prompt-btn');
            const activeBtn = buttonsContainer.querySelector('.custom-prompt-btn.active-state');

            if (activeBtn) {
                activeBtn.classList.remove('active-state');
                activeBtn.style.transform = 'scale(1)';
                const iconMask = activeBtn.querySelector('.custom-prompt-icon-mask');
                if (activeBtn.matches(':hover')) {
                    activeBtn.style.backgroundColor = activeBtn.dataset.hoverBg || defaultHoverBg;
                    activeBtn.style.borderColor = activeBtn.dataset.hoverBorder || defaultHoverBorder;
                    activeBtn.style.color = activeBtn.dataset.hoverText || defaultHoverText;
                    if (iconMask) iconMask.style.backgroundColor = activeBtn.dataset.hoverText || defaultHoverText;
                } else {
                    activeBtn.style.backgroundColor = activeBtn.dataset.baseBg || defaultLight;
                    activeBtn.style.borderColor = activeBtn.dataset.baseBorder || defaultVibrant;
                    activeBtn.style.color = activeBtn.dataset.baseText || defaultVibrant;
                    if (iconMask) iconMask.style.backgroundColor = activeBtn.dataset.baseText || defaultVibrant;
                }
                if (clickedButton === activeBtn) {
                    handleCustomPromptClick({ currentTarget: clickedButton });
                }
            }
            setTimeout(() => { isUIInteraction = false; }, 50);
            e.stopPropagation();
        };

        buttonsContainer.addEventListener('mousedown', currentButtonsContainerMousedownListener);
        buttonsContainer.addEventListener('mouseover', currentButtonsContainerMouseOverListener);
        buttonsContainer.addEventListener('mouseout', currentButtonsContainerMouseOutListener);
        buttonsContainer.addEventListener('mouseup', currentButtonsContainerMouseUpListener);

        currentButtonsContainerWheelListener = (e) => {
            e.preventDefault();
            buttonsContainer.scrollLeft += e.deltaY;
        };
        buttonsContainer.addEventListener('wheel', currentButtonsContainerWheelListener);

        const addNewPromptInlineBtn = shadowRoot.querySelector('.add-new-prompt-inline-btn');
        if (addNewPromptInlineBtn) {
            addNewPromptInlineBtn.addEventListener('click', openManagePromptsSidebar);
        }
    }

    const searchBtn = shadowRoot.querySelector('.search-btn');
    const copyTextBtn = shadowRoot.querySelector('.copy-text-btn');
    const translateActionBtn = shadowRoot.querySelector('.translate-action-btn');
    const addPromptsPlaceholderBtn = shadowRoot.querySelector('.add-prompts-placeholder-btn');
    const targetLangSelect = shadowRoot.querySelector('.target-lang');

    if (searchBtn) searchBtn.addEventListener('click', handleSearchClick);
    if (copyTextBtn) copyTextBtn.addEventListener('click', handleCopySelectionClick);

    if (translateActionBtn) {
        translateActionBtn.addEventListener('click', async (e) => {
            await toggleTranslateMode(shadowRoot, e);
        });
    }
    if (targetLangSelect) {
        targetLangSelect.addEventListener('change', async () => {
            const translationBox = shadowRoot.querySelector('.translation-box');
            if (translationBox.style.display === 'flex' && currentSelection) {
                await executeTranslation(shadowRoot, currentSelection, targetLangSelect.value);
                await setPreferredLanguage(targetLangSelect.value);
            }
        });
    }
    if (addPromptsPlaceholderBtn) {
        addPromptsPlaceholderBtn.addEventListener('click', openManagePromptsSidebar);
    }
}

async function toggleTranslateMode(shadowRoot, event) {
    const translationBox = shadowRoot.querySelector('.translation-box');
    const actionsToolbar = shadowRoot.querySelector('.actions-toolbar');
    const customPromptsArea = shadowRoot.querySelector('.custom-prompts-area');
    const resizeHandle = shadowRoot.querySelector('.floating-ui-resize-handle');

    const isTranslating = translationBox.style.display === 'flex';

    if (isTranslating) {
        translationBox.style.display = 'none';
        if (actionsToolbar) actionsToolbar.style.display = 'flex';
        if (customPromptsArea) customPromptsArea.style.display = 'flex';
        if (floatingUI) floatingUI.style.height = `${BASE_UI_HEIGHT}px`;
        if (resizeHandle) resizeHandle.style.display = 'block';
    } else {
        translationBox.style.display = 'flex';
        if (actionsToolbar) actionsToolbar.style.display = 'none';
        if (customPromptsArea) customPromptsArea.style.display = 'none';

        if (floatingUI) floatingUI.style.height = `${TRANSLATE_MODE_UI_HEIGHT}px`;
        if (resizeHandle) resizeHandle.style.display = 'none';
        if (event && currentSelection) {
            const targetLangSelect = shadowRoot.querySelector('.target-lang');
            await executeTranslation(shadowRoot, currentSelection, targetLangSelect.value);
            await setPreferredLanguage(targetLangSelect.value);
        }
    }
    setTimeout(() => { isUIInteraction = false; }, 50);
}

async function executeTranslation(shadowRoot, text, targetLang) {
    const translationResult = shadowRoot.querySelector('.translation-result');
    if (!translationResult) return;
    translationResult.value = 'Translating...';
    if (!text) {
        translationResult.value = 'No text selected.';
        return;
    }
    try {
        const translatedText = await translateText(text, targetLang);
        translationResult.value = translatedText;
    } catch (error) {
        console.error("Translation API error in executeTranslation:", error);
        translationResult.value = `Error: ${error.message || 'Translation failed'}`;
    }
}

function handleCustomPromptClick(event) {
    const targetButton = event.currentTarget;
    if (targetButton) {
        const promptText = targetButton.dataset.prompt;
        const selectedText = currentSelection;
        if (promptText) {
            const textToSend = `${promptText}: ${selectedText}`;
            openChatbot();
            setTimeout(() => {
                sendToSidebar('PREFILL_CHAT', { text: textToSend });
                removeFloatingUI();
            }, 150);
        }
    }
}

function handleSearchClick() {
    const selectedText = currentSelection;
    if (selectedText) {
        const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(selectedText)}`;
        window.open(searchUrl, '_blank');
        removeFloatingUI();
    }
    setTimeout(() => { isUIInteraction = false; }, 50);
}

async function handleCopySelectionClick() {
    const selectedText = currentSelection;
    if (selectedText) {
        try {
            await navigator.clipboard.writeText(selectedText);
            const copyBtnContainer = floatingUI.shadowRoot.querySelector('.copy-text-btn');
            if (copyBtnContainer) {
                const defaultIcon = copyBtnContainer.querySelector('.copy-icon-default');
                const feedbackIcon = copyBtnContainer.querySelector('.copy-feedback-icon');

                if (defaultIcon && feedbackIcon) {
                    defaultIcon.style.display = 'none';
                    feedbackIcon.style.display = 'inline-flex';
                    setTimeout(() => {
                        defaultIcon.style.display = 'inline-flex';
                        feedbackIcon.style.display = 'none';
                    }, 1500);
                }
            }
        } catch (err) { console.error('Floating UI: Failed to copy text: ', err); }
    }
    setTimeout(() => { isUIInteraction = false; }, 50);
}

// FIX: Logica semplificata per inviare un messaggio alla pagina host
function handleReadAloudClick(event) {
    const selectedText = currentSelection;
    if (!selectedText) return;

    // Invia un messaggio alla finestra host (content.js o reader.js)
    window.postMessage({
        type: 'GENIO_TTS_REQUEST',
        text: selectedText
    }, window.location.origin);

    removeFloatingUI();
    setTimeout(() => { isUIInteraction = false; }, 50);
}


async function translateText(text, targetLang) {
    const sourceLang = 'auto';
    try {
        const response = await fetch(`https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${sourceLang}|${targetLang}`);
        if (!response.ok) throw new Error(`MyMemory API error: ${response.status}`);
        const data = await response.json();
        if (data.responseStatus === 200 && data.responseData?.translatedText?.trim()) {
            return data.responseData.translatedText.replace(/<br\s*\/?>/gi, '\n');
        }
        const googleResponse = await fetch(`https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLang}&tl=${targetLang}&dt=t&q=${encodeURIComponent(text)}`);
        if (!googleResponse.ok) throw new Error(`Google Translate API error: ${googleResponse.status}`);
        const googleData = await googleResponse.json();
        if (googleData?.[0]?.[0]?.[0]?.trim()) {
            return googleData[0].map(item => item[0]).join('');
        }
        throw new Error("Translation failed from both services.");
    } catch (error) {
        console.error('[translateText] Error:', error);
        return `Error: ${error.message || 'Translation service unavailable'}`;
    }
}

// --- Funzioni Sidebar ---
const getSidebarTabTop = () => getStorageValue('sidebarTabTop', '15%');
const setSidebarTabTop = (topValue) => setStorageValue('sidebarTabTop', topValue);
const getSidebarWidth = () => getStorageValue('sidebarWidth', 360);
const setSidebarWidth = (widthPx) => setStorageValue('sidebarWidth', widthPx);

function openChatbot() {
    if (!window.sidebarController || !document.getElementById('chatbot-sidebar')) {
        initializeSidebar().then(() => {
            if (window.sidebarController && !window.sidebarController.isOpen()) {
                window.sidebarController.toggle();
            }
        }).catch(err => console.error("Error during fallback initializeSidebar:", err));
    } else {
        if (!window.sidebarController.isOpen()) {
            window.sidebarController.toggle();
        }
    }
}

function sendToSidebar(command, data) {
    const iframe = document.getElementById('sidebar-iframe');
    if (iframe?.contentWindow) {
        try {
            iframe.contentWindow.postMessage({ type: command, payload: data }, chrome.runtime.getURL('sidebar/index.html').substring(0, chrome.runtime.getURL('').length - 1));
        } catch (error) { console.error("Error sending postMessage to sidebar:", error); }
    } else {
        console.warn("Sidebar iframe not ready. Retrying message...");
        setTimeout(() => {
            const iframeRetry = document.getElementById('sidebar-iframe');
            if (iframeRetry?.contentWindow) {
                try { iframeRetry.contentWindow.postMessage({ type: command, payload: data }, chrome.runtime.getURL('sidebar/index.html').substring(0, chrome.runtime.getURL('').length - 1)); }
                catch (error) { console.error("Error sending postMessage (retry):", error); }
            } else console.error("Sidebar iframe still not ready after retry. Message lost:", command, data);
        }, 500);
    }
}

function openManagePromptsSidebar() {
    openChatbot();
    sendToSidebar('NAVIGATE_TO', { page: 'manage_prompts.html' });
    removeFloatingUI();
}

// --- Funzioni di Esportazione ---
// --- SVG Icons for 100% CSP compatibility ---
const SVG_ICONS = {
    search: `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>`,
    copy: `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>`,
    translate: `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12.87 15.07l-2.54-2.51.03-.03A17.52 17.52 0 0 0 14.07 6H17V4h-7V2H8v2H1v2h11.17C11.5 7.92 10.44 9.75 9 11.35 8.07 10.32 7.3 9.19 6.69 8h-2c.73 1.63 1.73 3.17 2.98 4.56l-5.09 5.02L4 19l5-5 3.11 3.11.76-2.04zM18.5 10h-2L12 22h2l1.12-3h4.75L21 22h2l-4.5-12zm-2.62 7l1.62-4.33L19.12 17h-3.24z"/></svg>`,
    add: `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>`,
    construction: `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.5 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z"/></svg>`,
    check: `<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>`,
    check_circle: `<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>`
};

export async function createFloatingUI(selectionRect) {
    if (floatingUI && floatingUI.parentNode) {
        floatingUI.parentNode.removeChild(floatingUI);
        floatingUI = null;
    }

    floatingUI = document.createElement('div');
    floatingUI.style.position = 'absolute';
    floatingUI.style.opacity = '0';
    floatingUI.style.zIndex = '2147483647';
    floatingUI.style.overflow = 'hidden';

    const shadow = floatingUI.attachShadow({ mode: 'open' });

    const response = await chrome.runtime.sendMessage({ command: 'getFloatingUiData' });
    if (chrome.runtime.lastError || !response || !response.success) {
        console.error("UI-Loader: Could not get data from background script.", chrome.runtime.lastError?.message || response?.error);
        removeFloatingUI();
        return;
    }

    const { isLoggedIn, prompts, uiWidth, preferredLanguage } = response.data;
    const customPrompts = isLoggedIn ? prompts : [];
    const savedWidth = uiWidth;
    const savedLang = preferredLanguage;

    floatingUI.style.width = `${savedWidth}px`;
    floatingUI.style.height = `${BASE_UI_HEIGHT}px`;

    const { html: customPromptsAreaHtml, useCustom: initialUseCustomPrompts } = generateCustomPromptsAreaHtml(customPrompts);

    shadow.innerHTML = `
      <style>
        :host { display: block; }
        .material-symbols-outlined { font-family: 'Material Symbols Outlined'; font-weight: normal; font-style: normal; font-size: 20px; line-height: 1; letter-spacing: normal; text-transform: none; display: inline-block; white-space: nowrap; word-wrap: normal; direction: ltr; -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility; font-feature-settings: 'liga'; }
        .custom-icon { vertical-align: middle; display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; }
        .actions-toolbar .action-icon-btn .custom-icon { width: 20px; height: 20px; }
        .actions-toolbar .action-icon-btn .copy-feedback-icon { display: none; }
        .translation-box .copy-translation-btn .custom-icon { width: 18px; height: 18px; }
        .translation-box .copy-translation-btn .copy-feedback-icon { display: none; }
        .custom-prompt-icon-mask { display: inline-block; width: 14px; height: 14px; margin-bottom: 2px; -webkit-mask-image: var(--icon-url); mask-image: var(--icon-url); -webkit-mask-size: contain; mask-size: contain; -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; -webkit-mask-position: center; mask-position: center; }
        .main-panel { display: flex; flex-direction: column; width: 100%; height: 100%; background: #ffffff; border-radius: 7px; box-shadow: 0 5px 15px rgba(0,0,0,0.12), 0 3px 6px rgba(0,0,0,0.08); border: 1px solid #d1d1d1; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; user-select: none; -webkit-user-select: none; transition: opacity 0.15s ease-in-out, width 0.2s ease-out, height 0.2s ease-out; overflow: hidden; position: relative; }
        .actions-toolbar { display: flex; justify-content: space-around; align-items: center; padding: 0 5px; height: ${ACTION_TOOLBAR_HEIGHT}px; border-bottom: 1px solid #e0e0e0; flex-shrink: 0; background-color: #f8f9fa; }
        .action-icon-btn { background: transparent; border: none; color: #5f6368; cursor: pointer; padding: 6px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: background-color 0.2s ease, color 0.2s ease; }
        .action-icon-btn:hover { background-color: #e8eaed; color: #202124; }
        .translation-box { padding: 8px 10px; border-bottom: 1px solid #e0e0e0; display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; background-color: #f8f9fa; box-sizing: border-box; overflow-y: auto; height: 100%; flex-grow: 1; }
        .target-lang { width: 100%; padding: 4px 6px; font-size: 12px; border: 1px solid #ccc; border-radius: 4px; margin-bottom: 6px; flex-shrink: 0; }
        .translation-result-container { position: relative; flex-grow: 1; display: flex; }
        .translation-result { width: 100%; min-height: 80px; padding: 6px 28px 6px 6px; border: 1px solid #ccc; border-radius: 4px; resize: none; font-size: 12px; box-sizing: border-box; user-select: text; -webkit-user-select: text; flex-grow: 1; }
        .copy-translation-btn { position: absolute; right: 2px; top: 2px; border: none; background: transparent; color: #5f6368; cursor: pointer; padding: 3px; border-radius: 50%; display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; }
        .copy-translation-btn:hover { background: #e0e0e0; }
        .custom-prompts-area { height: ${CUSTOM_PROMPT_AREA_HEIGHT}px; padding: ${PANEL_VERTICAL_PADDING}px 8px; display: flex; align-items: flex-start; flex-shrink: 0; box-sizing: border-box; }
        .buttons-container { display: flex; gap: 5px; overflow-x: auto; overflow-y: hidden; white-space: nowrap; align-items: center; width: 100%; height: 100%; padding-bottom: 5px; scrollbar-width: none; -ms-overflow-style: none; }
        .buttons-container::-webkit-scrollbar { display: none; }
        .action-btn { flex-shrink: 0; }
        .action-btn.custom-prompt-btn { padding: 2px 5px; font-size: 9px; min-width: 45px; height: ${CUSTOM_PROMPT_BUTTON_HEIGHT}px; max-height: ${CUSTOM_PROMPT_BUTTON_HEIGHT}px; border-radius: 4px; border-width: 1px; display: inline-flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box; line-height: 1; }
        .action-btn.custom-prompt-btn span { font-size: 8px; line-height: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 40px; }
        .add-new-prompt-inline-btn { background: #f0f0f0; border: 1px solid #ccc; color: #555; border-radius: 50%; width: 24px; height: 24px; padding: 0; margin-left: 4px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .add-new-prompt-inline-btn:hover { background: #e0e0e0; }
        .add-new-prompt-inline-btn svg { width: 18px; height: 18px; }
        .add-prompts-placeholder-btn { display: flex; flex-direction: row; align-items: center; justify-content: center; padding: 8px 10px; font-size: 11px; font-weight: 500; color: #1a73e8; background-color: #e8f0fe; border: 1px dashed #1a73e8; border-radius: 6px; cursor: pointer; transition: background-color 0.2s; width: 100%; height: 100%; box-sizing: border-box; }
        .add-prompts-placeholder-btn:hover { background-color: #d6e4ff; }
        .add-prompts-placeholder-btn svg { width: 16px; height: 16px; margin-right: 5px; }
        .floating-ui-resize-handle { position: absolute; bottom: 0; right: 0; width: 15px; height: 100%; cursor: e-resize; z-index: 100; }
      </style>
      <div class="main-panel">
        <div class="actions-toolbar" style="display: flex;">
          <button class="action-icon-btn search-btn" title="Cerca selezione su Google"><span class="custom-icon">${SVG_ICONS.search}</span></button>
          <button class="action-icon-btn copy-text-btn" title="Copia testo selezionato"><span class="custom-icon copy-icon-default">${SVG_ICONS.copy}</span><span class="custom-icon copy-feedback-icon">${SVG_ICONS.check_circle}</span></button>
          <button class="action-icon-btn translate-action-btn" title="Traduci testo selezionato"><span class="custom-icon">${SVG_ICONS.translate}</span></button>
        </div>
        <div class="translation-box" style="display: none;">
          <select class="target-lang">${['it', 'en', 'es', 'fr', 'de', 'pt', 'ru', 'zh', 'ja', 'ar', 'hi', 'nl', 'sv', 'pl', 'ko'].map(lang => { let dn = lang; try { dn = new Intl.DisplayNames(['en'], { type: 'language' }).of(lang); dn = dn.charAt(0).toUpperCase() + dn.slice(1); } catch (e) { } return `<option value="${lang}">${dn}</option>`; }).join('')}</select>
          <div class="translation-result-container">
            <textarea class="translation-result" readonly placeholder="Translation result..."></textarea>
            <button class="copy-translation-btn" title="Copy translation"><span class="custom-icon copy-icon-default">${SVG_ICONS.copy}</span><span class="custom-icon copy-feedback-icon">${SVG_ICONS.check}</span></button>
          </div>
        </div>
        <div class="custom-prompts-area" style="display: flex;">${customPromptsAreaHtml}</div>
        <div class="floating-ui-resize-handle"></div>
      </div>
    `;

    document.body.appendChild(floatingUI);

    const margin = 10;
    let targetX, targetY;
    let centerX = selectionRect.left + selectionRect.width / 2;
    targetX = centerX - savedWidth / 2;
    targetX = Math.max(window.scrollX + margin, Math.min(targetX, window.scrollX + window.innerWidth - savedWidth - margin));
    const spaceBelow = window.innerHeight - selectionRect.bottom - margin;
    const spaceAbove = selectionRect.top - margin;
    if (spaceBelow >= BASE_UI_HEIGHT || spaceBelow >= spaceAbove) {
        targetY = selectionRect.bottom + window.scrollY + margin;
    } else {
        targetY = selectionRect.top + window.scrollY - BASE_UI_HEIGHT - margin;
    }
    targetY = Math.max(window.scrollY + margin, Math.min(targetY, window.scrollY + window.innerHeight - BASE_UI_HEIGHT - margin));
    floatingUI.style.left = `${targetX}px`;
    floatingUI.style.top = `${targetY}px`;

    requestAnimationFrame(() => {
        floatingUI.style.transition = 'opacity 0.15s ease-in-out';
        floatingUI.style.opacity = '1';
    });

    const langSelect = shadow.querySelector('.target-lang');
    if (langSelect) langSelect.value = savedLang;

    const copyTranslationBtn = shadow.querySelector('.copy-translation-btn');
    const translationResultArea = shadow.querySelector('.translation-result');
    if (copyTranslationBtn && translationResultArea) {
        copyTranslationBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            try {
                await navigator.clipboard.writeText(translationResultArea.value);
                const defaultIcon = copyTranslationBtn.querySelector('.copy-icon-default');
                const feedbackIcon = copyTranslationBtn.querySelector('.copy-feedback-icon');
                if (defaultIcon && feedbackIcon) {
                    defaultIcon.style.display = 'none';
                    feedbackIcon.style.display = 'inline-flex';
                    setTimeout(() => {
                        defaultIcon.style.display = 'inline-flex';
                        feedbackIcon.style.display = 'none';
                    }, 1500);
                }
            } catch (err) { console.error('Failed to copy translation: ', err); }
        });
    }

    shadow.addEventListener('mousedown', (e) => { isUIInteraction = true; e.stopPropagation(); });
    shadow.addEventListener('mouseup', (e) => { setTimeout(() => { isUIInteraction = false; }, 0); e.stopPropagation(); });
    shadow.addEventListener('click', (e) => { e.stopPropagation(); });

    attachButtonListeners(shadow, initialUseCustomPrompts);

    const resizeHandle = shadow.querySelector('.floating-ui-resize-handle');
    let startXResizeHandle, initialWidthResizeHandle;
    let currentDragOverlayResizeHandle = null;

    const onFloatingUIMouseDown = (e) => {
        if (e.button !== 0) return;
        isResizingFloatingUI = true;
        startXResizeHandle = e.clientX;
        initialWidthResizeHandle = floatingUI.offsetWidth;
        currentDragOverlayResizeHandle = document.createElement('div');
        currentDragOverlayResizeHandle.style.cssText = `position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: transparent; cursor: e-resize; z-index: 2147483648; user-select: none; -webkit-user-select: none;`;
        document.body.appendChild(currentDragOverlayResizeHandle);
        floatingUI.style.transition = 'none';
        currentDragOverlayResizeHandle.addEventListener('mousemove', onFloatingUIMouseMove);
        currentDragOverlayResizeHandle.addEventListener('mouseup', onFloatingUIMouseUp);
        currentDragOverlayResizeHandle.addEventListener('mouseleave', onFloatingUIMouseUp);
        e.preventDefault();
        e.stopPropagation();
    };

    const onFloatingUIMouseMove = (e) => {
        if (!isResizingFloatingUI) return;
        const deltaX = e.clientX - startXResizeHandle;
        let newWidth = initialWidthResizeHandle + deltaX;
        newWidth = Math.max(MIN_FLOATING_UI_WIDTH, Math.min(newWidth, MAX_FLOATING_UI_WIDTH));
        floatingUI.style.width = `${newWidth}px`;
        const currentRect = floatingUI.getBoundingClientRect();
        const margin = 10;
        if (currentRect.right > window.innerWidth - margin) {
            const newLeft = window.scrollX + window.innerWidth - newWidth - margin;
            floatingUI.style.left = `${newLeft}px`;
        }
    };

    const onFloatingUIMouseUp = async (e) => {
        if (!isResizingFloatingUI) return;
        isResizingFloatingUI = false;
        if (currentDragOverlayResizeHandle && currentDragOverlayResizeHandle.parentNode) {
            currentDragOverlayResizeHandle.parentNode.removeChild(currentDragOverlayResizeHandle);
            currentDragOverlayResizeHandle = null;
        }
        floatingUI.style.transition = 'opacity 0.15s ease-in-out, width 0.2s ease-out, height 0.2s ease-out';
        await setFloatingUIWidth(floatingUI.offsetWidth);
        setTimeout(() => { isUIInteraction = false; }, 0);
        e.stopPropagation();
    };

    if (resizeHandle) {
        resizeHandle.addEventListener('mousedown', onFloatingUIMouseDown);
    }
}

export function handleSelection(e) {
    const isImage = e.target.tagName === 'IMG';
    if (isImage) {
        removeFloatingUI();
        currentSelection = ''; return;
    }
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();
    if (!selectedText) {
        if (floatingUI && !isUIInteraction && !isResizingFloatingUI) {
            const path = e.composedPath();
            if (!path.some(el => el === floatingUI)) {
                removeFloatingUI(); currentSelection = '';
            }
        }
        return;
    }
    try {
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            const selectionRect = range.getBoundingClientRect();
            if (selectionRect && (selectionRect.width > 0 || selectionRect.height > 0)) {
                if (!floatingUI || selectedText !== currentSelection) {
                    currentSelection = selectedText;
                    createFloatingUI(selectionRect);
                }
            } else if (floatingUI && !isUIInteraction && !isResizingFloatingUI) {
                const path = e.composedPath();
                if (!path.some(el => el === floatingUI)) {
                    removeFloatingUI(); currentSelection = '';
                }
            }
        }
    } catch (error) {
        console.error("Error getting selection position:", error);
        removeFloatingUI();
        currentSelection = '';
    }
}

export async function initializeSidebar() {
    if (window.sidebarController || document.getElementById('chatbot-sidebar')) return;

    // *** FIX: Sidebar Tab Aesthetic Changes ***
    const TAB_DIAMETER_PX = 40;
    const ICON_SIZE_PX = 24;
    const MIN_SIDEBAR_WIDTH_PX = 280;
    const MAX_SIDEBAR_WIDTH_PERCENT = 80;
    const HANDLE_WIDTH_PX = 8;
    const HANDLE_OFFSET_PX = Math.floor(HANDLE_WIDTH_PX / 2);

    const initialWidthPx = await getSidebarWidth();
    const initialTop = await getSidebarTabTop();

    const tabContainer = document.createElement('div');
    tabContainer.id = 'sidebar-tab-container';
    document.body.appendChild(tabContainer);
    // Updated styles for a circular, white tab
    tabContainer.style.cssText = `
        position: fixed; 
        top: ${initialTop}; 
        right: 0; 
        transform: translateY(-50%); 
        width: ${TAB_DIAMETER_PX}px; 
        height: ${TAB_DIAMETER_PX}px; 
        background-color: #ffffff; 
        border-radius: 50% 0 0 50%; 
        box-shadow: -3px 2px 8px rgba(0,0,0,0.18); 
        cursor: grab; 
        z-index: 2147483646; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        box-sizing: border-box; 
        transition: right 0.35s cubic-bezier(0.4, 0, 0.2, 1); 
        user-select: none; 
        -webkit-user-select: none;
    `;
    // Use the extension icon instead of the arrow
    tabContainer.innerHTML = `<img src="${chrome.runtime.getURL('icons/logo67.png')}" style="width: ${ICON_SIZE_PX}px; height: ${ICON_SIZE_PX}px; pointer-events: none;">`;

    const sidebarContainer = document.createElement('div');
    sidebarContainer.id = 'chatbot-sidebar';
    document.body.appendChild(sidebarContainer);
    sidebarContainer.style.cssText = `position: fixed; top: 0; right: -${initialWidthPx}px; width: ${initialWidthPx}px; height: 100vh; background-color: #f7f7f7; box-shadow: -6px 0 18px rgba(0,0,0,0.15); z-index: 2147483647; transition: right 0.35s cubic-bezier(0.4, 0, 0.2, 1); display: flex; flex-direction: column; overflow: hidden;`;
    sidebarContainer.innerHTML = `<div id="sidebar-resize-handle" style="position: absolute; left: -${HANDLE_OFFSET_PX}px; top: 0; bottom: 0; width: ${HANDLE_WIDTH_PX}px; cursor: col-resize; z-index: 10; background-color: transparent;"></div> <div style="height: 100%; width: 100%; flex-grow: 1; display: flex; position: relative; z-index: 1;"> <iframe id="sidebar-iframe" src="${chrome.runtime.getURL('sidebar/index.html')}" style="flex-grow: 1; border: none; display: block;"></iframe> </div>`;

    let sidebarOpen = false;
    let currentSidebarWidth = initialWidthPx;

    const contentToPush = document.getElementById('reader-main-content') || document.body;

    function toggleSidebar() {
        sidebarOpen = !sidebarOpen;
        const widthCss = `${currentSidebarWidth}px`;
        if (sidebarOpen) {
            sidebarContainer.style.right = '0';
            tabContainer.style.right = widthCss;
            contentToPush.style.marginRight = widthCss;
        } else {
            sidebarContainer.style.right = `-${widthCss}`;
            tabContainer.style.right = '0';
            contentToPush.style.marginRight = '0';
        }
    }

    let isDraggingTab = false, startYTab = 0, initialTopPercentTab = parseFloat(initialTop), wasTabDragged = false;
    tabContainer.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return;
        isDraggingTab = true; wasTabDragged = false; startYTab = e.clientY;
        initialTopPercentTab = parseFloat(tabContainer.style.top) || parseFloat(initialTop);
        tabContainer.style.cursor = 'grabbing';
        document.addEventListener('mousemove', onTabMouseMove);
        document.addEventListener('mouseup', onTabMouseUp);
        e.preventDefault();
    });

    const onTabMouseMove = (e) => {
        if (!isDraggingTab) return;
        wasTabDragged = true;
        const deltaY = e.clientY - startYTab;
        let newTopPx = (initialTopPercentTab / 100 * window.innerHeight) + deltaY;
        newTopPx = Math.max(TAB_DIAMETER_PX / 2, Math.min(newTopPx, window.innerHeight - (TAB_DIAMETER_PX / 2)));
        tabContainer.style.top = `${(newTopPx / window.innerHeight) * 100}%`;
    };

    const onTabMouseUp = async () => {
        if (!isDraggingTab) return;
        isDraggingTab = false;
        tabContainer.style.cursor = 'grab';
        document.removeEventListener('mousemove', onTabMouseMove);
        document.removeEventListener('mouseup', onTabMouseUp);
        if (!wasTabDragged) {
            toggleSidebar();
        } else {
            await setSidebarTabTop(tabContainer.style.top);
        }
    };

    const resizeHandle = sidebarContainer.querySelector('#sidebar-resize-handle');
    const sidebarIframe = sidebarContainer.querySelector('#sidebar-iframe');
    let dragOverlay = null, isResizing = false, startXResize = 0, initialWidthResize = 0;
    resizeHandle.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return;
        isResizing = true; startXResize = e.clientX; initialWidthResize = sidebarContainer.offsetWidth;
        dragOverlay = document.createElement('div');
        dragOverlay.style.cssText = `position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: transparent; cursor: col-resize; z-index: 2147483648; user-select: none; -webkit-user-select: none;`;
        document.body.appendChild(dragOverlay);
        if (sidebarIframe) sidebarIframe.style.pointerEvents = 'none';
        sidebarContainer.style.transition = 'none'; tabContainer.style.transition = 'none';
        contentToPush.style.transition = 'none';
        dragOverlay.addEventListener('mousemove', onResizeMouseMove);
        dragOverlay.addEventListener('mouseup', onResizeMouseUp);
        dragOverlay.addEventListener('mouseleave', onResizeMouseUp);
        e.preventDefault();
    });

    const onResizeMouseMove = (e) => {
        if (!isResizing) return;
        const deltaX = e.clientX - startXResize;
        let newWidth = initialWidthResize - deltaX;
        newWidth = Math.max(MIN_SIDEBAR_WIDTH_PX, Math.min(newWidth, window.innerWidth * (MAX_SIDEBAR_WIDTH_PERCENT / 100)));
        sidebarContainer.style.width = `${newWidth}px`;
        currentSidebarWidth = newWidth;
        if (sidebarOpen) {
            tabContainer.style.right = `${newWidth}px`;
            contentToPush.style.marginRight = `${newWidth}px`;
        }
    };

    const onResizeMouseUp = async () => {
        if (!isResizing) return;
        isResizing = false;
        if (dragOverlay && dragOverlay.parentNode) dragOverlay.parentNode.removeChild(dragOverlay);
        if (sidebarIframe) sidebarIframe.style.pointerEvents = 'auto';
        sidebarContainer.style.transition = 'right 0.35s cubic-bezier(0.4, 0, 0.2, 1)';
        tabContainer.style.transition = 'right 0.35s cubic-bezier(0.4, 0, 0.2, 1)';
        contentToPush.style.transition = 'margin-right 0.35s cubic-bezier(0.4, 0, 0.2, 1)';
        await setSidebarWidth(currentSidebarWidth);
    };

    window.sidebarController = { toggle: toggleSidebar, isOpen: () => sidebarOpen, open: () => { if (!sidebarOpen) toggleSidebar(); }, close: () => { if (sidebarOpen) toggleSidebar(); } };
}

export function initializeGlobalListeners() {
    document.addEventListener('mousedown', (e) => {
        const path = e.composedPath();
        const isClickOnFloatingUI = floatingUI && path.some(el => el === floatingUI);
        const isClickOnSidebarRelated = path.some(el => el && (el.id === 'sidebar-tab-container' || el.id === 'chatbot-sidebar' || el.id === 'sidebar-resize-handle'));
        if (isClickOnFloatingUI || isClickOnSidebarRelated || isUIInteraction || isResizingFloatingUI) {
            e.stopPropagation();
            return;
        }
        removeFloatingUI();
        currentSelection = '';
    });

    document.addEventListener('click', (e) => {
        if (e.target.tagName === 'IMG') {
            removeFloatingUI();
            currentSelection = '';
        }
    });
}