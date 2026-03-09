// FILE: src/sidebar/manage_prompts.js
import Sortable from 'sortablejs';

// --- DOM Elements ---
let backButton, promptList, addPromptBtn, promptForm, formTitle, promptIdInput,
    promptTitleInput, promptTextInput, selectedIconNameInput, promptColorInput,
    savePromptBtn, cancelPromptBtn, iconPicker;

function initializeDOMElements() {
    backButton = document.getElementById('backButton');
    promptList = document.getElementById('promptList');
    addPromptBtn = document.getElementById('addPromptBtn');
    promptForm = document.getElementById('promptForm');
    formTitle = document.getElementById('formTitle');
    promptIdInput = document.getElementById('promptId');
    promptTitleInput = document.getElementById('promptTitle');
    promptTextInput = document.getElementById('promptText');
    selectedIconNameInput = document.getElementById('selectedIconName');
    promptColorInput = document.getElementById('promptColor');
    savePromptBtn = document.getElementById('savePromptBtn');
    cancelPromptBtn = document.getElementById('cancelPromptBtn');
    iconPicker = document.getElementById('iconPicker');
}

// --- Global Variables ---
let sortableInstance = null;
let isSortableInitialized = false;

// LISTA ICONE DISPONIBILI (Nomi Material Icons)
const AVAILABLE_ICONS = [
    'auto_stories', 'brightness_2', 'brush', 'colorize', 'content_copy',
    'filter_drama', 'flare', 'gamepad', 'grain', 'group', 'hourglass_empty',
    'landscape', 'nature', 'palette', 'rocket_launch', 'search', 'sports_esports',
    'timer', 'translate', 'star', 'favorite', 'bolt', 'psychology', 'lightbulb',
    'terminal', 'code', 'format_quote', 'history_edu', 'school', 'work'
];

// --- Functions ---
function loadPrompts() {
    if (promptList && !isSortableInitialized && !promptList.querySelector('li')) {
        promptList.innerHTML = '<li class="loading-placeholder">Loading prompts...</li>';
    }
    chrome.runtime.sendMessage({ command: 'getCustomPrompts' }, (response) => {
        if (response && response.success) {
            renderPromptList(response.prompts);
        } else {
            if (promptList) promptList.innerHTML = `<li>Error loading prompts.</li>`;
        }
    });
}

function renderPromptList(prompts) {
    if (!promptList) return;
    promptList.innerHTML = '';

    if (!prompts || prompts.length === 0) {
        promptList.innerHTML = '<li>No custom prompts yet.</li>';
        return;
    }

    prompts.forEach(prompt => renderPromptItem(prompt.id, prompt));
    if (!isSortableInitialized) initializeDragAndDrop();
}

function renderPromptItem(id, data) {
    const li = document.createElement('li');
    li.setAttribute('data-id', id);

    // Render Icona come FONT, non immagine
    let iconHtml = '';
    if (data.iconName) {
        const color = data.color || '#5f6368';
        iconHtml = `<span class="material-symbols-outlined"
    style="color: ${color}; margin-right: 10px;">${data.iconName}</span>`;
    } else {
        iconHtml = `<span class="material-symbols-outlined" style="color: #ccc; margin-right: 10px;">label</span>`;
    }

    li.innerHTML = `
<span class="drag-handle"><span class="material-symbols-outlined">drag_indicator</span></span>
${iconHtml}
<div class="prompt-info">
    <div class="prompt-title">${escapeHtml(data.title || 'No Title')}</div>
    <div class="prompt-text-preview">${escapeHtml(data.prompt || '')}</div>
</div>
<div class="prompt-actions">
    <button class="edit-btn"><span class="material-symbols-outlined">edit</span></button>
    <button class="delete-btn"><span class="material-symbols-outlined">delete</span></button>
</div>
`;
    promptList.appendChild(li);
}

function initializeDragAndDrop() {
    if (typeof Sortable === 'undefined' || isSortableInitialized || !promptList) return;
    sortableInstance = new Sortable(promptList, {
        handle: '.drag-handle',
        animation: 150,
        onEnd: () => updatePromptOrder(),
    });
    isSortableInitialized = true;
}

function updatePromptOrder() {
    const orderedIds = Array.from(promptList.querySelectorAll('li[data-id]')).map(item => item.getAttribute('data-id'));
    chrome.runtime.sendMessage({ command: 'updatePromptOrder', payload: { orderedIds } });
}

function populateIconPicker() {
    if (!iconPicker) return;
    iconPicker.innerHTML = AVAILABLE_ICONS.map(iconName => `
<div class="icon-picker-item" data-icon-name="${iconName}">
    <span class="material-symbols-outlined">${iconName}</span>
</div>
`).join('');
}

function handleIconSelection(iconName) {
    if (!selectedIconNameInput) return;
    selectedIconNameInput.value = iconName;

    iconPicker.querySelectorAll('.icon-picker-item').forEach(el => el.classList.remove('selected'));
    const selected = iconPicker.querySelector(`.icon-picker-item[data-icon-name="${iconName}"]`);
    if (selected) selected.classList.add('selected');
}

function showForm(mode = 'add', promptData = {}, id = null) {
    promptIdInput.value = id || '';
    promptTitleInput.value = promptData.title || '';
    promptTextInput.value = promptData.prompt || '';
    selectedIconNameInput.value = promptData.iconName || '';
    promptColorInput.value = promptData.color || '#000000';

    handleIconSelection(promptData.iconName || '');

    formTitle.textContent = mode === 'edit' ? 'Edit Prompt' : 'Add New Prompt';
    promptForm.style.display = 'block';
    promptList.parentElement.style.display = 'none'; // Nascondi lista
}

function hideForm() {
    promptForm.style.display = 'none';
    promptList.parentElement.style.display = 'block'; // Mostra lista
    promptForm.reset();
}

function savePrompt(event) {
    event.preventDefault();
    const promptData = {
        id: promptIdInput.value || null,
        title: promptTitleInput.value,
        prompt: promptTextInput.value,
        iconName: selectedIconNameInput.value,
        color: promptColorInput.value
    };

    chrome.runtime.sendMessage({ command: 'savePrompt', payload: promptData }, (res) => {
        if (res && res.success) {
            hideForm();
            loadPrompts(); // Ricarica lista
        } else {
            alert("Error saving prompt.");
        }
    });
}

function deletePrompt(id) {
    if (confirm("Delete this prompt?")) {
        chrome.runtime.sendMessage({ command: 'deletePrompt', payload: { id } }, () => loadPrompts());
    }
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function setupEventListeners() {
    backButton.addEventListener('click', () => window.location.href = 'index.html');
    addPromptBtn.addEventListener('click', () => showForm('add'));
    promptForm.addEventListener('submit', savePrompt);
    cancelPromptBtn.addEventListener('click', hideForm);

    promptList.addEventListener('click', (e) => {
        const li = e.target.closest('li');
        if (!li) return;
        const id = li.getAttribute('data-id');

        if (e.target.closest('.edit-btn')) {
            chrome.runtime.sendMessage({ command: 'getCustomPrompts' }, (res) => {
                const p = res.prompts.find(x => x.id === id);
                if (p) showForm('edit', p, id);
            });
        } else if (e.target.closest('.delete-btn')) {
            deletePrompt(id);
        }
    });

    iconPicker.addEventListener('click', (e) => {
        const item = e.target.closest('.icon-picker-item');
        if (item) handleIconSelection(item.dataset.iconName);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initializeDOMElements();
    setupEventListeners();
    populateIconPicker();
    loadPrompts();
});