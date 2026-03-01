"""Lightweight internationalization for SearchMuse UI strings.

Provides a simple catalog-based translation system without external
dependencies. Each supported locale maps message keys to translated strings.

Usage::

    from searchmuse.infrastructure.i18n import get_translator

    t = get_translator("it")
    print(t("welcome"))         # "Benvenuto in SearchMuse!"
    print(t("missing_key"))     # Falls back to English
"""

from __future__ import annotations

from typing import Final

_CATALOG: Final[dict[str, dict[str, str]]] = {
    "en": {
        # Banner & general
        "welcome": "Welcome to SearchMuse!",
        "goodbye": "Goodbye!",
        "tips_title": "Tips for getting started",
        "provider_status": "Provider status",
        "type_query_hint": "Type a research query and press Enter. Type 'help' for commands, 'exit' to quit.",

        # Interactive help
        "help_title": "SearchMuse Interactive Mode",
        "help_commands": "Commands:",
        "help_query": "Run a research query",
        "help_models": "List installed Ollama models",
        "help_use_model": "Switch model for this session",
        "help_lang": "Switch UI language",
        "help_help": "Show this help message",
        "help_exit": "Leave the interactive session",
        "help_options": "Options:",
        "help_provider_flag": "after your query to switch provider",
        "help_iterations_flag": "after your query to limit iterations",
        "help_examples": "Examples:",
        "help_ctrl_c": "to cancel a running search.",
        "help_ctrl_d": "to exit.",

        # Progress
        "search_started": "Search session started",
        "generating_strategy": "Generating search strategy",
        "scraping_pages": "Scraped {count} pages",
        "extracting_content": "Extracting content",
        "assessing_contents": "Assessing {count} contents",
        "synthesizing": "Synthesizing final answer",
        "search_complete": "Search complete in {duration}s",
        "search_interrupted": "Search interrupted.",

        # Ollama
        "ollama_unreachable": "Cannot reach Ollama at {url}",
        "ollama_start_hint": "Make sure Ollama is running: ollama serve",
        "no_models_installed": "No models installed.",
        "pull_hint": "Pull one with: searchmuse ollama pull <model>",
        "pulling_model": "Pulling model {model} from Ollama registry...",
        "pull_success": "Model {model} pulled successfully!",
        "pull_failed": "Pull failed: {error}",
        "model_available": "Model {model} is available.",
        "model_not_installed": "Model {model} is not installed.",
        "model_pull_first": "Pull it first: searchmuse ollama pull {model}",
        "model_env_hint": "To use it, set the environment variable:",
        "model_config_hint": "Or add to your config YAML:",
        "switched_model": "Switched to model {model} for this session.",
        "switched_lang": "UI language switched to {lang}.",

        # Errors
        "validation_error": "Validation Error",
        "auth_error": "LLM Authentication Error",
        "connection_error": "LLM Connection Error",
        "config_error": "Configuration Error",
        "search_error": "Search Error",
        "check_api_key": "Check your API key: searchmuse config set-key <provider> <key>",
        "ensure_service": "Make sure the LLM service is available.",

        # Config
        "checking_services": "Checking services (provider: {provider})...",
        "connected_to": "Connected to {url} (model: {model})",
        "cannot_reach": "Cannot reach {url}",
        "api_key_resolved": "API key resolved",
        "no_api_key": "No API key found",
        "search_backend_ok": "Search backend available (no auth required)",
        "db_path": "Database path: {path}",
        "key_stored": "API key for {provider!r} stored in system keyring.",
        "key_store_failed": "Failed to store API key for {provider!r}.",
        "keyring_unavailable": "The 'keyring' package is not installed.",
        "no_key_found": "No API key found for {provider!r}.",

        # Phase labels
        "phase_initializing": "Initializing",
        "phase_strategizing": "Strategizing",
        "phase_scraping": "Scraping",
        "phase_extracting": "Extracting",
        "phase_assessing": "Assessing",
        "phase_synthesizing": "Synthesizing",
        "phase_complete": "Complete",
        "phase_failed": "Failed",

        # Display
        "starting": "Starting...",
        "error_panel_title": "Error",
        "config_panel_title": "Configuration",
        "keyring_error": "Keyring Error",
        "keyring_install_hint": "Install it with: pip install 'searchmuse[keyring]'",
        "unsupported_lang": "Unsupported language {lang}. Supported: {supported}",
        "error_fetching_models": "Error fetching models: {error}",
        "ollama_conn_title": "Connection Error",

        # Chat memory
        "chat_saved": "Chat saved as '{name}'.",
        "chat_loaded": "Chat '{name}' loaded ({count} messages).",
        "chat_renamed": "Chat renamed to '{name}'.",
        "chat_new_started": "New chat started.",
        "chat_list_title": "Saved Chats",
        "chat_list_empty": "No saved chats.",
        "chat_not_found": "Chat '{name}' not found.",
        "chat_context_summary": "Current context: {count} previous messages.",
        "chat_no_context": "No context (first message in chat).",
        "chat_deleted": "Chat '{name}' deleted.",
        "chat_auto_created": "Chat session created automatically.",
        "chat_col_name": "Name",
        "chat_col_date": "Date",
        "chat_col_messages": "Messages",
        "chat_col_id": "ID",
        "help_chats": "List saved chats",
        "help_save": "Save/name current chat",
        "help_load": "Load a previous chat as context",
        "help_rename": "Rename current chat",
        "help_new": "Start a new chat (clear context)",
        "help_context": "Show current context summary",
        "help_delete_chat": "Delete a saved chat",
    },
    "it": {
        "welcome": "Benvenuto in SearchMuse!",
        "goodbye": "Arrivederci!",
        "tips_title": "Suggerimenti per iniziare",
        "provider_status": "Stato provider",
        "type_query_hint": "Scrivi una query di ricerca e premi Invio. Scrivi 'help' per i comandi, 'exit' per uscire.",

        "help_title": "SearchMuse Modalita Interattiva",
        "help_commands": "Comandi:",
        "help_query": "Esegui una query di ricerca",
        "help_models": "Elenca i modelli Ollama installati",
        "help_use_model": "Cambia modello per questa sessione",
        "help_lang": "Cambia lingua interfaccia",
        "help_help": "Mostra questo messaggio di aiuto",
        "help_exit": "Esci dalla sessione interattiva",
        "help_options": "Opzioni:",
        "help_provider_flag": "dopo la query per cambiare provider",
        "help_iterations_flag": "dopo la query per limitare le iterazioni",
        "help_examples": "Esempi:",
        "help_ctrl_c": "per annullare una ricerca in corso.",
        "help_ctrl_d": "per uscire.",

        "search_started": "Sessione di ricerca avviata",
        "generating_strategy": "Generazione strategia di ricerca",
        "scraping_pages": "{count} pagine scaricate",
        "extracting_content": "Estrazione contenuto",
        "assessing_contents": "Valutazione di {count} contenuti",
        "synthesizing": "Sintesi della risposta finale",
        "search_complete": "Ricerca completata in {duration}s",
        "search_interrupted": "Ricerca interrotta.",

        "ollama_unreachable": "Impossibile raggiungere Ollama su {url}",
        "ollama_start_hint": "Assicurati che Ollama sia in esecuzione: ollama serve",
        "no_models_installed": "Nessun modello installato.",
        "pull_hint": "Scaricane uno con: searchmuse ollama pull <modello>",
        "pulling_model": "Download del modello {model} dal registro Ollama...",
        "pull_success": "Modello {model} scaricato con successo!",
        "pull_failed": "Download fallito: {error}",
        "model_available": "Il modello {model} e disponibile.",
        "model_not_installed": "Il modello {model} non e installato.",
        "model_pull_first": "Scaricalo prima: searchmuse ollama pull {model}",
        "model_env_hint": "Per usarlo, imposta la variabile d'ambiente:",
        "model_config_hint": "Oppure aggiungi al config YAML:",
        "switched_model": "Modello cambiato a {model} per questa sessione.",
        "switched_lang": "Lingua interfaccia cambiata a {lang}.",

        "validation_error": "Errore di Validazione",
        "auth_error": "Errore di Autenticazione LLM",
        "connection_error": "Errore di Connessione LLM",
        "config_error": "Errore di Configurazione",
        "search_error": "Errore di Ricerca",
        "check_api_key": "Controlla la tua API key: searchmuse config set-key <provider> <key>",
        "ensure_service": "Assicurati che il servizio LLM sia disponibile.",

        "checking_services": "Verifica servizi (provider: {provider})...",
        "connected_to": "Connesso a {url} (modello: {model})",
        "cannot_reach": "Impossibile raggiungere {url}",
        "api_key_resolved": "API key trovata",
        "no_api_key": "Nessuna API key trovata",
        "search_backend_ok": "Backend di ricerca disponibile (nessuna autenticazione richiesta)",
        "db_path": "Percorso database: {path}",
        "key_stored": "API key per {provider!r} salvata nel keyring di sistema.",
        "key_store_failed": "Impossibile salvare l'API key per {provider!r}.",
        "keyring_unavailable": "Il pacchetto 'keyring' non e installato.",
        "no_key_found": "Nessuna API key trovata per {provider!r}.",

        "phase_initializing": "Inizializzazione",
        "phase_strategizing": "Strategia",
        "phase_scraping": "Scraping",
        "phase_extracting": "Estrazione",
        "phase_assessing": "Valutazione",
        "phase_synthesizing": "Sintesi",
        "phase_complete": "Completato",
        "phase_failed": "Fallito",

        "starting": "Avvio...",
        "error_panel_title": "Errore",
        "config_panel_title": "Configurazione",
        "keyring_error": "Errore Keyring",
        "keyring_install_hint": "Installalo con: pip install 'searchmuse[keyring]'",
        "unsupported_lang": "Lingua {lang} non supportata. Supportate: {supported}",
        "error_fetching_models": "Errore nel recupero dei modelli: {error}",
        "ollama_conn_title": "Errore di Connessione",

        # Chat memory
        "chat_saved": "Chat salvata come '{name}'.",
        "chat_loaded": "Chat '{name}' caricata ({count} messaggi).",
        "chat_renamed": "Chat rinominata a '{name}'.",
        "chat_new_started": "Nuova chat avviata.",
        "chat_list_title": "Chat Salvate",
        "chat_list_empty": "Nessuna chat salvata.",
        "chat_not_found": "Chat '{name}' non trovata.",
        "chat_context_summary": "Contesto corrente: {count} messaggi precedenti.",
        "chat_no_context": "Nessun contesto (primo messaggio della chat).",
        "chat_deleted": "Chat '{name}' eliminata.",
        "chat_auto_created": "Sessione chat creata automaticamente.",
        "chat_col_name": "Nome",
        "chat_col_date": "Data",
        "chat_col_messages": "Messaggi",
        "chat_col_id": "ID",
        "help_chats": "Elenca le chat salvate",
        "help_save": "Salva/nomina la chat corrente",
        "help_load": "Carica una chat precedente come contesto",
        "help_rename": "Rinomina la chat corrente",
        "help_new": "Inizia una nuova chat (pulisce contesto)",
        "help_context": "Mostra riepilogo contesto corrente",
        "help_delete_chat": "Elimina una chat salvata",
    },
    "fr": {
        "welcome": "Bienvenue dans SearchMuse !",
        "goodbye": "Au revoir !",
        "tips_title": "Conseils pour commencer",
        "provider_status": "Statut des fournisseurs",
        "type_query_hint": "Tapez une requete de recherche et appuyez sur Entree. 'help' pour les commandes, 'exit' pour quitter.",

        "help_title": "SearchMuse Mode Interactif",
        "help_commands": "Commandes :",
        "help_query": "Lancer une requete de recherche",
        "help_models": "Lister les modeles Ollama installes",
        "help_use_model": "Changer de modele pour cette session",
        "help_lang": "Changer la langue de l'interface",
        "help_help": "Afficher ce message d'aide",
        "help_exit": "Quitter la session interactive",
        "help_options": "Options :",
        "help_provider_flag": "apres votre requete pour changer de fournisseur",
        "help_iterations_flag": "apres votre requete pour limiter les iterations",
        "help_examples": "Exemples :",
        "help_ctrl_c": "pour annuler une recherche en cours.",
        "help_ctrl_d": "pour quitter.",

        "search_started": "Session de recherche demarree",
        "generating_strategy": "Generation de la strategie de recherche",
        "scraping_pages": "{count} pages telechargees",
        "extracting_content": "Extraction du contenu",
        "assessing_contents": "Evaluation de {count} contenus",
        "synthesizing": "Synthese de la reponse finale",
        "search_complete": "Recherche terminee en {duration}s",
        "search_interrupted": "Recherche interrompue.",

        "ollama_unreachable": "Impossible de joindre Ollama sur {url}",
        "ollama_start_hint": "Assurez-vous qu'Ollama est en cours d'execution : ollama serve",
        "no_models_installed": "Aucun modele installe.",
        "pull_hint": "Telechargez-en un avec : searchmuse ollama pull <modele>",
        "pulling_model": "Telechargement du modele {model} depuis le registre Ollama...",
        "pull_success": "Modele {model} telecharge avec succes !",
        "pull_failed": "Echec du telechargement : {error}",
        "model_available": "Le modele {model} est disponible.",
        "model_not_installed": "Le modele {model} n'est pas installe.",
        "model_pull_first": "Telechargez-le d'abord : searchmuse ollama pull {model}",
        "model_env_hint": "Pour l'utiliser, definissez la variable d'environnement :",
        "model_config_hint": "Ou ajoutez dans le config YAML :",
        "switched_model": "Modele change pour {model} pour cette session.",
        "switched_lang": "Langue de l'interface changee en {lang}.",

        "validation_error": "Erreur de Validation",
        "auth_error": "Erreur d'Authentification LLM",
        "connection_error": "Erreur de Connexion LLM",
        "config_error": "Erreur de Configuration",
        "search_error": "Erreur de Recherche",
        "check_api_key": "Verifiez votre cle API : searchmuse config set-key <fournisseur> <cle>",
        "ensure_service": "Assurez-vous que le service LLM est disponible.",

        "checking_services": "Verification des services (fournisseur : {provider})...",
        "connected_to": "Connecte a {url} (modele : {model})",
        "cannot_reach": "Impossible de joindre {url}",
        "api_key_resolved": "Cle API trouvee",
        "no_api_key": "Aucune cle API trouvee",
        "search_backend_ok": "Backend de recherche disponible (aucune authentification requise)",
        "db_path": "Chemin de la base de donnees : {path}",
        "key_stored": "Cle API pour {provider!r} stockee dans le keyring systeme.",
        "key_store_failed": "Impossible de stocker la cle API pour {provider!r}.",
        "keyring_unavailable": "Le package 'keyring' n'est pas installe.",
        "no_key_found": "Aucune cle API trouvee pour {provider!r}.",

        "phase_initializing": "Initialisation",
        "phase_strategizing": "Strategie",
        "phase_scraping": "Scraping",
        "phase_extracting": "Extraction",
        "phase_assessing": "Evaluation",
        "phase_synthesizing": "Synthese",
        "phase_complete": "Termine",
        "phase_failed": "Echoue",

        "starting": "Demarrage...",
        "error_panel_title": "Erreur",
        "config_panel_title": "Configuration",
        "keyring_error": "Erreur Keyring",
        "keyring_install_hint": "Installez-le avec : pip install 'searchmuse[keyring]'",
        "unsupported_lang": "Langue {lang} non supportee. Supportees : {supported}",
        "error_fetching_models": "Erreur lors de la recuperation des modeles : {error}",
        "ollama_conn_title": "Erreur de Connexion",

        # Chat memory
        "chat_saved": "Chat enregistree sous '{name}'.",
        "chat_loaded": "Chat '{name}' chargee ({count} messages).",
        "chat_renamed": "Chat renommee en '{name}'.",
        "chat_new_started": "Nouvelle chat demarree.",
        "chat_list_title": "Chats Enregistrees",
        "chat_list_empty": "Aucune chat enregistree.",
        "chat_not_found": "Chat '{name}' introuvable.",
        "chat_context_summary": "Contexte actuel : {count} messages precedents.",
        "chat_no_context": "Pas de contexte (premier message de la chat).",
        "chat_deleted": "Chat '{name}' supprimee.",
        "chat_auto_created": "Session de chat creee automatiquement.",
        "chat_col_name": "Nom",
        "chat_col_date": "Date",
        "chat_col_messages": "Messages",
        "chat_col_id": "ID",
        "help_chats": "Lister les chats enregistrees",
        "help_save": "Enregistrer/nommer la chat actuelle",
        "help_load": "Charger une chat precedente comme contexte",
        "help_rename": "Renommer la chat actuelle",
        "help_new": "Demarrer une nouvelle chat (vider le contexte)",
        "help_context": "Afficher le resume du contexte actuel",
        "help_delete_chat": "Supprimer une chat enregistree",
    },
    "de": {
        "welcome": "Willkommen bei SearchMuse!",
        "goodbye": "Auf Wiedersehen!",
        "tips_title": "Tipps zum Einstieg",
        "provider_status": "Anbieterstatus",
        "type_query_hint": "Geben Sie eine Suchanfrage ein und druecken Sie Enter. 'help' fuer Befehle, 'exit' zum Beenden.",

        "help_title": "SearchMuse Interaktiver Modus",
        "help_commands": "Befehle:",
        "help_query": "Eine Suchanfrage ausfuehren",
        "help_models": "Installierte Ollama-Modelle auflisten",
        "help_use_model": "Modell fuer diese Sitzung wechseln",
        "help_lang": "UI-Sprache wechseln",
        "help_help": "Diese Hilfemeldung anzeigen",
        "help_exit": "Interaktive Sitzung verlassen",

        "search_started": "Suchsitzung gestartet",
        "generating_strategy": "Suchstrategie wird generiert",
        "synthesizing": "Endgueltige Antwort wird synthetisiert",
        "search_complete": "Suche abgeschlossen in {duration}s",
        "search_interrupted": "Suche unterbrochen.",

        "ollama_unreachable": "Ollama unter {url} nicht erreichbar",
        "switched_model": "Modell auf {model} fuer diese Sitzung gewechselt.",
        "switched_lang": "UI-Sprache auf {lang} gewechselt.",

        "phase_initializing": "Initialisierung",
        "phase_strategizing": "Strategieplanung",
        "phase_scraping": "Scraping",
        "phase_extracting": "Extraktion",
        "phase_assessing": "Bewertung",
        "phase_synthesizing": "Synthese",
        "phase_complete": "Abgeschlossen",
        "phase_failed": "Fehlgeschlagen",

        "starting": "Starten...",
        "error_panel_title": "Fehler",
        "config_panel_title": "Konfiguration",
    },
    "es": {
        "welcome": "Bienvenido a SearchMuse!",
        "goodbye": "Adios!",
        "tips_title": "Consejos para empezar",
        "provider_status": "Estado de proveedores",
        "type_query_hint": "Escribe una consulta de busqueda y pulsa Enter. 'help' para comandos, 'exit' para salir.",

        "help_title": "SearchMuse Modo Interactivo",
        "help_commands": "Comandos:",
        "help_query": "Ejecutar una consulta de busqueda",
        "help_models": "Listar modelos Ollama instalados",
        "help_use_model": "Cambiar modelo para esta sesion",
        "help_lang": "Cambiar idioma de la interfaz",
        "help_help": "Mostrar este mensaje de ayuda",
        "help_exit": "Salir de la sesion interactiva",

        "search_started": "Sesion de busqueda iniciada",
        "generating_strategy": "Generando estrategia de busqueda",
        "synthesizing": "Sintetizando respuesta final",
        "search_complete": "Busqueda completada en {duration}s",
        "search_interrupted": "Busqueda interrumpida.",

        "ollama_unreachable": "No se puede conectar a Ollama en {url}",
        "switched_model": "Modelo cambiado a {model} para esta sesion.",
        "switched_lang": "Idioma de interfaz cambiado a {lang}.",

        "phase_initializing": "Inicializacion",
        "phase_strategizing": "Estrategia",
        "phase_scraping": "Scraping",
        "phase_extracting": "Extraccion",
        "phase_assessing": "Evaluacion",
        "phase_synthesizing": "Sintesis",
        "phase_complete": "Completado",
        "phase_failed": "Fallido",

        "starting": "Iniciando...",
        "error_panel_title": "Error",
        "config_panel_title": "Configuracion",
    },
}

