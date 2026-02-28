# Requisiti LLM e Configurazione Ollama

SearchMuse dipende da modelli linguistici locali eseguiti tramite Ollama. Questa sezione descrive i requisiti, modelli consigliati, configurazione hardware, e ottimizzazioni.

---

## Panoramica Ollama

**Ollama** è un runtime che permette di eseguire modelli linguistici open-source sulla propria macchina, senza dipendere da servizi cloud.

**Installazione**: Visita https://ollama.ai per scaricare la versione per il tuo OS (Windows, macOS, Linux).

**Avvio Servizio**:
```bash
# Ollama si avvia come servizio
# Si connette su http://localhost:11434

# Verificare che è in esecuzione
curl http://localhost:11434/api/tags

# Scaricare un modello
ollama pull mistral

# Chat interattiva per testare
ollama run mistral
```

---

## Modelli Consigliati

SearchMuse è stato testato e ottimizzato per questi modelli:

### 1. Mistral 7B (CONSIGLIATO PER LA MAGGIOR PARTE)

**Specifiche**:
```
Name: mistral
Size: 4 GB
Context Window: 8k tokens
Performance: High throughput
Quality: Eccellente per task generali
Memory: 8 GB RAM minimo
Latency: 100-200ms per query
```

**Vantaggi**:
- Velocità eccellente (ideal per iterazione rapida)
- Qualità ragionevole per query refinement
- Basso overhead memoria
- Model leggero, scarica velocemente
- Supporto context window 8k

**Svantaggi**:
- Leggermente meno accurato di Llama3 su task complessi
- Context window limitato (8k)

**Installation**:
```bash
ollama pull mistral
```

**Casi d'Uso**:
- Query refinement (ideale)
- Relevance scoring (buono)
- Aspect identification (buono)
- Summarization (buono, con trimming)

---

### 2. Llama 3 8B (PER QUALITÀ SUPERIORE)

**Specifiche**:
```
Name: llama3
Size: 4.7 GB
Context Window: 8k tokens
Performance: Buono
Quality: Eccellente
Memory: 10 GB RAM minimo
Latency: 150-300ms per query
```

**Vantaggi**:
- Qualità superiore a Mistral
- Eccellente su task reasoning
- Migliore comprensione contestuale
- Istruzioni seguite più accuratamente
- Multilingual capabilities

**Svantaggi**:
- Leggermente più lento di Mistral
- Più memoria richiesta
- Context window stesso di Mistral (8k)

**Installation**:
```bash
ollama pull llama3
```

**Casi d'Uso**:
- Query refinement (eccellente)
- Relevance scoring (eccellente)
- Aspect identification (eccellente)
- Summarization (eccellente)

---

### 3. Llama 3 70B (PER MASSIMA QUALITÀ)

**Specifiche**:
```
Name: llama3:70b
Size: 40+ GB
Context Window: 8k tokens
Performance: Lento
Quality: Massimo
Memory: 64+ GB RAM richiesto
Latency: 500ms-1s per query
```

**Vantaggi**:
- Migliore qualità complessiva
- Reasoning complesso e accurato
- Meno allucinazioni
- Migliore seguimento istruzioni

**Svantaggi**:
- Molto lento (impraticabile per iterazioni rapide)
- Memoria enorme richiesta (GPU VRAM o swap)
- Overhead di download (40+ GB)
- Non consigliato se max_iterations > 2

**Installation**:
```bash
ollama pull llama3:70b
```

**Casi d'Uso**:
- Ricerche singole, non iterative
- Analisi approfondita con pochi step
- Quando qualità è più importante di velocità

---

### 4. Phi 3 (PER EDGE/LIGHTWEIGHT)

**Specifiche**:
```
Name: phi3
Size: 2.2 GB
Context Window: 4k tokens
Performance: Molto veloce
Quality: Buona per il tamaño
Memory: 4 GB RAM sufficiente
Latency: 50-100ms per query
```

**Vantaggi**:
- Piccolissimo e velocissimo
- Funziona su hardware limitato (laptop vecchi)
- Download rapido
- Quantized, esecuzione CPU-only OK

