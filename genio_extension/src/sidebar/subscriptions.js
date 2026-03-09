// FILE: src/sidebar/subscriptions.js
// Gestione sottoscrizioni feed con SmartFetch

import { smartFetch } from '../services/smartFetch.js';
import { db } from '../shared/db.js';

class SubscriptionsManager {
    constructor() {
        this.feeds = [];
        this.userTier = 'free'; // Default
        this.init();
    }

    async init() {
        this.cacheElements();
        this.bindEvents();
        await this.loadUserTier();
        await this.loadFeeds();
        this.updateStats();
    }

    cacheElements() {
        this.elements = {
            feedUrl: document.getElementById('feedUrl'),
            addFeedBtn: document.getElementById('addFeedBtn'),
            addFeedError: document.getElementById('addFeedError'),
            feedsList: document.getElementById('feedsList'),
            loadingState: document.getElementById('loadingState'),
            emptyState: document.getElementById('emptyState'),
            totalFeeds: document.getElementById('totalFeeds'),
            unreadCount: document.getElementById('unreadCount'),
            lastUpdate: document.getElementById('lastUpdate'),
            refreshAllBtn: document.getElementById('refreshAllBtn'),
            importOpmlBtn: document.getElementById('importOpmlBtn'),
            opmlFileInput: document.getElementById('opmlFileInput'),
            feedItemTemplate: document.getElementById('feedItemTemplate')
        };
    }

