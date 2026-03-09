// src/reader/engine.js
import ePub from 'epubjs';

export class ReaderEngine {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`ReaderEngine: Container #${containerId} not found.`);
        }
        this.mode = null; // 'article' | 'epub'
        this.book = null;
        this.rendition = null;
    }

    async load(item, bookData = null) {
        this.clear();

        if (item.type === 'epub' || (item.blob && !item.content)) {
            this.mode = 'epub';
            // Passiamo l'ArrayBuffer o il Blob direttamente
            await this._loadEpub(bookData || item.blob);
        } else {
            this.mode = 'article';
            this._loadArticle(item);
        }
    }

    _loadArticle(item) {
        // Per gli articoli, il rendering è gestito esternamente da reader.js
        this.mode = 'article';
    }

    async _loadEpub(bookData) {
        // 1. Inizializza il libro
        this.book = ePub(bookData);

        // 2. Renderizza. IMPORTANTE: width/height al 100%
        this.rendition = this.book.renderTo(this.container, {
            width: '100%',
            height: '100%',
            flow: 'paginated',
            manager: 'default',
            allowScriptedContent: false
        });

        // 3. Visualizza
        await this.rendition.display();

        // 4. Registra temi base
        this.rendition.themes.register('dark', { body: { color: '#E1E3E6', background: '#23272F' } });
        this.rendition.themes.register('light', { body: { color: '#000000', background: '#ffffff' } });
    }

    async getActiveText() {
        if (this.mode === 'article') {
            const selection = window.getSelection().toString();
            const articleEl = document.getElementById('articleContent');
            return selection || (articleEl ? articleEl.innerText : "");
        }

        if (this.mode === 'epub' && this.rendition) {
            try {
                // Tentativo 1: Selezione nel libro (difficile con iframe, ma proviamo)
                // epub.js non espone facilmente la selezione nativa, ma possiamo provare a prendere il testo visibile
                const visibleRange = await this.rendition.currentLocation();
                if (visibleRange && visibleRange.start) {
                    // Se non c'è selezione, prendiamo il testo della pagina corrente
                    // Nota: epub.js non ha un metodo sincrono "getText", è complesso.
                    // Per ora, restituiamo un messaggio generico se non riusciamo a estrarre.
                    return "Funzionalità estrazione testo EPUB in arrivo. Usa su articoli per ora.";
                }
            } catch (e) {
                console.error("Errore testo EPUB:", e);
            }
        }
        return "";
    }

    applyTheme(themeName) {
        if (this.mode === 'epub' && this.rendition) {
            this.rendition.themes.select(themeName);
        }
    }

    next() {
        if (this.mode === 'epub' && this.rendition) this.rendition.next();
    }

    prev() {
        if (this.mode === 'epub' && this.rendition) this.rendition.prev();
    }

    clear() {
        this.container.innerHTML = '';
        if (this.book) {
            this.book.destroy();
            this.book = null;
            this.rendition = null;
        }
        this.mode = null;
    }
}