**Svantaggi**:
- Qualità diminuisce su task complessi
- Context window molto limitato (4k)
- Meno affidabile su reasoning
- Non ideale per summarization lunga

**Installation**:
```bash
ollama pull phi3
```

**Casi d'Uso**:
- Dispositivi con <4GB RAM
- Query refinement veloce (sacrificando qualità)
- Prototipazione rapida
- Edge deployment

---

### 5. Neural Chat (SPECIALIZZATO PER DIALOG)

**Specifiche**:
```
Name: neural-chat
Size: 4 GB
Context Window: 8k tokens
Performance: Alto
Quality: Ottima per conversazioni
Memory: 8 GB RAM minimo
Latency: 120-200ms per query
```

**Vantaggi**:
- Fine-tuned per conversazioni e istruzioni
- Dialog quality superiore
- Buono per query refinement conversazionale
- Segue istruzioni molto bene

**Svantaggi**:
- Meno specializzato su reasoning puro
- Training data più orientato a chat

**Installation**:
```bash
ollama pull neural-chat
```

**Casi d'Uso**:
- Query refinement interpretativo
- Aspect identification conversazionale
- Quando la dialog quality è prioritaria

---

## Selezione Modello per Caso d'Uso

| Caso | Ideale | Accettabile | Evitare |
|-----|--------|-----------|---------|
| Ricerca Rapida (< 90s) | Mistral | Neural Chat, Phi3 | Llama3:70b |
| Ricerca Profonda (5 iter) | Mistral | Llama3 | Llama3:70b |
| Massima Qualità | Llama3:70b | Llama3 | Phi3 |
| Hardware Limitato | Phi3 | Mistral | Llama3:70b |
| Domain Specializzato | Llama3 | Mistral | - |

---

## Requisiti Hardware

### Configurazione Minima

```
Processore: Intel Core i5 / AMD Ryzen 5 (2GHz+)
RAM: 8 GB
Disco: 50 GB SSD (per modelli)
Connessione: Non richiesta (tutto locale)
GPU: NON richiesta (CPU works fine)
OS: Linux, macOS, Windows
```

**Modello per minimo**: Phi3 (4GB RAM ideale)

### Configurazione Consigliata

```
Processore: Intel i7 / AMD Ryzen 7
RAM: 16+ GB
Disco: 100 GB SSD
GPU: NVIDIA (CUDA) opzionale ma consigliato
OS: Linux preferred, Windows/macOS OK
```

**Modello per consigliato**: Mistral (8GB RAM ideale)

### Configurazione Ottimale

```
Processore: Intel i9 / AMD Ryzen 9
RAM: 32+ GB
Disco: 200 GB NVMe SSD
GPU: NVIDIA A6000 / H100 (64GB VRAM)
OS: Linux (Ubuntu 22.04+)
```

**Modello per ottimale**: Llama3:70b (64GB RAM + 24GB VRAM)

---

## Parametri Modello Ottimizzati

SearchMuse configura questi parametri per ogni operazione LLM:

### Query Refinement

```yaml
temperature: 0.3
  # Bassa variabilità - vogliamo query consistent
top_p: 0.9
  # Nucleus sampling - evita tail (cose strane)
top_k: 40
  # Top-k filtering
max_tokens: 100
  # Query raffinate non dovrebbero essere lunghe
repeat_penalty: 1.2
  # Penalizza ripetizioni forti
stop_sequences: ["Query:", "Next:", "\n\n"]
  # Stop quando raggiunge fine naturale
```

### Relevance Scoring

```yaml
temperature: 0.1
  # Molto bassa - vogliamo score consistent e deterministic
top_p: 0.95
  # Un po' più flessibile
max_tokens: 50
  # Solo score e spiegazione breve
num_predict: -1
  # Full generation (non limitare)
```

### Content Summarization

