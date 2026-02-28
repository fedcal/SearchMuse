# Limitazioni e Scope

È importante comprendere cosa SearchMuse può e non può fare. Questa sezione articola chiaramente le limitazioni in quattro categorie.

---

## Limitazioni di Scope

SearchMuse è uno strumento specializzato, non un sistema universale. Ha un'area specifica di applicazione eccellente e aree dove non è appropriato.

### What SearchMuse DOES Well

✓ Ricerca di informazioni fattiche generali sul web
✓ Sintesi di testo da multiple fonti
✓ Identificazione di tendenze e pattern da web pubblico
✓ Generazione di bibliografia verificabile
✓ Ricerche iterative con feedback refinement
✓ Ricerca su argomenti tecnici e contemporanei
✓ Estrazione di informazioni strutturate da articoli
✓ Comparazione di prodotti/servizi basata su review pubbliche

### What SearchMuse DOES NOT Do

✗ Ricerca accademica rigorosa (Usa PubMed, Google Scholar, JSTOR)
✗ Analisi di dati proprietari (Accesso a database commerciali)
✗ Accesso a contenuto pagato/premium (LinkedIn, paywalled news)
✗ Monitoraggio in tempo reale (Non è un alert system)
✗ Analisi predittiva (Non genera modelli o previsioni)
✗ Recupero di informazioni personali (Privacy-respecting)
✗ Interrogazione di database privati (Solo contenuto pubblico)
✗ Consensus building (Non "decide" risposte, aggrega solo)

---

## Limitazioni di Qualità

La qualità dei risultati di SearchMuse è vincolata da diversi fattori:

### 1. Qualità Variabile della Fonte

**Problema**: Non tutte le fonti sul web sono uguali. Alcuni siti contengono misinformation, altre sono expert-authored, altre ancora sono outdated.

**Impatto**:
- Risultati includono potential inaccuracies dalla fonte
- LLM non sempre detecta misinformation
- Authority scoring è euristico, non definitivo

**Mitigation**:
- Sempre verifica affermazioni critiche nella fonte originale
- Preferisci domini autorevoli (.edu, .gov, noti publication)
- Nota discrepanze tra fonti
- Usa result diversity come signal di confidence

**Esempio problematico**:
```
Query: "is flat earth possible?"
Result: SearchMuse troverà articoli flat-earth conspiracies
Rischio: Se non leggi attentamente source, potresti credere misinformation
Soluzione: Verifica sempre fonti, preferisci scienza peer-reviewed
```

### 2. Allucinazioni LLM

**Problema**: I modelli LLM talvolta generano informazioni false che suonano plausibili. Usano "temperature" bassa per minimizzare ma non eliminare il rischio.

**Impatto**:
- Query refinement potrebbe proporre query non logiche
- Summary potrebbe contenere deduzioni false
- Aspect identification potrebbe aggiungere aspetti non supportati

**Mitigation**:
- SearchMuse require citazioni per ogni claim
- Claims senza source sono visibilmente evidenti
- Sempre controlla source originale per claim importante
- Riporta allucinazioni visibili per improvement

**Esempio**:
```
Query: "Python 4.0 release date"
Hallucination possibile: LLM aggiunge "Available since May 2025"
Reality: Python 3.12 è latest (Feb 2026), non c'è Python 4.0
Protection: Se claim non è nella source, non lo cita
```

### 3. Recency di Informazione

**Problema**: Il web è in costante cambio. Training data di LLM ha cutoff, dati web hanno delay di indicizzazione e cacching.

**Impatto**:
- Informazioni "2026" potrebbero essere effettivamente 2025
- Prezzi, statistiche, rank cambiano frequentemente
- Ultime notizie potrebbero richiedere ore per propagarsi

**Mitigation**:
- SearchMuse preferizia siti recenti (score più alto)
- Timestamp di accesso è registrato (Feb 28, 2026)
- Per argomenti ad evoluzione veloce, riricerca spesso
- Nota data accesso in ogni citazione

### 4. Incompletezza Dovuta a Coverage Web

**Problema**: Non tutto il web è pubblico, indicizzabile, o scrapabile. Informazioni dietro paywall, login, o JavaScript complesso è inaccessibile.

**Impatto**:
- Articoli paywalled (Bloomberg, FT, paywalled news) non accessibili
- Contenuto behind login (LinkedIn, GitHub private) non accessibile
- PDF-heavy siti difficili da scrapare
- JavaScript SPAs richiedono rendering (lento, fallible)

**Mitigation**:
- SearchMuse tenta fallback (Wayback Machine per archived)
- Circu breaker per siti irraggiungibili
- Disclose quando coverage è incompleta
- Suggest alternative public sources

---

## Limitazioni Tecniche

Vincoli tecnici determinati dall'architettura di SearchMuse:

### 1. Context Window LLM

**Problema**: I modelli LLM hanno limiti di input (context window). Mistral = 8k token, circa 6000 parole.

**Impatto**:
- Articoli molto lunghi sono troncati
- Summarization può perdere dettagli per contenuto long
- Query refinement ha visibilità limitata

**Mitigation**:
- Articoli sono trimmati intelligentemente (head + tail + important sections)
- Long articles sono fragmentati e processati separatamente
- User può aumentare max_iterations per coverage di lunghi articoli

**Esempio**:
```
Articolo lungo (20,000 parole) è processato così:
- Prendi primi 1000 parole (context)
- Prendi ultimi 1000 parole (summary)
- Estrai headings e jump to important sections
- Risultato: ~6000 token di content rilevante
```

### 2. Latency di Ricerca

**Problema**: Iterative search è più lento di single-pass ricerca. Ogni iterazione richiede scraping, extraction, LLM scoring.

