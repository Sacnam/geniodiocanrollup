# Genio Knowledge OS - Architettura Prodotto

> **Versione:** 1.0  
> **Ultimo aggiornamento:** Febbraio 2026  
> **Stato:** MVP in sviluppo

---

## 🎯 Visione Generale

**Genio** è un **sistema operativo personale per la conoscenza** che aiuta gli utenti a:
- **Raccogliere** informazioni da fonti multiple (RSS, documenti, web)
- **Organizzare** automaticamente contenuti in una knowledge base personale
- **Assimilare** meglio ciò che si legge con strumenti AI-powered
- **Ricordare** connessioni e concetti attraverso grafi della conoscenza

### Value Proposition
> "Un assistente di ricerca personale che legge migliaia di fonti al tuo posto, ricorda tutto ciò che hai letto, e ti aiuta a trovare connessioni tra idee sparse."

---

## 🏗️ Architettura a Tre Livelli

```
┌─────────────────────────────────────────────────────────────────┐
│                     LIVELLO 1: ACQUISIZIONE                      │
│                   (Come entra l'informazione)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Estensione  │  │     Web      │  │      Upload          │  │
│  │   Browser    │  │    Scraping  │  │   (PDF/EPUB/DOCX)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LIVELLO 2: PROCESSING                        │
│              (Come viene elaborata l'informazione)               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    BACKEND (FastAPI)                     │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────────────┐  │   │
│  │  │  RSS    │ │Document │ │  AI     │ │  Knowledge    │  │   │
│  │  │ Parser  │ │Parser   │ │Gateway  │ │   Graph       │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LIVELLO 3: CONSUMO                           │
│                (Come l'utente interagisce)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Web App     │  │  Estensione  │  │    E-Reader          │  │
│  │  (React)     │  │   Sidebar    │  │   (EPUB/PDF)         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Componenti del Prodotto

### 1. ESTENSIONE BROWSER (Chrome/Firefox)
**Percorso:** `genio_extension/`

#### Cos'è
Un'estensione Manifest V3 che funziona direttamente nel browser dell'utente.

#### Cosa fa
| Funzione | Descrizione | Costo per te |
|----------|-------------|--------------|
| **Save Article** | Salva pagine web in lettura più tardi | 0€ (locale) |
| **RSS Reader** | Legge feed RSS/Atom direttamente | 0€ (fetch browser) |
| **Reader Mode** | Pulisce pagine per lettura focus | 0€ (locale) |
| **Highlighting** | Evidenzia testo su pagine web | 0€ (locale) |
| **Sidebar AI** | Chat con AI su contenuto pagina | $$$ (API AI) |

#### Target Utente
- Utenti che navigano molto e vogliono salvare contenuti rapidamente
- Utenti FREE (funziona offline, nessun backend richiesto)

#### Tech Stack
- JavaScript vanilla (no framework per leggerezza)
- IndexedDB (storage locale)
- EPUB.js (lettura libri)
- Readability.js (parsing articoli)

---

### 2. WEB APP (React + FastAPI)
**Percorso:** `genio-mvp/`

#### Cos'è
L'applicazione principale accessibile via browser all'indirizzo `app.genio.ai`.

#### Cosa fa

##### 2.1 Modulo STREAM (Feed Aggregator)
```
RSS Feeds → Fetch → Deduplicazione AI → Daily Brief
```
| Funzione | Descrizione |
|----------|-------------|
| **Feed Management** | Aggiungi/organizza fonti RSS |
| **Daily Brief** | RIepilogo giornaliero AI-generato |
| **Deduplication** | Raggruppa articoli simili |
| **Knowledge Delta** | Evidenzia solo info nuove |

##### 2.2 Modulo LIBRARY (Document Management)
```
Upload → Parse → Chunking Semantico → Knowledge Graph
```
| Funzione | Descrizione |
|----------|-------------|
| **Universal Parser** | PDF, EPUB, DOCX, TXT, MD |
| **E-Reader** | Lettura con annotazioni AI |
| **Semantic Search** | Cerca per concetto, non keyword |
| **Knowledge Graph** | Visualizza connessioni tra documenti |
| **Flashcards** | Generazione automatica + spaced repetition |

##### 2.3 Modulo LAB (Research Agents)
```
Topic → Scout Agent → Multi-source → Insights Report
```
| Funzione | Descrizione |
|----------|-------------|
| **Scout Agents** | Ricerca automatizzata su topic |
| **Monitoring** | Traccia fonti nel tempo |
| **Pattern Detection** | Trova trend nei dati raccolti |

#### Target Utente
- Utenti PRO (richiede backend, database, AI)
- Ricercatori, giornalisti, studenti, professionisti

#### Tech Stack
**Frontend:**
- React 18 + TypeScript
- TanStack Query (data fetching)
- Tailwind CSS
- D3.js (visualizzazioni)

**Backend:**
- FastAPI (Python)
- PostgreSQL (dati)
- Qdrant (vector DB)
- Redis (cache)
- Celery (task queue)

---

### 3. MOBILE APP (Futuro)
**Stato:** Non ancora sviluppato

#### Piano
- **React Native** o **Flutter** per cross-platform
- Sincronizzazione con backend
- Focus su reading e note-taking

#### Priorità
🔴 Non prioritaria per MVP — l'estensione + web app responsive coprono il 90% dei casi d'uso.

---

### 4. DESKTOP APP (Futuro)
**Stato:** Non ancora sviluppato

#### Piano
- **Tauri** (Rust + WebView) o **Electron**
- Lettura offline di documenti
- Sync quando online

#### Priorità
🟡 Bassa — l'estensione browser copre già molto del desktop usage.

---

## 🔄 Flusso Dati tra Componenti

### Scenario: Utente salva articolo
```
1. UTENTE clicca "Save to Genio" su blog.com/article
   ↓
