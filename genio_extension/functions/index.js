// FILE: functions/index.js
const { onCall, HttpsError, onRequest } = require("firebase-functions/v2/https");
const logger = require("firebase-functions/logger");
const admin = require("firebase-admin");
const { FieldValue } = require('firebase-admin/firestore');
const { defineSecret } = require("firebase-functions/params");
const crypto = require('crypto');

// Importiamo v1 per i trigger legacy se servono
const v1 = require("firebase-functions/v1");

// --- Inizializzazione ---
try {
    if (admin.apps.length === 0) admin.initializeApp();
} catch (e) {
    logger.error("Errore init Firebase Admin:", e);
}
const db = admin.firestore();

// --- Secrets ---
const replicateApiKey = defineSecret("REPLICATE_API_KEY");
const geminiApiKey = defineSecret("GEMINI_API_KEY");

// ===================================================================
// 1. PROCESS ARTICLE (Parsing)
// ===================================================================
exports.processAndSaveArticle = onCall({
    region: 'us-central1',
    timeoutSeconds: 300,
    memory: '512MiB'
}, async (request) => {
    // Import dinamico o require per fetch
    const fetch = require('node-fetch');
    const { JSDOM } = require('jsdom');
    const { Readability } = require('@mozilla/readability');

    if (!request.auth) throw new HttpsError("unauthenticated", "Auth required.");
    const uid = request.auth.uid;
    const url = request.data.url;

    if (!url) throw new HttpsError("invalid-argument", "URL required.");

    try {
        const response = await fetch(url, { headers: { 'User-Agent': 'GenioBot/1.0' }, timeout: 20000 });
        if (!response.ok) throw new HttpsError('unavailable', `Fetch failed: ${response.status}`);
        const html = await response.text();
        const doc = new JSDOM(html, { url }).window.document;
        const reader = new Readability(doc);
        const article = reader.parse();

        if (!article) throw new HttpsError('not-found', "Parsing failed.");

        // Salvataggio su Firestore (se ancora usato per backup)
        const articleRef = db.collection('users').doc(uid).collection('savedArticles').doc();
        await articleRef.set({
            title: article.title,
            content: article.content,
            url: url,
            dateAdded: FieldValue.serverTimestamp(),
            source: 'manual_parsed'
        });

        return { success: true, articleId: articleRef.id };
    } catch (error) {
        logger.error("Process Error:", error);
        throw new HttpsError('internal', error.message);
    }
});

// ===================================================================
// 2. AI TASK (Chat & Prompts) - FIX CRITICO FETCH
// ===================================================================
exports.processArticleTask = onCall({
    region: 'us-central1',
    secrets: [geminiApiKey],
    timeoutSeconds: 120,
    memory: '256MiB'
}, async (request) => {
    // *** FIX: Require node-fetch qui dentro per garantire che esista ***
    const fetch = require('node-fetch');

    if (!request.auth) throw new HttpsError("unauthenticated", "Auth required.");

    const { prompt, articleText, promptTitle } = request.data;
    const userId = request.auth.uid;

    if (!prompt) throw new HttpsError("invalid-argument", "Prompt required.");

    // Calcolo Costi (Semplificato)
    const userRef = db.collection("users").doc(userId);
    const inputCost = 1; // Costo fisso per messaggio chat

    // Transazione Monete
    try {
        await db.runTransaction(async (t) => {
            const doc = await t.get(userRef);
            const coins = doc.data()?.coins || 0;
            if (coins < inputCost) throw new HttpsError("resource-exhausted", "Insufficient coins.");
            t.update(userRef, { coins: FieldValue.increment(-inputCost) });
        });
    } catch (e) {
        throw e; // Rilancia errore al client
    }

    // Chiamata Gemini
    const GEMINI_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiApiKey.value()}`;

    // Costruiamo il prompt. Se c'è articleText (contesto), lo aggiungiamo.
    let fullPrompt = prompt;
    if (articleText) {
        fullPrompt = `Context:\n${articleText.substring(0, 20000)}\n\nUser Question:\n${prompt}`;
    }

    try {
        const apiRes = await fetch(GEMINI_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contents: [{ parts: [{ text: fullPrompt }] }] })
        });

        if (!apiRes.ok) {
            const err = await apiRes.json();
            throw new Error(err.error?.message || "Gemini API Error");
        }

        const data = await apiRes.json();
        const generatedText = data.candidates?.[0]?.content?.parts?.[0]?.text;

        if (!generatedText) throw new Error("No text generated.");

        return { success: true, generatedText: generatedText };

    } catch (error) {
        logger.error("AI Error:", error);
        // Rimborsa in caso di errore tecnico
        await userRef.update({ coins: FieldValue.increment(inputCost) });
        throw new HttpsError("internal", `AI Failed: ${error.message}`);
    }
});

// ===================================================================
// 3. TTS (Text to Speech)
// ===================================================================
exports.generateSpeech = onCall({
    secrets: [replicateApiKey],
    timeoutSeconds: 540,
    region: 'us-central1'
}, async (request) => {
    const fetch = require('node-fetch');
    if (!request.auth) throw new HttpsError("unauthenticated", "Auth required.");

    const { text, voice } = request.data;
    if (!text) throw new HttpsError("invalid-argument", "Text required.");

    // Logica Replicate (semplificata per brevità, assicurati che funzioni come prima)
    const apiKey = replicateApiKey.value();
    const REPLICATE_URL = "https://api.replicate.com/v1/predictions";

    try {
        const startRes = await fetch(REPLICATE_URL, {
            method: "POST",
            headers: { "Authorization": `Token ${apiKey}`, "Content-Type": "application/json" },
            body: JSON.stringify({
                version: "f559560eb822dc509045f3921a1921234918b91739db4bf3daab2169b71c7a13", // Kokoro TTS
                input: { text, voice: voice || "af_alloy", speed: 1 }
            })
        });

        if (!startRes.ok) throw new Error(await startRes.text());
        let prediction = await startRes.json();

        // Polling
        while (prediction.status !== "succeeded" && prediction.status !== "failed") {
            await new Promise(r => setTimeout(r, 1000));
            const check = await fetch(prediction.urls.get, { headers: { "Authorization": `Token ${apiKey}` } });
            prediction = await check.json();
        }

        if (prediction.status === "failed") throw new Error("Prediction failed");

        return { audioUrl: prediction.output, metrics: prediction.metrics };

    } catch (e) {
        logger.error("TTS Error:", e);
        throw new HttpsError("internal", e.message);
    }
});

// ===================================================================
// 4. AUTH & USER CREATION
// ===================================================================
exports.createToken = onRequest({ cors: true }, async (req, res) => {
    const idToken = req.body.idToken;
    try {
        const decoded = await admin.auth().verifyIdToken(idToken);
        const token = await admin.auth().createCustomToken(decoded.uid);
        res.json({ token });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

exports.createuserdocument = v1.auth.user().onCreate((user) => {
    return db.collection('users').doc(user.uid).set({
        email: user.email,
        coins: 50, // Bonus benvenuto
        createdAt: FieldValue.serverTimestamp()
    });
}); 