**Impatto**:
- Ricerca iterativa richiede 1-5 minuti (vs 30+ minuti manuali)
- Hardware lento fattore limitante
- GPU rendering di JS-heavy sites è lento

**Mitigation**:
- Default max_iterations = 3 (buon balance)
- Fast strategy = 1-2 iterazioni (< 90 secondi)
- Caching delle query identiche (24 ore)
- Asyncio parallelization del scraping

### 3. Pulizia di Contenuto

**Problema**: Estrarre testo puro da HTML sporco è difficile. Pubblicità, popup, elementi irrilevanti contamina il contenuto.

**Impatto**:
- Articoli con molto "rumore" potrebbero essere incompleti
- Tabelle/codice potrebbe perdersi
- Formattazione originale non preservata completamente

**Mitigation**:
- Multi-strategy extraction (trafilatura, readability, CSS selectors)
- Fallback a Wayback Machine per archived clean version
- Content confidence scoring (nota problemi estratti)

---

## Limitazioni Site-Specifiche

Alcune categorie di siti hanno limitazioni particolari:

### Social Media (Reddit, Twitter, LinkedIn)

```
Success Rate: 50-75%
Challenges:
  - Aggressive rate limiting
  - Dynamic content (JavaScript)
  - Session-required content
  - Misinformation prevalence

Recommendation: Use as secondary source, verify claims
```

### E-commerce (Amazon, eBay)

```
Success Rate: 60-70%
Challenges:
  - Pricing data volatile
  - Product availability changes
  - Reviews are subjective
  - Dynamic page structure

Recommendation: Good for product comparison, not pricing verification
```

### Paywalled News (FT, WSJ, Bloomberg)

```
Success Rate: 5-20%
Challenges:
  - Explicit paywall blocks content
  - Fallback to Wayback Machine limited
  - Article quality is premium (worth paying)

Recommendation: Subscribe if important, or use free aggregators
```

### Academic Papers (ArXiv, JSTOR, SSRN)

```
Success Rate: 85%+ (ArXiv), 10-30% (JSTOR)
Challenges:
  - JSTOR requires subscription
  - PDF rendering complex
  - Citation extraction difficult

Recommendation: Use for preprints (ArXiv), avoid paywalled journals
```

### Code Repositories (GitHub)

```
Success Rate: 95%+
Challenges:
  - API rate limiting (60 req/hr unauthenticated)
  - README extraction good, code context limited
  - Issue/PR context sometimes unclear

Recommendation: Excellent for documentation, good for issues
```

---

## Confronto con Strumenti Alternativi

### vs. Google Search

**SearchMuse Vantaggi**:
- Risultati tracciabili (citazioni complete)
- Privacy-first (niente dati a Google)
- Iterative refinement automatico
- Offline capable

**Google Vantaggi**:
- Velocissimo (miliardi di documenti indicizzati)
- Migliore ranking (ML di Google è superior)
- Integrazione con ekosistema Google
- Voice search, visual search

**Quando usare SearchMuse**: Ricerca tracciabile, privacy-critical, topic approfondito
**Quando usare Google**: Quick facts, viralità, immagini

---

### vs. ChatGPT

**SearchMuse Vantaggi**:
- Dati attuali (live web scraping)
- Citazioni verificabili (ogni fatto tracciato)
- Privacy-first (LLM locale)
- Free/open-source (costo operativo)

**ChatGPT Vantaggi**:
- Conversazione stateful (context storico)
- Migliore reasoning (modello superiore)
- Capacità multi-modale (images, audio)
- Faster response (pre-trained, nessun scraping)

**Quando usare SearchMuse**: Ricerca fattuale, citazioni obbligatorie, dati attuali
**Quando usare ChatGPT**: Brainstorming, writing assistance, conversazione

---

### vs. Database Accademici (PubMed, Google Scholar)

**SearchMuse Vantaggi**:
- Contenuto contemporaneo (news, blogs)
- Setup facile (niente account/subscription)
- Ricerca rapida (non richiede expertise)

**Google Scholar Vantaggi**:
- Peer-reviewed content only
- Citation tracking (who cited this paper)
- h-index e metrics dell'autore
- Rigore scientifico garantito

**Quando usare SearchMuse**: General knowledge, contemporaneo, non-accademico
**Quando usare Google Scholar**: Ricerca accademica, peer-reviewed richiesto

---

## Disclaimer di Responsabilità

SearchMuse è uno strumento di ricerca, non una fonte di verità. Utenti sono responsabili per:

1. **Verificare Affermazioni Critiche**: Soprattutto per salute, legale, finanziale
2. **Valutare Fonti**: Considera authority, bias, recency della fonte
3. **Disclosure di Fonti**: Quando usi risultati SearchMuse, cita le fonti originali
4. **Comprensione di Limitazioni**: Leggi questa sezione, comprendi cosa tool non fa
5. **Rischi Specifici di Dominio**:
   - **Salute**: Sempre consulta medico, non usare per diagnosi
   - **Legale**: Consulta avvocato, non è legal advice
   - **Finanziale**: Consulta advisor, non è financial advice
   - **Sicurezza**: Test thoroughly, non è security audit

---

## Segnalazione di Problemi

Se scopri limitazione non documentata, allucinazione LLM, o fonte corrotta:

1. Apri Issue su GitHub
2. Includi: query, risultato problematico, fonte affetta
3. Specifica: categoria (hallucination, staleness, misinformation)
4. Contribuisci fix se possibile

La comunità di SearchMuse migliora continuamente basandosi su feedback.

---

**Versione**: 1.0
**Ultimo aggiornamento**: 2026-02-28