2. ESTENSIONE estrae contenuto (Readability.js)
   ↓
3. ESTENSIONE salva in IndexedDB (locale)
   ↓
4. SE utente è FREE: stop qui (dati solo locale)
   
   SE utente è PRO:
   ↓
5. ESTENSIONE invia a BACKEND (quando online)
   ↓
6. BACKEND processa: estrazione, embedding, grafo
   ↓
7. DATI disponibili su WEB APP
```

### Scenario: Utente legge libro EPUB
```
1. UTENTE carica file in ESTENSIONE (drag & drop)
   ↓
2. ESTENSIONE salva in IndexedDB (locale)
   ↓
3. UTENTE apre E-Reader nell'estensione
   ↓
4. Lettura avviene 100% offline
   ↓
5. Highlights/annotazioni salvate in locale
   ↓
6. SE utente è PRO: sync con backend quando online
```

---

## 💰 Modello di Business per Componente

| Componente | FREE | PRO ($5/mese) | ENTERPRISE |
|------------|------|---------------|------------|
| **Estensione** | Tutto offline, no sync | Sync cloud, AI illimitata | SSO, Teams |
| **Web App STREAM** | 10 feed, no AI | Feed illimitati, Daily Brief AI | API access |
| **Web App LIBRARY** | 10 documenti, reader base | Illimitato, GraphRAG, flashcards | On-premise |
| **Web App LAB** | Non incluso | Scout agents inclusi | Custom agents |

---

## 🎯 Matrice Funzionalità vs Componente

| Funzionalità | Estensione | Web App | Mobile (futuro) |
|--------------|------------|---------|-----------------|
| Save articles | ✅ | ✅ | ✅ |
| Read RSS | ✅ | ✅ | ✅ |
| Reader mode | ✅ | ❌ | ❌ |
| Read EPUB/PDF | ✅ | ✅ | ✅ |
| Full-text search | ⚡ (locale) | ✅ (cloud) | ✅ |
| AI summarization | ❌ | ✅ | ✅ |
| Knowledge Graph | ❌ | ✅ | ⚡ (simplified) |
| Flashcards/Quiz | ⚡ (base) | ✅ (avanzato) | ✅ |
| Daily Brief | ❌ | ✅ | ✅ |
| Scout Agents | ❌ | ✅ | ❌ |
| Offline mode | ✅ | ⚡ (parziale) | ✅ |

*Legenda: ✅ Completo | ⚡ Limitato | ❌ Non disponibile*

---

## 🛠️ Stack Tecnologico Riassuntivo

| Layer | Tecnologia | Motivazione |
|-------|------------|-------------|
| **Extension** | Vanilla JS | Leggera, no build, offline-first |
| **Web Frontend** | React + TS | Type safety, ecosystem |
| **Web Backend** | FastAPI + SQLModel | Veloce, moderno, Python AI-friendly |
| **Database** | PostgreSQL | Affidabile, JSON support |
| **Vector DB** | Qdrant | Efficiente, self-hosted |
| **AI Gateway** | OpenAI + Gemini | Fallback, cost optimization |
| **Task Queue** | Celery + Redis | Background jobs |
| **Auth** | JWT + bcrypt | Standard, sicuro |
| **Storage** | S3-compatible | Files, audio TTS |

---

## 🚀 Roadmap Componenti

### Q1 2026 (Current)
- ✅ Estensione browser v1.0 (offline-first)
- ✅ Web app MVP (Stream + Library)
- 🔄 Testing e bugfixing

### Q2 2026
- ✅ Modulo LAB (Scout Agents)
- ✅ E-Reader avanzato con AI
- 🔄 Mobile web app (PWA)

### Q3 2026
- 🔄 Native mobile app (iOS/Android)
- 🔄 Desktop app (Tauri)
- 🔄 Plugin system

### Q4 2026
- 🔄 Enterprise features (SSO, teams)
- 🔄 Marketplace templates

---

## 🤔 Decisioni Architetturali Chiave

### 1. Perché l'estensione è offline-first?
**Per ridurre i costi operativi.** Se 100.000 utenti free fanno tutto sul nostro backend, falliamo. Se fanno tutto in locale e solo gli utenti pro paganti usano il backend, scaliamo in profitto.

### 2. Perché due codebase (extension vs web)?
**Per ottimizzare l'esperienza.** L'estensione deve essere istantanea (< 100ms), la web app può permettersi load time maggiore per feature più complesse.

### 3. Perché non un'unica app Electron/Tauri?
**Perché il browser è dove gli utenti passano il 90% del tempo.** Un'app desktop sarebbe usata dal 5% degli utenti ma costerebbe il 50% dello sviluppo.

---

## 📞 Contatti e Documentazione

- **MVP Docs:** `genio-mvp/README.md`
- **Extension Docs:** `genio_extension/README.md`
- **API Docs:** `https://api.genio.ai/docs`
- **Design System:** Figma (link interno)

---

*Questo documento è vivo. Aggiornare quando cambiano architettura o priorità.*
