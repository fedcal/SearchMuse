"""LLM adapter implementations (Ollama, Claude, OpenAI, Gemini)."""

from searchmuse.adapters.llm._factory import create_llm_adapter
from searchmuse.adapters.llm.ollama_adapter import OllamaLLMAdapter

__all__ = ["OllamaLLMAdapter", "create_llm_adapter"]
