# Genio Knowledge OS - User Workflows Master Document

> **Analisi completa di tutti i flussi utente con micro-passaggi**  
> **Status:** Gap Analysis per MVP Completo

---

## 📋 INDICE WORKFLOW

1. [Onboarding & First Setup](#1-onboarding--first-setup)
2. [Feed Management](#2-feed-management)
3. [Article Reading](#3-article-reading)
4. [Daily Brief](#4-daily-brief)
5. [Library & Documents](#5-library--documents)
6. [Knowledge Graph](#6-knowledge-graph)
7. [Scout Agents](#7-scout-agents)
8. [Reading List](#8-reading-list)
9. [Search](#9-search)
10. [Settings & Profile](#10-settings--profile)
11. [Administration](#11-administration)

---

## 1. ONBOARDING & FIRST SETUP

### Workflow 1.1: Registrazione Nuovo Utente
**Goal:** Creare account e accedere all'app

#### Micro-passaggi:
1. Utente arriva su landing page
2. Clicca "Get Started" / "Sign Up"
3. **FORM REGISTRAZIONE:**
   - Inserisce email
   - Inserisce password (con strength indicator)
   - Conferma password
   - Inserisce nome
   - Accetta Terms of Service (checkbox)
   - Accetta Privacy Policy (checkbox)
4. Clicca "Create Account"
5. **VALIDAZIONE:**
   - Check email valida
   - Check password policy (8 char, maiuscola, numero, speciale)
   - Check email non già registrata
6. **POST-REGISTRAZIONE:**
   - Account creato
   - JWT token generato
   - Refresh token salvato
   - Email di conferma inviata? ⚠️ **MANCANTE**
7. Redirect a onboarding wizard

**✅ Implementato:** Registrazione base, JWT  
**⚠️ Mancante:** Email verification, Onboarding wizard

---

### Workflow 1.2: Onboarding Wizard (⚠️ MANCANTE)
**Goal:** Configurare preferenze iniziali

#### Micro-passaggi:
1. **STEP 1 - Benvenuto:**
   - Messaggio benvenuto personalizzato
   - Breve spiegazione app (3 slides)
   - Clicca "Inizia"

2. **STEP 2 - Interessi:**
   - Selezione categorie interesse (Technology, Science, Business, etc.)
   - Tag input per topic specifici
   - Suggerimenti basati su trending

3. **STEP 3 - Aggiungi Feed:**
   - Import OPML da altri reader (Feedly, etc.)
   - Oppure suggerimenti feed popolari per categorie scelte
   - Checkbox "Aggiungi feed consigliati"
   - Preview feed prima di aggiungere

4. **STEP 4 - Preferenze Brief:**
   - Orario ricezione Daily Brief (time picker)
   - Fuso orario (dropdown)
   - Formato preferito (Email, Web, Both)
   - Lingua preferita

5. **STEP 5 - Budget AI:**
   - Spiegazione budget AI
   - Slider budget mensile ($0-10)
   - Toggle "Quiet Day" (salta giorni senza news rilevanti)

6. **STEP 6 - Completa:**
   - Ringraziamento
   - Anteprima dashboard
   - Clicca "Vai alla Dashboard"

**❌ STATO:** Wizard completamente assente  
**🔴 IMPATTO:** Alto - UX confusionaria per nuovi utenti

---

### Workflow 1.3: Login
**Goal:** Accedere all'app

#### Micro-passaggi:
1. Utente arriva su `/login`
2. **FORM LOGIN:**
   - Inserisce email
   - Inserisce password
   - Checkbox "Remember me" ⚠️ **MANCANTE**
   - Link "Forgot password?" ⚠️ **MANCANTE**
3. Clicca "Sign In"
4. **VALIDAZIONE:**
   - Check credenziali
   - Generate JWT + Refresh token
   - Salva in localStorage/HttpOnly cookie
5. Redirect a dashboard
6. **RECUPERO SESSIONE:**
   - Se refresh token valido, auto-login ⚠️ **MANCANTE**

**✅ Implementato:** Login base, JWT  
**⚠️ Mancante:** Remember me, Forgot password, Auto-refresh token

---

### Workflow 1.4: Password Reset (⚠️ MANCANTE)
**Goal:** Recuperare accesso se password dimenticata

#### Micro-passaggi:
1. Utente clicca "Forgot password?"
2. Inserisce email
3. Clicca "Send Reset Link"
4. **BACKEND:**
   - Generate reset token (JWT con exp breve)
   - Salva token in DB con timestamp
   - Invia email con link `/reset-password?token=xyz`
5. **EMAIL TEMPLATE:**
   - Logo Genio
   - Messaggio personalizzato
   - Link reset (valido 1 ora)
   - Istruzioni se non ha richiesto reset
6. Utente clicca link email
7. **FORM RESET:**
   - Nuova password
   - Conferma password
   - Strength indicator
8. Submit
9. **VALIDAZIONE:**
   - Check token valido e non scaduto
   - Check password policy
   - Hash nuova password
   - Invalidate token usato
   - Invia email conferma cambio password
10. Redirect a login con messaggio successo

**❌ STATO:** Completamente assente  
**🔴 IMPATTO:** Critico - bloccante per utenti reali

---

## 2. FEED MANAGEMENT

### Workflow 2.1: Aggiungere Nuovo Feed
**Goal:** Aggiungere fonte contenuto

#### Micro-passaggi:
1. Utente su pagina `/feeds`
2. **METODO A - URL Diretto:**
   - Input field "Feed URL"
   - Placeholder "https://example.com/feed.xml"
   - Pulsante "Add Feed"
   - **VALIDAZIONE:**
     - Check URL valido
     - Check URL raggiungibile
     - Check formato XML/RSS/Atom valido
     - Estrai titolo feed
     - Estrai favicon
   - **ERROR HANDLING:**
     - URL non valido → Toast error
     - Feed non raggiungibile → Toast error con retry
     - Formato invalido → Suggerisci URL alternativo
   - **SUCCESS:**
     - Feed aggiunto a lista
     - Fetch immediato articoli recenti (ultimi 10)
     - Toast successo

3. **METODO B - Import OPML:**
   - Drag & drop area file .opml/.xml
   - Oppure click per selezionare file
   - Preview feeds trovati prima di importare
   - Checkbox selezione singoli feed
   - Pulsante "Import Selected"
   - Progress bar importazione
   - Report risultato (X feeds importati, Y errori)

4. **METODO C - Discover/Suggeriti:**
   - Tab "Discover"
   - Categorie feed (Tech, Science, etc.)
   - Lista feed popolari
   - Search nella lista
   - Pulsante "+" per aggiungere
   - Trending badge

**✅ Implementato:** URL diretto, Import OPML base  
**⚠️ Mancante:** Discover/suggeriti, Favicon extraction, Preview feed

---

### Workflow 2.2: Organizzare Feed
**Goal:** Organizzare feed in categorie/cartelle

#### Micro-passaggi:
1. **CREARE CATEGORIA:**
   - Pulsante "New Category"
   - Modal con:
     - Nome categoria
     - Colore (color picker)
     - Icona (icon picker)
   - Save

2. **ASSEGNARE FEED A CATEGORIA:**
   - Drag & drop feed su categoria
   - Oppure: Edit feed → Dropdown categoria
   - Oppure: Multi-select → "Move to Category"

3. **RIORDINARE FEED:**
   - Drag & drop per riordinare
   - Sort by: Name, Date Added, Unread Count

4. **NESTED FOLDERS:**
   - Cartelle dentro cartelle
   - Expand/collapse
   - Badge count unread totali

5. **REMOVE FROM CATEGORY:**
   - Right-click → "Remove from category"
   - O trascina fuori

**❌ STATO:** Categorie completamente assenti  
**🔴 IMPATTO:** Alto - organizzazione fondamentale per molti feed

---

### Workflow 2.3: Gestione Feed Singolo
**Goal:** Configurare opzioni specifiche feed

#### Micro-passaggi:
1. **EDIT FEED:**
   - Click su feed → Modal/Drawer
   - **TAB GENERAL:**
     - Nome personalizzato
     - URL (readonly)
     - Categoria (dropdown)
     - Favicon preview
   - **TAB SETTINGS:**
     - Fetch frequency (15min, 30min, 1h, 6h, daily)
     - Max articles to keep (10, 50, 100, 500, unlimited)
     - Auto-archive after X days
     - Include in Daily Brief (toggle)
   - **TAB NOTIFICATIONS:**
     - Notify on new articles (toggle)
     - Only for high delta articles (toggle)
     - Notify via (Push, Email, In-app)
   - **TAB ADVANCED:**
     - Custom CSS selector for extraction
     - Exclude patterns (regex)
     - Only include if contains keywords
   - Save changes

2. **REFRESH MANUALE:**
   - Icona refresh accanto a feed
   - Spin while fetching
   - Badge "New X articles" dopo fetch

3. **MARK ALL READ:**
   - Right-click feed → "Mark all as read"
   - Conferma modal (se >10 articoli)

4. **DELETE FEED:**
   - Delete button
   - Confirm modal:
     - "Keep articles in library" (checkbox)
     - "Delete all articles" (default)
   - Archivia invece di cancellare? (soft delete)

**✅ Implementato:** Edit base, Refresh, Delete  
**⚠️ Mancante:** Impostazioni avanzate, Notifiche per feed, Auto-archive

---

## 3. ARTICLE READING

### Workflow 3.1: Browse Articoli
**Goal:** Trovare e leggere articoli interessanti

#### Micro-passaggi:
1. **VISTA LISTA:**
   - Lista articoli cronologica
   - **CARD ARTICOLO:**
     - Titolo (bold se unread)
     - Source (feed name + favicon)
     - Excerpt (2 righe)
     - Data pubblicazione (relativa: "2h ago")
     - Thumbnail (se disponibile)
     - **BADGES:**
       - Delta score (Novel, Related, Duplicate)
       - Word count
       - Read time estimate
     - **ACTIONS:**
       - Star (toggle)
       - Archive (toggle)
       - Read Later (add to reading list)
       - Share (copy link)
   - **INFINITE SCROLL:** ⚠️ **MANCANTE** (ora solo pagination)
   - Pull to refresh (mobile)

2. **FILTRI:**
   - **Quick Filters:**
     - All, Unread, Starred, Archived
     - Today, This Week, This Month
   - **Advanced Filters:**
     - By feed (multi-select dropdown)
     - By category
     - By delta score (slider)
     - By date range (date picker)
     - By content length (short/medium/long)
   - **SEARCH:**
     - Search bar con debounce
     - Suggestions while typing
     - Recent searches
     - Search in: Title, Content, Both

3. **SORTING:**
   - Date (newest/oldest)
   - Delta score (highest first)
   - Read time
   - Feed name

4. **VISTE ALTERNATIVE:**
   - Grid view (card più grandi con thumbnail)
   - Compact view (solo titolo)
   - Magazine view

**✅ Implementato:** Lista base, Filtri base, Star, Archive  
**⚠️ Mancante:** Infinite scroll, Advanced filters, Grid view, Search avanzata

---

### Workflow 3.2: Leggere Articolo
**Goal:** Leggere contenuto articolo

#### Micro-passaggi:
1. **READER VIEW:**
   - Click su articolo → Modal/Drawer/Page
   - **HEADER:**
     - Titolo articolo
     - Source (clickable → filtra per feed)
     - Data pubblicazione
     - Author (se disponibile)
   - **TOOLBAR:**
     - Back button
     - Star toggle
     - Read Later toggle
     - Share (copy link, native share mobile)
     - Text size (A- A A+)
     - Theme (Light, Sepia, Dark)
     - Full screen toggle
   - **CONTENT:**
     - Contenuto formattato (HTML sanitized)
     - Immagini lazy loaded
     - Links cliccabili (aprono in nuova tab)
     - **HIGHLIGHT:**
       - Seleziona testo → Toolbar appare
       - Highlight (colori: yellow, green, blue, pink)
       - Add note (popup input)
       - Copy selected
       - Share quote
     - **SEMANTIC ZOOM:** ⚠️ **MANCANTE UI**
       - Livello 1: Solo headings
       - Livello 2: Headings + key sentences
       - Livello 3: Full text
   - **FOOTER:**
     - Tags suggeriti
     - Related articles (3-5)
     - Original URL (visit source)

2. **MARK AS READ:**
   - Auto-mark dopo X secondi (configurabile)
   - Oppure manuale: click "Mark Read"
   - Progress bar lettura (scroll-based)

3. **GESTURE MOBILE:**
   - Swipe left → Archive
   - Swipe right → Star
   - Swipe up → Next article
   - Swipe down → Close

**✅ Implementato:** Reader base, Highlight  
**⚠️ Mancante:** Text size, Theme toggle, Semantic zoom UI, Gestures, Progress bar

---

### Workflow 3.3: Azioni Batch su Articoli
**Goal:** Gestire molti articoli insieme

#### Micro-passaggi:
1. **SELEZIONE MULTIPLA:**
   - Checkbox su ogni card
   - "Select All" in viewport
   - "Select All" totali (across pages)
   - Shift-click per range selection

2. **ACTION BAR:**
   - Compare quando items selezionati
   - Counter "X items selected"
   - Azioni:
     - Mark Read/Unread
     - Star/Unstar
     - Archive/Unarchive
     - Add to Reading List
     - Delete
     - Add Tag ⚠️ **MANCANTE**

3. **KEYBOARD SHORTCUTS:**
   - j/k → Next/Prev
   - o → Open
   - s → Star
   - a → Archive
   - r → Mark read
   - shift+a → Mark all read
   - ? → Show shortcuts help

**❌ STATO:** Batch operations completamente assenti  
**🔴 IMPATTO:** Alto - essenziale per produttività

---

## 4. DAILY BRIEF

### Workflow 4.1: Ricevere Brief
**Goal:** Ottenere sintesi giornaliera

#### Micro-passaggi:
1. **GENERAZIONE:**
   - Automatica all'orario configurato
   - Background job (Celery beat)
   - Email notification "Your Daily Brief is ready" ⚠️ **MANCANTE**
   - Push notification (se abilitate) ⚠️ **MANCANTE**
   - In-app notification badge

2. **QUIET DAY:**
   - Se nessun articolo rilevante
   - Messaggio: "Quiet Day - No news worth your time"
   - Suggerimento: "Adjust your delta threshold?"

**✅ Implementato:** Generazione automatica  
**⚠️ Mancante:** Email notification, Push notification

---

### Workflow 4.2: Leggere Brief
**Goal:** Consumare sintesi giornaliera

#### Micro-passaggi:
1. **BRIEF VIEW:**
   - **HEADER:**
     - Data brief
     - Article count
     - Reading time estimate
     - Share brief (PDF?) ⚠️ **MANCANTE**
   - **SECTIONS:**
     - **Executive Summary** (AI generated)
     - **Key Stories** (3-5 articoli principali)
       - Titolo
       - Bullet points key insights
       - Perché è rilevante (AI explanation)
       - Clicca per leggere articolo completo
     - **The Diff** (cosa c'è di nuovo vs ieri)
     - **Emerging Trends** (pattern rilevati)
     - **Deep Dive** (argomento approfondito)
   - **NAVIGAZIONE:**
     - TOC laterale (sticky)
     - Prev/Next brief (date navigation)
   - **AZIONI:**
     - Mark all as read
     - Save to Reading List (tutta sezione)
     - Export as PDF ⚠️ **MANCANTE**
     - Share via email ⚠️ **MANCANTE**

2. **INTERAZIONE:**
   - Espandi/collassa sezioni
   - Click su articolo → Reader view
   - Hover su link → Preview card

**✅ Implementato:** Brief base con sezioni  
**⚠️ Mancante:** PDF export, Email share, Deep Dive section

---

### Workflow 4.3: Storico Brief
**Goal:** Consultare brief passati

#### Micro-passaggi:
1. **CALENDAR VIEW:**
   - Calendario mensile
   - Giorni con brief hanno indicatore
   - Giorni "Quiet Day" hanno icona diversa
   - Click giorno → vedi brief

2. **LIST VIEW:**
   - Lista cronologica brief
   - Preview: Data, titoli principali
   - Search dentro brief

3. **STATS:**
   - Brief ricevuti questo mese
   - Articoli letti vs totali
   - Tempo risparmiato vs leggere tutto

**❌ STATO:** Storico e calendar view assenti  
**🟡 IMPATTO:** Medio - nice to have

---

## 5. LIBRARY & DOCUMENTS

### Workflow 5.1: Upload Documento
**Goal:** Aggiungere documenti personali

#### Micro-passaggi:
1. **UPLOAD:**
   - Pulsante "Upload Document"
   - **METODI:**
     - Drag & drop files su zona upload
     - Click per selezionare file
     - Paste from clipboard ⚠️ **MANCANTE**
   - **SUPPORTED FORMATS:**
     - PDF, EPUB, DOCX, TXT, MD, HTML
   - **VALIDAZIONE:**
     - Check formato
     - Check dimensione (max 50MB)
     - Check virus scan? ⚠️ **MANCANTE**
   - **UPLOAD PROGRESS:**
     - Progress bar per file
     - Upload speed
     - ETA
     - Cancel button

2. **PROCESSING:**
   - Queue status: "In coda", "Processing", "Ready", "Error"
   - Progress steps: Upload → Extraction → Chunking → Embedding → Graph Extraction
   - Percentage complete
   - Estimated time remaining

3. **POST-PROCESSING:**
   - Notifica "Document ready"
   - Auto-open when ready (toggle in settings)
   - Add to collection (dropdown)

**✅ Implementato:** Upload base, processing status  
**⚠️ Mancante:** Progress bar upload, Virus scan, Auto-open

---

### Workflow 5.2: Organizzare Documenti
**Goal:** Gestire collezione documenti

#### Micro-passaggi:
1. **COLLECTIONS/FOLDERS:**
   - Create folder (nome, colore, icona)
   - Nested folders (cartelle dentro cartelle)
   - Drag & drop documenti
   - Multi-select per batch move

2. **TAGGING:**
   - Add tags a documento
   - Tag input (autocomplete da esistenti)
   - Color coded tags
   - Filter by tag
   - Tag cloud view

3. **METADATA:**
   - Edit titolo
   - Edit author
   - Add description/notes
   - Add source URL
   - Date read

4. **VIEWS:**
   - Grid view (thumbnails)
   - List view (dettagli)
   - Tree view (folders)

**✅ Implementato:** Collections base  
**⚠️ Mancante:** Tagging completo, Thumbnails, Tree view

---

### Workflow 5.3: Lettura Documento
**Goal:** Leggere e annotare documenti

#### Micro-passaggi:
1. **READER:**
   - **TOOLBAR:**
     - Indietro
     - Titolo documento
     - Search in document
     - Text size
     - Theme (light/dark/sepia)
     - Full screen
   - **CONTENT:**
     - Rendering PDF/HTML/TXT
     - Pagination (PDF)
     - Scroll continuo (TXT/MD)
     - Sidebar TOC (se disponibile)

2. **HIGHLIGHTS & ANNOTATIONS:**
   - Seleziona testo → toolbar appare
   - Highlight colors (yellow, green, blue, pink, purple)
   - Add note (popup textarea)
   - Categorize highlight (key concept, quote, todo, etc.)
   - View all highlights sidebar
   - Export highlights (CSV, MD) ⚠️ **MANCANTE**
   - Print highlights only ⚠️ **MANCANTE**

3. **SEMANTIC ZOOM:**
   - Slider zoom level
   - Level 1: Overview (solo headings)
   - Level 2: Key concepts
   - Level 3: Full text

4. **GRAPH OVERLAY:**
   - Toggle concept overlay
   - Click concept → info card
   - Highlight related concepts in text

**✅ Implementato:** Reader base, Highlights base  
**⚠️ Mancante:** Export highlights, Semantic zoom UI, Print

---

## 6. KNOWLEDGE GRAPH

### Workflow 6.1: Esplorare Knowledge Graph
**Goal:** Visualizzare e navigare conoscenza personale

#### Micro-passaggi:
1. **GRAPH VIEW:**
   - **CONTROLS:**
     - Zoom (wheel/pinch)
     - Pan (drag)
     - Reset view
     - Full screen
     - Filter by concept type
     - Filter by confidence
     - Time slider (vedi evoluzione nel tempo) ⚠️ **MANCANTE**
   - **NODI:**
     - Dimensione = importance/confidence
     - Colore = type (concept, atom, document)
     - Label = concept name
     - Hover → tooltip con details
     - Click → open detail panel
   - **EDGES:**
     - Spessore = confidence
     - Colore = relationship type
     - Hover → show relationship type

2. **DETAIL PANEL:**
   - Concept name
   - Definition (AI generated)
   - Source documents (links)
   - Connected concepts (list)
   - Knowledge state (known/learning/gap)
   - Mark as "I know this" / "Want to learn"
   - Add personal note

3. **SEARCH IN GRAPH:**
   - Search bar
   - Autocomplete
   - Highlight matching nodes
   - Zoom to node

4. **VIEWS:**
   - Force-directed (default)
   - Hierarchical
   - Timeline (chronological)
   - Radial (ego network)

**✅ Implementato:** ConceptMap base con D3  
**⚠️ Mancante:** Detail panel completo, Time evolution, Multiple layouts

---

### Workflow 6.2: GraphRAG Search
**Goal:** Ricerca semantica con ragionamento

#### Micro-passaggi:
1. **SEARCH INTERFACE:**
   - Search bar prominente
   - Placeholder: "Ask anything about your knowledge..."
   - Voice input (mic icon) ⚠️ **MANCANTE**
   - Search suggestions (trending questions)

2. **QUERY TYPES:**
   - Natural language question
   - Keyword search
   - Cross-document query
   - Contradiction detection

3. **RESULTS:**
   - **ANSWER CARD:**
     - AI-generated answer
     - Confidence score
     - Citations (numbered links)
   - **SOURCES PANEL:**
     - Lista documenti/articoli usati
     - Relevance score per source
     - Quote esatte usate
     - Click → jump to location
   - **RELATED QUESTIONS:**
     - "People also asked..."
   - **GRAPH PATH:**
     - Visualizzazione percorso logico
     - Step-by-step reasoning

4. **FILTERS:**
   - Date range
   - Source type (articles, documents, both)
   - Confidence threshold

5. **HISTORY:**
   - Recent searches
   - Saved searches
   - Alerts (notify when new info available)

**✅ Implementato:** GraphRAGSearch component base  
**⚠️ Mancante:** Voice input, Citations, Graph path viz, Alerts

---

## 7. SCOUT AGENTS

### Workflow 7.1: Creare Scout Agent
**Goal:** Configurare agente ricerca automatica

#### Micro-passaggi:
1. **WIZARD CREAZIONE:**
   - **STEP 1 - Nome & Descrizione:**
     - Nome scout
     - Descrizione (opzionale)
     - Icona/colore
   
   - **STEP 2 - Research Question:**
     - Input principale: "What do you want to know?"
     - Esempi: "Latest developments in AI", "Competitor news"
     - AI suggestion: "Riformula per risultati migliori"
   
   - **STEP 3 - Keywords:**
     - Include keywords (tag input)
     - Exclude keywords (tag input)
     - AI suggestion da research question
   
   - **STEP 4 - Sources:**
     - Checkbox sources:
       - My Feeds
       - My Documents
       - Web Search ⚠️ **MANCANTE**
       - arXiv ⚠️ **MANCANTE**
       - News APIs ⚠️ **MANCANTE**
       - GitHub ⚠️ **MANCANTE**
     - Configurazione per source
   
   - **STEP 5 - Filters:**
     - Content type (articles, papers, videos)
     - Min relevance score (slider 0-1)
     - Date range (last 7d, 30d, 90d, 1y)
     - Language
   
   - **STEP 6 - Schedule:**
     - Frequency: Realtime, Hourly, Daily, Weekly
     - Time of day (per daily/weekly)
     - Max findings per run
   
   - **STEP 7 - Review:**
     - Preview configurazione
     - Estimated cost per run
     - Create button

2. **POST-CREAZIONE:**
   - Auto-run immediato? (toggle)
   - Notifica quando completato

**✅ Implementato:** Creazione base, Keywords, Sources (feeds/docs)  
**⚠️ Mancante:** Web/arxiv search, Wizard step-by-step, Cost estimation

---

### Workflow 7.2: Monitorare Findings
**Goal:** Revisionare scoperte degli scout

#### Micro-passaggi:
1. **FINDINGS LIST:**
   - **FILTRI:**
     - By scout (multi-select)
     - Status: All, Unread, Read, Saved, Dismissed
     - Relevance: High (>0.8), Medium, Low
     - Date range
     - Source type
   
   - **SORTING:**
     - Date (newest)
     - Relevance (highest)
     - Source
   
   - **CARD FINDING:**
     - Source title
     - Relevance score (badge color)
     - Matched keywords
     - AI explanation (why relevant)
     - Contradiction warning (if any)
     - Timestamp
     - **ACTIONS:**
       - Read/Save/Dismiss
       - Add note
       - Share
       - View original

2. **BULK ACTIONS:**
   - Select multiple
   - Mark all read
   - Save all
   - Dismiss all
   - Export (CSV) ⚠️ **MANCANTE**

3. **INSIGHTS:**
   - Tab separato "Insights"
   - Trend detection
   - Pattern recognition
   - Knowledge gaps identified
   - Opportunities

**✅ Implementato:** Findings base, Save/Dismiss  
**⚠️ Mancante:** Export, Bulk actions, Insights visualization

---

### Workflow 7.3: Verifica Claim
**Goal:** Verificare affermazione specifica

#### Micro-passaggi:
1. **INPUT:**
   - Text area: "Enter claim to verify"
   - Esempio: "Is it true that...?"
   - Select scout context (optional)

2. **PROCESSING:**
   - Spin "Researching..."
   - Search across PKG
   - Find supporting/contradicting evidence

3. **RESULT:**
   - Verdict: Supported / Contradicted / Uncertain
   - Confidence score
   - Evidence list (pro/con)
   - Sources cited
   - Recommendation

**✅ Implementato:** Endpoint API esiste  
**⚠️ Mancante:** UI completa

---

## 8. READING LIST

### Workflow 8.1: Aggiungere a Reading List
**Goal:** Salvare contenuto per dopo

#### Micro-passaggi:
1. **DA ARTICOLO:**
   - Click icona bookmark in lista
   - Oppure in reader view
   - Badge counter incrementa

2. **DA URL MANUALE:**
   - "Add URL" in reading list page
   - Input URL
   - Auto-extract title/preview

3. **BROWSER EXTENSION:**
   - Click extension icon
   - Salva pagina corrente
   - Select tags
   - Add note

4. **ORGANIZZAZIONE:**
   - Tags
   - Priority (High, Normal, Low)
   - Due date (optional)
   - Notes

**✅ Implementato:** Aggiunta base da articoli  
**⚠️ Mancante:** Browser extension, Tags, Priority

---

### Workflow 8.2: Gestire Reading List
**Goal:** Consumare contenuto salvato

#### Micro-passaggi:
1. **VISTE:**
   - All items
   - Unread
   - Archived
   - By tag
   - By priority

2. **AZIONI:**
   - Mark as read
   - Archive
   - Delete
   - Move to Library (save as document)
   - Share

3. **STATS:**
   - Items added this week
   - Read vs unread ratio
   - Average time to read

**✅ Implementato:** CRUD base  
**⚠️ Mancante:** Stats, Priority management

---

## 9. SEARCH

### Workflow 9.1: Global Search
**Goal:** Trovare qualsiasi contenuto nell'app

#### Micro-passaggi:
1. **SEARCH BAR:**
   - Posizione: Header (sempre visibile)
   - Shortcut: Cmd/Ctrl + K
   - Modal con focus auto
   - Recent searches
   - Trending searches

2. **SCOPE SELECTION:**
   - All
   - Articles
   - Documents
   - Briefs
   - Knowledge Graph

3. **RESULTS:**
   - Grouped by type
   - Highlight matching terms
   - Preview snippet
   - Filters sidebar

4. **ADVANCED SEARCH:**
   - Query syntax (AND, OR, NOT)
   - Date range
   - Source filters
   - File type (per documents)

**❌ STATO:** Global search assente  
**🔴 IMPATTO:** Alto - essenziale per navigazione

---

## 10. SETTINGS & PROFILE

### Workflow 10.1: Gestire Profilo
**Goal:** Configurare account utente

#### Micro-passaggi:
1. **PROFILE PAGE:**
   - **INFO PERSONALI:**
     - Avatar (upload/Gravatar)
     - Nome
     - Email (readonly se verified)
     - Bio
   
   - **PASSWORD:**
     - Current password
     - New password
     - Confirm password
   
   - **ACCOUNT:**
     - Email notifications toggle
     - Push notifications toggle
     - Language preference
     - Timezone
     - Delete account (with confirmation)

2. **INTEGRAZIONI:**
   - Connect Google
   - Connect GitHub
   - Browser extension install

**⚠️ Mancante:** Avatar upload, Password change, Account deletion

---

### Workflow 10.2: Preferenze App
**Goal:** Configurare comportamento app

#### Micro-passaggi:
1. **DAILY BRIEF:**
   - Delivery time
   - Timezone
   - Format (Email, Web, Both)
   - Quiet day threshold
   - Max articles per brief

2. **READING:**
   - Default text size
   - Default theme
   - Auto-mark as read (after X seconds)
   - Scroll progress indicator
   - Font family (serif/sans)

3. **NOTIFICATIONS:**
   - New articles (toggle)
   - New findings from scouts (toggle)
   - Budget alerts (toggle)
   - Digest frequency

4. **AI SETTINGS:**
   - Monthly budget limit
   - Preferred models
   - Auto-summarize threshold

5. **PRIVACY:**
   - Data export (GDPR)
   - Activity log view
   - Third-party integrations

**✅ Implementato:** Preferenze brief base  
**⚠️ Mancante:** Molte opzioni avanzate

---

### Workflow 10.3: Billing & Subscription
**Goal:** Gestire pagamenti

#### Micro-passaggi:
1. **CURRENT PLAN:**
   - Plan name
   - Price
   - Renewal date
   - Usage this month (articles, API calls)

2. **AI BUDGET:**
   - Used / Total
   - Progress bar
   - Cost breakdown by operation
   - Alert when 80% used
   - Top-up (if prepaid)

3. **CHANGE PLAN:**
   - Compare plans
   - Upgrade/Downgrade
   - Stripe checkout

4. **PAYMENT METHOD:**
   - Card on file
   - Add new card
   - Billing address

5. **INVOICES:**
   - History
   - Download PDF
   - Email receipts

**✅ Implementato:** Stripe integration base  
**⚠️ Mancante:** Usage dashboard, Invoices UI

---

## 11. ADMINISTRATION

### Workflow 11.1: Platform Monitoring
**Goal:** Monitorare salute piattaforma (Admin only)

#### Micro-passaggi:
1. **DASHBOARD:**
   - Active users (today/week/month)
   - Total feeds/articles
   - System health indicators
   - Recent errors
   - Queue status (Celery)

2. **USER MANAGEMENT:**
   - List all users
   - Filter by tier, status
   - Disable/Enable user
   - Impersonate user ⚠️ **MANCANTE**
   - View user activity

3. **SYSTEM HEALTH:**
   - DB connection
   - Redis connection
   - Qdrant connection
   - External APIs status
   - Disk space
   - Memory usage

**✅ Implementato:** Admin endpoints base  
**⚠️ Mancante:** UI Admin completa

---

## 📊 RIEPILOGO GAP CRITICI

### 🔴 CRITICO (Bloccante per launch)

| # | Feature | Workflow | Impatto |
|---|---------|----------|---------|
| 1 | **Onboarding Wizard** | 1.2 | Alto - senza guida, utenti persi |
| 2 | **Password Reset** | 1.4 | Critico - bloccante accesso |
| 3 | **Error States UI** | 3.1, 5.1 | Alto - UX frustrante |
| 4 | **Global Search** | 9.1 | Alto - navigazione impossibile |
| 5 | **Batch Operations** | 3.3 | Alto - produttività |

### 🟡 MEDIO (Importante)

| # | Feature | Workflow | Impatto |
|---|---------|----------|---------|
| 6 | Email Verification | 1.1 | Medio - trust |
| 7 | Feed Categories | 2.2 | Medio - organizzazione |
| 8 | Advanced Filters | 3.1 | Medio - discovery |
| 9 | Tagging Documents | 5.2 | Medio - organizzazione |
| 10 | Scout Insights UI | 7.2 | Medio - valore scout |

### 🟢 BASSO (Nice to have)

| # | Feature | Workflow | Impatto |
|---|---------|----------|---------|
| 11 | Brief History Calendar | 4.3 | Basso |
| 12 | Voice Input | 6.2 | Basso |
| 13 | Social Sharing | 4.2 | Basso |
| 14 | Print Features | 5.3 | Basso |

---

## 🎯 RECOMMENDED PRIORITY ORDER

### Sprint 1 (Critical)
1. Password Reset Flow
2. Error States Component + Integration
3. Global Search
4. Batch Operations

### Sprint 2 (High)
5. Onboarding Wizard
6. Feed Categories
7. Advanced Filters
8. Tagging System

### Sprint 3 (Medium)
9. Email Verification
10. Scout Insights UI
11. Billing Dashboard
12. Admin UI

---

**Documento creato per guidare sviluppo completo dell'UX** 🎯
