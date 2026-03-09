// FILE: src/services/smartFetch.js
// Gestisce il fetch di feed RSS in modo intelligente: diretto → cache → proxy (solo Pro)

import { db } from '../shared/db.js';

const CACHE_MAX_AGE_HOURS = 24;
const DIRECT_FETCH_TIMEOUT = 10000; // 10 secondi

export class SmartFetch {
    constructor(userTier = 'free') {
        this.userTier = userTier;
        this.proxyUrl = 'https://genio-cors-proxy.yourname.workers.dev'; // Configurabile
    }

    /**
     * Fetch intelligente di un feed RSS
     * 1. Prova fetch diretto (gratis, funziona con host_permissions)
     * 2. Se fallisce, usa cache locale
     * 3. Solo per Pro: usa proxy come ultima risorsa
     */
    async fetchFeed(feedUrl) {
        console.log(`[SmartFetch] Fetching: ${feedUrl}`);
        
        // Step 1: Prova fetch diretto
        try {
            const data = await this._fetchDirect(feedUrl);
            await this._saveToCache(feedUrl, data);
            return {
                success: true,
                data,
                source: 'direct',
                timestamp: Date.now()
            };
        } catch (directError) {
            console.warn(`[SmartFetch] Direct fetch failed: ${directError.message}`);
        }

        // Step 2: Usa cache locale se disponibile
        const cached = await this._getFromCache(feedUrl);
        if (cached) {
            const ageHours = (Date.now() - cached.timestamp) / (1000 * 60 * 60);
            console.log(`[SmartFetch] Using cache (${ageHours.toFixed(1)}h old)`);
            
            return {
                success: true,
                data: cached.data,
                source: 'cache',
                timestamp: cached.timestamp,
                stale: ageHours > CACHE_MAX_AGE_HOURS,
                warning: ageHours > CACHE_MAX_AGE_HOURS ? 'Dati potrebbero essere datati' : null
            };
        }

        // Step 3: Solo per utenti Pro, prova proxy
        if (this.userTier === 'pro') {
            try {
                const data = await this._fetchViaProxy(feedUrl);
                await this._saveToCache(feedUrl, data);
                return {
                    success: true,
                    data,
                    source: 'proxy',
                    timestamp: Date.now()
                };
            } catch (proxyError) {
                console.error(`[SmartFetch] Proxy fetch failed: ${proxyError.message}`);
            }
        }

        // Tutti i metodi falliti
        return {
            success: false,
            error: 'Impossibile recuperare il feed. Riprova più tardi.',
            code: 'ALL_METHODS_FAILED'
        };
    }

