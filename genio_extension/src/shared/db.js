// FILE: src/shared/db.js
import { openDB } from 'idb';

const DB_NAME = 'genio-local-db';
const DB_VERSION = 2;

export class LocalDB {
    constructor() {
        this.dbPromise = openDB(DB_NAME, DB_VERSION, {
            upgrade(db, oldVersion, newVersion, transaction) {
                if (!db.objectStoreNames.contains('articles')) {
                    const articleStore = db.createObjectStore('articles', { keyPath: 'id' });
                    articleStore.createIndex('dateAdded', 'dateAdded');
                    articleStore.createIndex('url', 'url', { unique: true });
                    articleStore.createIndex('isFavorite', 'isFavorite');
                    articleStore.createIndex('isReadLater', 'isReadLater');
                }
                if (!db.objectStoreNames.contains('subscriptions')) {
                    db.createObjectStore('subscriptions', { keyPath: 'url' });
                }
                if (!db.objectStoreNames.contains('feedItems')) {
                    const feedItemStore = db.createObjectStore('feedItems', { keyPath: 'id' });
                    feedItemStore.createIndex('feedUrl', 'feedUrl');
                    feedItemStore.createIndex('pubDate', 'pubDate');
                }
                if (!db.objectStoreNames.contains('prompts')) {
                    const promptStore = db.createObjectStore('prompts', { keyPath: 'id' });
                    promptStore.createIndex('order', 'order');
                }
                if (!db.objectStoreNames.contains('chat')) {
                    const chatStore = db.createObjectStore('chat', { keyPath: 'id', autoIncrement: true });
                    chatStore.createIndex('timestamp', 'timestamp');
                }
                if (!db.objectStoreNames.contains('keyval')) {
                    db.createObjectStore('keyval');
                }
            },
        });
    }

    async get(storeName, key) {
        return (await this.dbPromise).get(storeName, key);
    }

    async getAll(storeName) {
        return (await this.dbPromise).getAll(storeName);
    }

    async put(storeName, value) {
        return (await this.dbPromise).put(storeName, value);
    }

    async delete(storeName, key) {
        return (await this.dbPromise).delete(storeName, key);
    }

    async clear(storeName) {
        return (await this.dbPromise).clear(storeName);
    }

    // --- Articoli ---
    async addArticle(article) {
        if (!article.id) article.id = crypto.randomUUID();
        if (!article.dateAdded) article.dateAdded = new Date().toISOString();
        article.lastModified = Date.now();
        await this.put('articles', article);
        return article;
    }

    async updateArticle(id, updates) {
        const db = await this.dbPromise;
        const tx = db.transaction('articles', 'readwrite');
        const store = tx.objectStore('articles');
        const article = await store.get(id);
        if (!article) throw new Error(`Article with id ${id} not found`);
        const updatedArticle = { ...article, ...updates, lastModified: Date.now() };
        await store.put(updatedArticle);
        await tx.done;
        return updatedArticle;
    }

    async articleExists(url) {
        const db = await this.dbPromise;
        const index = db.transaction('articles').store.index('url');
        const article = await index.get(url);
        return !!article;
    }

    // --- Feed ---
    async addSubscription(subscription) {
        if (!subscription.subscribedAt) subscription.subscribedAt = new Date().toISOString();
        await this.put('subscriptions', subscription);
    }

    // FIX: Save intelligente che preserva lo stato locale (letto/nascosto)
    async saveFeedItems(newItems) {
        const db = await this.dbPromise;
        const tx = db.transaction('feedItems', 'readwrite');
        const store = tx.objectStore('feedItems');

        for (const item of newItems) {
            const existing = await store.get(item.id);
            if (existing) {
                // Mantieni i flag locali se l'item esiste già
                item.isRead = existing.isRead;
                item.hiddenFromHome = existing.hiddenFromHome || false;
            } else {
                // Default per nuovi item
                item.hiddenFromHome = false;
            }
            await store.put(item);
        }
        await tx.done;
    }

    // FIX: Metodo per nascondere dalla home invece di cancellare
    async hideFeedItem(id) {
        const db = await this.dbPromise;
        const tx = db.transaction('feedItems', 'readwrite');
        const store = tx.objectStore('feedItems');
        const item = await store.get(id);
        if (item) {
            item.hiddenFromHome = true;
            await store.put(item);
        }
        await tx.done;
    }

    // --- Chat ---
    async addChatMessage(message) {
        if (!message.timestamp) message.timestamp = Date.now();
        await this.put('chat', message);
    }

    async getChatHistory() {
        const db = await this.dbPromise;
        return db.getAllFromIndex('chat', 'timestamp');
    }
}

export const db = new LocalDB();