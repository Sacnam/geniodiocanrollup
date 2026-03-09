// FILE: src/reader/book_viewer.js
import { db } from '../shared/db.js';

document.addEventListener('DOMContentLoaded', async () => {
    const params = new URLSearchParams(window.location.search);
    const bookId = params.get('id');

    if (!bookId) {
        alert("Book ID missing.");
        return;
    }

    // --- UI References ---
    const ui = {
        loader: document.getElementById('loader'),
        bookTitle: document.getElementById('bookTitle'),
        tocContainer: document.getElementById('tocContainer'),
        viewer: document.getElementById('viewer'),
        sidebar: document.getElementById('sidebar'),
        settingsPanel: document.getElementById('settingsPanel'),
        tocBtn: document.getElementById('tocBtn'),
        settingsBtn: document.getElementById('settingsBtn'),
        fullscreenBtn: document.getElementById('fullscreenBtn'),
        closeBookBtn: document.getElementById('closeBookBtn'),
        closeSidebarBtn: document.getElementById('closeSidebarBtn'),
        prevArea: document.getElementById('prevArea'),
        nextArea: document.getElementById('nextArea'),
        chapterTitle: document.getElementById('chapterTitle'),
        currentPage: document.getElementById('currentPage'),
        totalPages: document.getElementById('totalPages'),
        progressBarFill: document.getElementById('progressBarFill'),
        // Settings Controls
        themeBtns: document.querySelectorAll('.theme-btn'),
        increaseFont: document.getElementById('increaseFont'),
        decreaseFont: document.getElementById('decreaseFont'),
        fontSizeDisplay: document.getElementById('fontSizeDisplay'),
        fontFamilySelect: document.getElementById('fontFamilySelect'),
        modeBtns: document.querySelectorAll('.mode-btn'),
        marginSlider: document.getElementById('marginSlider'),
        singlePageCheckbox: document.getElementById('singlePageCheckbox'),
        spreadControlRow: document.getElementById('spreadControlRow')
    };

    // --- State ---
    let book;
    let rendition;
    let currentSettings = {
        theme: 'dark',
        fontSize: 100,
        fontFamily: 'Helvetica, Arial, sans-serif',
        flow: 'paginated', // 'paginated' or 'scrolled'
        spread: 'auto',    // 'auto' (double if wide) or 'none' (single)
        margin: 10,        // percentage padding
        location: null
    };

    // --- Load Settings from Storage ---
    const storedSettings = localStorage.getItem('bookReaderSettings');
    if (storedSettings) {
        currentSettings = { ...currentSettings, ...JSON.parse(storedSettings) };
    }

    // --- Initialize Book ---
    try {
        const bookData = await db.get('articles', bookId);
        if (!bookData || !bookData.contentBlob) throw new Error("Book not found.");

        ui.bookTitle.textContent = bookData.title;
        document.title = bookData.title;

        book = ePub(bookData.contentBlob);

        await initRendition();

        const navigation = await book.loaded.navigation;
        renderTOC(navigation.toc);

        const startLocation = bookData.lastLocation || undefined;
        await rendition.display(startLocation);

        ui.loader.classList.add('hidden');

    } catch (error) {
        console.error(error);
        ui.loader.innerHTML = `<p style="color:red">Error: ${error.message}</p>`;
    }

    // --- Core Functions ---

    async function initRendition() {
        if (rendition) rendition.destroy();

        const isScrolled = currentSettings.flow === 'scrolled';
        const spreadMode = isScrolled ? 'none' : currentSettings.spread;

        rendition = book.renderTo(ui.viewer, {
            width: "100%",
            height: "100%",
            flow: isScrolled ? "scrolled-doc" : "paginated",
            manager: isScrolled ? "continuous" : "default",
            spread: spreadMode
        });

        // Register Themes
        rendition.themes.register("light", { body: { color: "#000000", background: "#ffffff" } });
        rendition.themes.register("sepia", { body: { color: "#5b4636", background: "#f4ecd8" } });
        rendition.themes.register("dark", { body: { color: "#e1e3e6", background: "#121212" } });

        // Apply Settings
        applyVisualSettings();

        // Event Listeners
        rendition.on("relocated", (location) => {
            updateProgress(location);
            saveLocation(location.start.cfi);
        });

        document.addEventListener("keyup", (e) => {
            if (e.key === "ArrowLeft") rendition.prev();
            if (e.key === "ArrowRight") rendition.next();
        });
    }

    function applyVisualSettings() {
        rendition.themes.select(currentSettings.theme);
        rendition.themes.fontSize(currentSettings.fontSize + "%");

        const rules = {
            "body": {
                "font-family": `${currentSettings.fontFamily} !important`,
                "padding-left": `${currentSettings.margin}px !important`, // Usiamo PX per padding interno
                "padding-right": `${currentSettings.margin}px !important`,
                "max-width": "100% !important",
                "margin": "0 auto !important"
            },
            "p": { "font-family": `${currentSettings.fontFamily} !important` },
            "div": { "font-family": `${currentSettings.fontFamily} !important` },
            "span": { "font-family": `${currentSettings.fontFamily} !important` }
        };
        rendition.themes.default(rules);

        ui.fontSizeDisplay.textContent = currentSettings.fontSize + "%";
        ui.fontFamilySelect.value = currentSettings.fontFamily;
        ui.marginSlider.value = currentSettings.margin;
        ui.singlePageCheckbox.checked = currentSettings.spread === 'none';

        ui.spreadControlRow.style.display = currentSettings.flow === 'scrolled' ? 'none' : 'flex';

        ui.themeBtns.forEach(btn => btn.classList.toggle('selected', btn.dataset.theme === currentSettings.theme));
        ui.modeBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.flow === currentSettings.flow));

        saveSettingsToStorage();
    }

    function saveSettingsToStorage() {
        localStorage.setItem('bookReaderSettings', JSON.stringify(currentSettings));
    }

    async function saveLocation(cfi) {
        await db.updateArticle(bookId, { lastLocation: cfi });
    }

    function updateProgress(location) {
        const percent = book.locations.percentageFromCfi(location.start.cfi);
        const percentage = Math.floor(percent * 100);

        ui.progressBarFill.style.width = percentage + "%";
        ui.currentPage.textContent = location.start.displayed.page;
        ui.totalPages.textContent = location.start.displayed.total;

        const chapter = book.navigation.get(location.start.href);
        if (chapter) ui.chapterTitle.textContent = chapter.label.trim();
    }

    // FIX: Navigazione TOC corretta
    function renderTOC(toc) {
        const ul = document.createElement('ul');
        toc.forEach(chapter => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.textContent = chapter.label.trim();
            a.href = chapter.href; // Mantiene l'href originale per accessibilità

            a.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation(); // Evita che il click si propaghi

                try {
                    await rendition.display(chapter.href);
                    // Chiudi sidebar solo su mobile o se desiderato
                    if (window.innerWidth < 768) {
                        ui.sidebar.classList.remove('open');
                    }
                } catch (err) {
                    console.error("Error navigating to chapter:", err);
                }
            });

            li.appendChild(a);
            ul.appendChild(li);
        });
        ui.tocContainer.innerHTML = '';
        ui.tocContainer.appendChild(ul);
    }

    // --- Event Listeners (UI) ---

    // FIX: Gestione corretta chiusura popup impostazioni
    document.addEventListener('click', (e) => {
        // Se il pannello è aperto E il click NON è dentro il pannello E NON è sul bottone settings
        if (!ui.settingsPanel.classList.contains('hidden')) {
            if (!ui.settingsPanel.contains(e.target) && !ui.settingsBtn.contains(e.target)) {
                ui.settingsPanel.classList.add('hidden');
            }
        }
    });

    // Previeni che i click DENTRO il pannello lo chiudano
    ui.settingsPanel.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    ui.settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Previeni che il click sul bottone venga catturato dal document
        ui.settingsPanel.classList.toggle('hidden');
    });

    ui.tocBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        ui.sidebar.classList.add('open');
    });

    ui.closeSidebarBtn.addEventListener('click', () => ui.sidebar.classList.remove('open'));

    ui.fullscreenBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else document.exitFullscreen();
    });

    ui.closeBookBtn.addEventListener('click', () => window.close());

    ui.prevArea.addEventListener('click', () => rendition.prev());
    ui.nextArea.addEventListener('click', () => rendition.next());

    ui.themeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            currentSettings.theme = btn.dataset.theme;
            applyVisualSettings();
        });
    });

    ui.increaseFont.addEventListener('click', () => {
        currentSettings.fontSize += 10;
        applyVisualSettings();
    });

    ui.decreaseFont.addEventListener('click', () => {
        if (currentSettings.fontSize > 50) currentSettings.fontSize -= 10;
        applyVisualSettings();
    });

    ui.fontFamilySelect.addEventListener('change', (e) => {
        currentSettings.fontFamily = e.target.value;
        applyVisualSettings();
    });

    ui.modeBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const newFlow = btn.dataset.flow;
            if (currentSettings.flow !== newFlow) {
                currentSettings.flow = newFlow;
                const currentLocation = rendition.currentLocation();
                const cfi = currentLocation && currentLocation.start ? currentLocation.start.cfi : null;
                await initRendition();
                if (cfi) rendition.display(cfi);
            }
        });
    });

    ui.singlePageCheckbox.addEventListener('change', async (e) => {
        currentSettings.spread = e.target.checked ? 'none' : 'auto';
        const currentLocation = rendition.currentLocation();
        const cfi = currentLocation && currentLocation.start ? currentLocation.start.cfi : null;
        await initRendition();
        if (cfi) rendition.display(cfi);
    });

    ui.marginSlider.addEventListener('input', (e) => {
        currentSettings.margin = e.target.value;
        applyVisualSettings();
    });

    book.ready.then(() => {
        book.locations.generate(1000);
    });
});