    bindEvents() {
        // Aggiungi feed
        this.elements.addFeedBtn.addEventListener('click', () => this.addFeed());
        this.elements.feedUrl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addFeed();
        });

        // Refresh tutti
        this.elements.refreshAllBtn.addEventListener('click', () => this.refreshAllFeeds());

        // Import OPML
        this.elements.importOpmlBtn.addEventListener('click', () => {
            this.elements.opmlFileInput.click();
        });
        this.elements.opmlFileInput.addEventListener('change', (e) => this.importOPML(e));
    }

    async loadUserTier() {
        // Carica tier da storage locale o auth
        const tier = await db.get('keyval', 'user_tier');
        if (tier) {
            this.userTier = tier;
            smartFetch.setUserTier(tier);
        }
    }

    async loadFeeds() {
        this.showLoading(true);
        
        try {
            // Carica sottoscrizioni da IndexedDB
            this.feeds = await db.getAll('subscriptions');
            this.renderFeeds();
        } catch (error) {
            console.error('Error loading feeds:', error);
            this.showError('Errore nel caricamento dei feed');
        } finally {
            this.showLoading(false);
        }
    }

    renderFeeds() {
        const { feedsList, emptyState, feedItemTemplate } = this.elements;

        if (this.feeds.length === 0) {
            feedsList.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        feedsList.innerHTML = '';

        this.feeds.forEach(feed => {
            const clone = feedItemTemplate.content.cloneNode(true);
            const item = clone.querySelector('.feed-item');
            
            item.dataset.feedUrl = feed.url;
            
            // Icona
            const favicon = item.querySelector('.feed-favicon');
            favicon.src = feed.favicon || this.getFaviconUrl(feed.url);
            favicon.alt = feed.title || 'Feed';
            favicon.onerror = () => {
                favicon.src = '../icons/rss-rounded.svg';
            };

            // Status
            const status = item.querySelector('.feed-status');
            status.className = `feed-status ${feed.status || 'active'}`;

            // Info
            item.querySelector('.feed-title').textContent = feed.title || 'Feed senza titolo';
            item.querySelector('.feed-url').textContent = this.truncateUrl(feed.url);
            item.querySelector('.feed-count').textContent = `${feed.itemCount || 0} articoli`;
            item.querySelector('.feed-last-fetch').textContent = feed.lastFetch 
                ? this.timeAgo(feed.lastFetch) 
                : 'Mai aggiornato';

            // Azioni
            const refreshBtn = item.querySelector('.btn-refresh');
            const deleteBtn = item.querySelector('.btn-delete');

            refreshBtn.addEventListener('click', () => this.refreshFeed(feed.url));
            deleteBtn.addEventListener('click', () => this.deleteFeed(feed.url));

            feedsList.appendChild(item);
        });
    }

    async addFeed() {
        const url = this.elements.feedUrl.value.trim();
        
        if (!url) {
            this.showError('Inserisci un URL valido');
            return;
        }

        if (!this.isValidUrl(url)) {
            this.showError('URL non valido');
            return;
        }

        // Verifica se già presente
        if (this.feeds.some(f => f.url === url)) {
            this.showError('Feed già presente');
            return;
        }

        this.setLoadingButton(true);
        this.hideError();

        try {
            // Usa SmartFetch per recuperare e parsare il feed
            const result = await smartFetch.fetchFeed(url);

            if (!result.success) {
                throw new Error(result.error || 'Errore nel recupero del feed');
            }

            // Salva sottoscrizione
            const subscription = {
                url: url,
                title: result.data.title,
                description: result.data.description,
                link: result.data.link,
                favicon: this.getFaviconUrl(url),
                status: result.source === 'direct' ? 'active' : 'cached',
                subscribedAt: new Date().toISOString(),
                lastFetch: new Date().toISOString(),
                itemCount: result.data.items?.length || 0
            };

            await db.addSubscription(subscription);

            // Salva items nel feedItems store
            if (result.data.items?.length > 0) {
                const feedItems = result.data.items.map(item => ({
                    ...item,
                    feedUrl: url,
                    feedTitle: result.data.title
                }));
                await db.saveFeedItems(feedItems);
            }

            // Aggiorna UI
            this.elements.feedUrl.value = '';
            await this.loadFeeds();
            this.updateStats();

            // Mostra notifica
            this.showNotification(`Feed "${result.data.title}" aggiunto!`);

        } catch (error) {
            console.error('Error adding feed:', error);
            this.showError(error.message || 'Errore nell\'aggiunta del feed');
        } finally {
            this.setLoadingButton(false);
        }
    }

    async refreshFeed(url) {
        const feedItem = document.querySelector(`[data-feed-url="${url}"]`);
        const statusEl = feedItem?.querySelector('.feed-status');
        
        if (statusEl) {
            statusEl.className = 'feed-status pending';
        }

        try {
            const result = await smartFetch.fetchFeed(url);

            if (result.success) {
                // Aggiorna subscription
                const feed = this.feeds.find(f => f.url === url);
                if (feed) {
                    feed.lastFetch = new Date().toISOString();
                    feed.itemCount = result.data.items?.length || 0;
                    feed.status = result.source === 'direct' ? 'active' : 'cached';
                    await db.put('subscriptions', feed);
                }

                // Aggiorna items
                if (result.data.items?.length > 0) {
                    const feedItems = result.data.items.map(item => ({
                        ...item,
                        feedUrl: url,
                        feedTitle: result.data.title
                    }));
                    await db.saveFeedItems(feedItems);
                }

                // Ricarica UI
                await this.loadFeeds();
                this.updateStats();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error refreshing feed:', error);
            if (feedItem) {
                const status = feedItem.querySelector('.feed-status');
                status.className = 'feed-status error';
            }
            this.showNotification('Errore aggiornamento feed', 'error');
        }
    }

    async refreshAllFeeds() {
        const btn = this.elements.refreshAllBtn;
        btn.classList.add('spinning');

        let updated = 0;
        let failed = 0;

        for (const feed of this.feeds) {
            try {
                await this.refreshFeed(feed.url);
                updated++;
            } catch {
                failed++;
            }
        }

        btn.classList.remove('spinning');
        
        const message = failed > 0 
            ? `Aggiornati ${updated} feed, ${failed} falliti`
            : `Tutti i feed aggiornati!`;
        
        this.showNotification(message, failed > 0 ? 'warning' : 'success');
    }

    async deleteFeed(url) {
        if (!confirm('Eliminare questo feed? Gli articoli salvati rimarranno disponibili.')) {
            return;
        }

        try {
            await db.delete('subscriptions', url);
            
            // Rimuovi anche i feedItems associati
            const items = await db.getAll('feedItems');
            for (const item of items) {
                if (item.feedUrl === url) {
                    await db.delete('feedItems', item.id);
                }
            }

            await this.loadFeeds();
            this.updateStats();
            this.showNotification('Feed eliminato');
        } catch (error) {
            console.error('Error deleting feed:', error);
            this.showNotification('Errore eliminazione', 'error');
        }
    }

    async importOPML(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/xml');
            
            const outlines = doc.querySelectorAll('outline[type="rss"], outline[xmlUrl]');
            let added = 0;
            let failed = 0;

            for (const outline of outlines) {
                const url = outline.getAttribute('xmlUrl');
                const title = outline.getAttribute('title') || outline.getAttribute('text');

                if (url && !this.feeds.some(f => f.url === url)) {
                    try {
                        await this.addFeedFromImport(url, title);
                        added++;
                    } catch {
                        failed++;
                    }
                }
            }

            await this.loadFeeds();
            this.updateStats();
            
            const message = `Importati ${added} feed${failed > 0 ? `, ${failed} falliti` : ''}`;
            this.showNotification(message, failed > 0 ? 'warning' : 'success');

        } catch (error) {
            console.error('Error importing OPML:', error);
            this.showNotification('Errore importazione OPML', 'error');
        }

        // Reset input
        event.target.value = '';
    }

    async addFeedFromImport(url, title) {
        const result = await smartFetch.fetchFeed(url);
        
        if (!result.success) {
            throw new Error(result.error);
        }

        const subscription = {
            url: url,
            title: result.data.title || title || 'Feed senza titolo',
            description: result.data.description || '',
            link: result.data.link || url,
            favicon: this.getFaviconUrl(url),
            status: 'active',
            subscribedAt: new Date().toISOString(),
            lastFetch: new Date().toISOString(),
            itemCount: result.data.items?.length || 0
        };

        await db.addSubscription(subscription);

        if (result.data.items?.length > 0) {
            const feedItems = result.data.items.map(item => ({
                ...item,
                feedUrl: url,
                feedTitle: subscription.title
            }));
            await db.saveFeedItems(feedItems);
        }
    }

    updateStats() {
        this.elements.totalFeeds.textContent = this.feeds.length;
        
        // Conta articoli non letti (se implementato)
        this.elements.unreadCount.textContent = '0';
        
        // Ultimo aggiornamento
        const lastFetch = this.feeds
            .map(f => f.lastFetch)
            .filter(Boolean)
            .sort()
            .pop();
        
        this.elements.lastUpdate.textContent = lastFetch 
            ? this.timeAgo(new Date(lastFetch))
            : '--';
    }

    // Helpers
    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch {
            return false;
        }
    }

    getFaviconUrl(url) {
        try {
            const urlObj = new URL(url);
            return `https://www.google.com/s2/favicons?domain=${urlObj.hostname}&sz=64`;
        } catch {
            return '../icons/rss-rounded.svg';
        }
    }

    truncateUrl(url, maxLength = 40) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength) + '...';
    }

    timeAgo(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Adesso';
        if (minutes < 60) return `${minutes}m fa`;
        if (hours < 24) return `${hours}h fa`;
        if (days < 7) return `${days}g fa`;
        return new Date(date).toLocaleDateString('it-IT');
    }

    showLoading(show) {
        this.elements.loadingState.classList.toggle('hidden', !show);
        this.elements.feedsList.classList.toggle('hidden', show);
    }

    setLoadingButton(loading) {
        const btn = this.elements.addFeedBtn;
        btn.disabled = loading;
        btn.querySelector('.btn-text').classList.toggle('hidden', loading);
        btn.querySelector('.btn-loader').classList.toggle('hidden', !loading);
    }

    showError(message) {
        this.elements.addFeedError.textContent = message;
        this.elements.addFeedError.classList.remove('hidden');
    }

    hideError() {
        this.elements.addFeedError.classList.add('hidden');
    }

    showNotification(message, type = 'success') {
        // Crea elemento notifica
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Stili inline per notifica
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            z-index: 1000;
            animation: slide-up 0.3s ease forwards;
            ${type === 'success' ? 'background: #22c55e; color: white;' : ''}
            ${type === 'error' ? 'background: #ef4444; color: white;' : ''}
            ${type === 'warning' ? 'background: #f59e0b; color: white;' : ''}
        `;

        document.body.appendChild(notification);

        // Rimuovi dopo 3 secondi
        setTimeout(() => {
            notification.style.animation = 'slide-down 0.3s ease forwards';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// CSS Animations per notifiche
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-up {
        to { transform: translateX(-50%) translateY(0); }
    }
    @keyframes slide-down {
        to { transform: translateX(-50%) translateY(100px); opacity: 0; }
    }
    .btn-icon.spinning .refresh-icon {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);

// Inizializza
document.addEventListener('DOMContentLoaded', () => {
    new SubscriptionsManager();
});
