# SearchMuse - Assistente di Ricerca Web Intelligente

Benvenuti nella documentazione italiana di SearchMuse, un assistente di ricerca web intelligente che utilizza modelli di linguaggio locali tramite Ollama con perfezionamento iterativo delle ricerche e citazione delle fonti.

## Panoramica

SearchMuse è un'applicazione Python open source progettata secondo i principi dell'architettura esagonale. Combina le capacità di elaborazione del linguaggio naturale con la ricerca web intelligente, permettendo agli utenti di ottenere risposte accurate e ben fondate da molteplici fonti.

### Caratteristiche Principali

- **LLM Locali**: Integrazione con Ollama per l'elaborazione del linguaggio naturale senza dipendenze da servizi cloud
- **Ricerca Iterativa**: Perfezionamento automatico delle query di ricerca basato sui risultati iniziali
- **Citazione delle Fonti**: Tracciamento completo delle fonti con riferimenti verificabili
- **Architettura Esagonale**: Separazione chiara delle responsabilità e facilità di estensione
- **Tecnologie Moderne**: Python 3.11+, Typer CLI, Playwright, httpx, SQLite
- **Open Source**: Licenza MIT, comunità collaborativa

## Struttura della Documentazione

### Documentazione Tecnica

#### Setup e Sviluppo
- [Development Setup](./002_technical/006_development-setup.md) - Configurazione dell'ambiente di sviluppo
- [Configuration Reference](./002_technical/005_configuration-reference.md) - Guida completa ai parametri di configurazione

#### Architettura
- [Architecture](./002_technical/001_architecture.md) - Panoramica dell'architettura esagonale e ADR
- [Components](./002_technical/002_components.md) - Descrizione dettagliata di tutti i componenti
- [Data Flow](./002_technical/003_data-flow.md) - Flusso dei dati attraverso il sistema

#### API e Integrazione
- [API Reference](./002_technical/004_api-reference.md) - Riferimento completo delle classi di dominio e interfacce
- [Testing Strategy](./002_technical/007_testing-strategy.md) - Approccio TDD e strategie di test

#### Distribuzione e Produzione
- [Deployment](./002_technical/008_deployment.md) - Guida alla distribuzione e monitoraggio
- [Security](./002_technical/009_security.md) - Linee guida sulla sicurezza e best practice

#### Comunità
- [Contributing](./002_technical/010_contributing.md) - Come contribuire al progetto

## Nota sulla Documentazione in Inglese

Per la documentazione originale in inglese, consultare la cartella `/docs` del repository principale. Questa documentazione italiana è una traduzione completa dei contenuti tecnici.

## Iniziare Rapidamente

### Installazione Rapida

```bash
# Clonare il repository
git clone https://github.com/federicocalo/WebScraping.git
cd WebScraping

# Installare le dipendenze
pip install -e .

# Configurare Ollama (se non installato)
# Scaricare da https://ollama.ai

# Eseguire la prima ricerca
searchmuse "tua domanda di ricerca"
```

### Requisiti Minimi

- Python 3.11 o superiore
- Ollama con un modello LLM configurato (consigliato: mistral o neural-chat)
- 2 GB di RAM minimo
- Connessione internet per le ricerche web

## Supporto e Comunità

- **Issues**: Segnalare bug o richiedere funzionalità su GitHub
- **Discussions**: Partecipare alle discussioni della comunità
- **Contributing**: Contribuire con codice, documentazione, o test

## Licenza

SearchMuse è distribuito sotto licenza MIT. Consulta il file LICENSE nel repository per i dettagli completi.

---

**Versione Documentazione**: 1.0
**Ultimo Aggiornamento**: Febbraio 2026
**Stato**: Stabile