SUPPORTED_LANGUAGES: frozenset[str] = frozenset(_CATALOG)

_current_language: str = "en"


def set_language(lang: str) -> None:
    """Set the current UI language globally.

    Falls back to English if the language is not supported.

    Args:
        lang: BCP-47 language code (e.g. ``"it"``, ``"en"``, ``"fr"``).
    """
    global _current_language
    _current_language = lang if lang in _CATALOG else "en"


def get_language() -> str:
    """Return the current UI language code."""
    return _current_language


def t(key: str, **kwargs: object) -> str:
    """Translate a message key using the current language.

    Falls back to English if the key is missing in the current locale.
    Returns the key itself if not found in any locale.

    Args:
        key: The message key to look up.
        **kwargs: Format parameters for string interpolation.

    Returns:
        The translated and formatted string.
    """
    catalog = _CATALOG.get(_current_language, _CATALOG["en"])
    message = catalog.get(key, _CATALOG["en"].get(key, key))
    if kwargs:
        try:
            return message.format(**kwargs)
        except (KeyError, IndexError):
            return message
    return message


def get_translator(lang: str | None = None) -> type[_Translator]:
    """Return a translator bound to a specific language.

    Args:
        lang: Language code. Uses current language if None.

    Returns:
        A callable translator object.
    """
    effective = lang if lang is not None else _current_language

    class _BoundTranslator(_Translator):
        _lang = effective

    return _BoundTranslator


class _Translator:
    """Callable translator bound to a specific language."""

    _lang: str = "en"

    @classmethod
    def __call__(cls, key: str, **kwargs: object) -> str:
        catalog = _CATALOG.get(cls._lang, _CATALOG["en"])
        message = catalog.get(key, _CATALOG["en"].get(key, key))
        if kwargs:
            try:
                return message.format(**kwargs)
            except (KeyError, IndexError):
                return message
        return message