```yaml
temperature: 0.5
  # Media - vogliamo qualche variazione ma no randomness
top_p: 0.9
  # Standard nucleus sampling
max_tokens: 200
  # 50-150 parole target
repeat_penalty: 1.1
  # Leggera penalità per ripetizioni
```

### Aspect Identification

```yaml
temperature: 0.4
  # Bassa-media
top_p: 0.9
max_tokens: 300
  # 5-7 aspect con descrizioni
presence_penalty: 0.6
  # Penalizza aspetti ripetuti
```

---

## Prompt Templates

### Template: Query Refinement

```
Original query: {original_query}
Previous search terms used: {previous_queries}
Results found so far: {results_count}

Current coverage assessment:
Covered aspects: {covered_aspects}
Missing aspects: {missing_aspects}
Coverage score: {coverage_score}%

Based on the missing aspects and previous results,
generate a NEW search query that will find content
addressing the gaps. Make it natural language, not
keyword stuffing. Focus on missing aspects.

Return ONLY the query string, nothing else.
```

### Template: Relevance Scoring

```
Query: {query}
Content excerpt: {content_excerpt}

Score this content on relevance to the query (0-100):
- Does it directly address the main query? (0-30 pts)
- Does it cover important aspects? (0-40 pts)
- Is information recent and authoritative? (0-30 pts)

Respond with: SCORE: [number] | REASONING: [brief reason]
```

### Template: Summarization

```
Content: {content_full_text}
Query: {original_query}
Key aspects to cover: {aspects_list}

Summarize this content in 100-150 words, addressing
the key aspects relevant to the query. Assume the
reader is familiar with the topic. Be specific and
avoid filler.

Summary:
```

### Template: Aspect Identification

```
Query: {query}
Aggregated results: {results_summary}

Identify 5-7 main aspects or themes that should be
covered when answering this query comprehensively.

For each aspect provide:
1. Name (one phrase)
2. Description (one sentence)
3. Importance (high/medium/low)

Format as JSON array.
```

---

## Monitoring e Performance

SearchMuse traccia performance del modello:

```json
{
  "model_performance": {
    "query_refinement": {
      "avg_latency_ms": 145,
      "success_rate": 98,
      "avg_tokens_generated": 32
    },
    "relevance_scoring": {
      "avg_latency_ms": 85,
      "success_rate": 100,
      "agreement_with_baseline": 87
    },
    "summarization": {
      "avg_latency_ms": 320,
      "success_rate": 95,
      "avg_output_length": 128
    },
    "aspect_identification": {
      "avg_latency_ms": 210,
      "success_rate": 92,
      "avg_aspects_found": 6.2
    }
  },
  "resource_usage": {
    "avg_memory_mb": 4500,
    "avg_cpu_percent": 35,
    "gpu_vram_mb": 0,
    "requests_per_minute": 24
  }
}
```

---

## Troubleshooting

### Problema: Model non scarica / Errore connessione

**Soluzione**:
```bash
# Verificare che Ollama è in esecuzione
ollama serve

# Se non parte, reinstallare
ollama pull mistral
```

### Problema: Risposte incoerenti

**Soluzione**: Abbassare `temperature`
```bash
# In SearchMuse config
model_params:
  temperature: 0.2  # instead of 0.3
```

### Problema: Troppo lento

**Soluzione**: Cambiare modello più veloce
```bash
# Usare Mistral o Phi3 invece di Llama3:70b
# O aggiungere GPU support
```

### Problema: Out of Memory

**Soluzione**: Ridurre context window
```bash
# In SearchMuse config
context_window: 4000  # instead of 8000
```

---

## Configurazione SearchMuse

```yaml
# config.yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434"

  # Modello da usare
  model: "mistral"  # o "llama3", "phi3", etc.

  # Parametri globali
  default_temperature: 0.3
  default_top_p: 0.9
  default_top_k: 40

  # Timeouts
  request_timeout: 30
  connection_timeout: 5

  # Context
  max_context_tokens: 8000

  # Fallback
  fallback_model: "phi3"
  fallback_on_timeout: true
```

---

**Versione**: 1.0
**Ultimo aggiornamento**: 2026-02-28