    /**
     * Fetch diretto dal browser (grazie a host_permissions: <all_urls>)
     */
    async _fetchDirect(url) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), DIRECT_FETCH_TIMEOUT);

        try {
            const response = await fetch(url, {
                signal: controller.signal,
                headers: {
                    'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
                    'User-Agent': 'Mozilla/5.0 (compatible; GenioBot/1.0)'
                }
            });

            clearTimeout(timeout);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const xmlText = await response.text();
            return this._parseRSS(xmlText, url);

        } catch (error) {
            clearTimeout(timeout);
            throw error;
        }
    }

    /**
     * Fetch via proxy (solo per utenti Pro)
     */
    async _fetchViaProxy(url) {
        const proxyUrl = `${this.proxyUrl}?url=${encodeURIComponent(url)}`;
        
        const response = await fetch(proxyUrl, {
            headers: {
                'X-Genio-Tier': this.userTier,
                'X-Genio-Version': '1.9.10'
            }
        });

        if (!response.ok) {
            throw new Error(`Proxy error: ${response.status}`);
        }

        const xmlText = await response.text();
        return this._parseRSS(xmlText, url);
    }

    /**
     * Parser RSS/Atom semplice (browser-compatible)
     */
    _parseRSS(xmlText, sourceUrl) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(xmlText, 'text/xml');

        // Verifica errori di parsing
        const parseError = doc.querySelector('parsererror');
        if (parseError) {
            throw new Error('XML parsing error');
        }

        // Detect formato (RSS vs Atom)
        const isAtom = doc.querySelector('feed') !== null;
        const isRSS = doc.querySelector('rss, channel') !== null;

        if (!isAtom && !isRSS) {
            throw new Error('Formato feed non riconosciuto');
        }

        // Estrai metadati feed
        const feed = {
            title: '',
            description: '',
            link: '',
            items: []
        };

        if (isRSS) {
            const channel = doc.querySelector('channel');
            feed.title = channel?.querySelector('title')?.textContent || 'Feed senza titolo';
            feed.description = channel?.querySelector('description')?.textContent || '';
            feed.link = channel?.querySelector('link')?.textContent || sourceUrl;

            const items = doc.querySelectorAll('item');
            items.forEach((item, index) => {
                if (index >= 50) return; // Max 50 item
                feed.items.push(this._parseRSSItem(item));
            });

        } else if (isAtom) {
            const feedEl = doc.querySelector('feed');
            feed.title = feedEl?.querySelector('title')?.textContent || 'Feed senza titolo';
            feed.description = feedEl?.querySelector('subtitle')?.textContent || '';
            feed.link = feedEl?.querySelector('link')?.getAttribute('href') || sourceUrl;

            const entries = doc.querySelectorAll('entry');
            entries.forEach((entry, index) => {
                if (index >= 50) return; // Max 50 item
                feed.items.push(this._parseAtomEntry(entry));
            });
        }

        return feed;
    }

    _parseRSSItem(item) {
        const getText = (selector) => item.querySelector(selector)?.textContent || '';
        
        return {
            id: this._generateId(getText('guid') || getText('link') || getText('title')),
            title: this._cleanText(getText('title')),
            description: this._cleanText(getText('description') || getText('content:encoded')),
            link: getText('link'),
            pubDate: this._parseDate(getText('pubDate')),
            author: getText('author') || getText('dc:creator') || '',
            categories: Array.from(item.querySelectorAll('category')).map(c => c.textContent)
        };
    }

    _parseAtomEntry(entry) {
        const getText = (selector) => entry.querySelector(selector)?.textContent || '';
        const linkEl = entry.querySelector('link');
        
        return {
            id: entry.querySelector('id')?.textContent || this._generateId(getText('title')),
            title: this._cleanText(getText('title')),
            description: this._cleanText(getText('summary') || getText('content')),
            link: linkEl?.getAttribute('href') || '',
            pubDate: this._parseDate(getText('published') || getText('updated')),
            author: entry.querySelector('author name')?.textContent || '',
            categories: Array.from(entry.querySelectorAll('category')).map(c => c.getAttribute('term') || c.textContent)
        };
    }

    _cleanText(text) {
        if (!text) return '';
        return text
            .replace(/<[^>]+>/g, ' ') // Rimuovi HTML
            .replace(/\s+/g, ' ')     // Normalizza spazi
            .trim();
    }

    _parseDate(dateStr) {
        if (!dateStr) return new Date().toISOString();
        try {
            return new Date(dateStr).toISOString();
        } catch {
            return new Date().toISOString();
        }
    }

    _generateId(str) {
        // Simple hash per ID univoco
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return `item_${Math.abs(hash).toString(36)}_${Date.now().toString(36)}`;
    }

    /**
     * Salva feed nella cache IndexedDB
     */
    async _saveToCache(url, data) {
        const cacheKey = `feed_cache_${this._hashUrl(url)}`;
        await db.put('keyval', {
            url,
            data,
            timestamp: Date.now()
        }, cacheKey);
    }

    /**
     * Recupera feed dalla cache
     */
    async _getFromCache(url) {
        const cacheKey = `feed_cache_${this._hashUrl(url)}`;
        const cached = await db.get('keyval', cacheKey);
        
        if (!cached) return null;
        
        return {
            data: cached.data,
            timestamp: cached.timestamp
        };
    }

    _hashUrl(url) {
        // Simple hash per chiave cache
        let hash = 0;
        for (let i = 0; i < url.length; i++) {
            const char = url.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
        }
        return Math.abs(hash).toString(36);
    }

    /**
     * Forza refresh di un feed (bypassa cache)
     */
    async forceRefresh(feedUrl) {
        await this._saveToCache(feedUrl, null); // Clear cache
        return this.fetchFeed(feedUrl);
    }

    /**
     * Cambia tier utente (chiamato al login/logout/upgrade)
     */
    setUserTier(tier) {
        this.userTier = tier;
        console.log(`[SmartFetch] User tier changed to: ${tier}`);
    }
}

// Singleton export
export const smartFetch = new SmartFetch('free');
