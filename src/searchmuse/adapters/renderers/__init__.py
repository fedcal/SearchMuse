"""Result renderer adapter implementations (Markdown, JSON, plain text)."""

from searchmuse.adapters.renderers.factory import create_renderer
from searchmuse.adapters.renderers.json_renderer import JsonRendererAdapter
from searchmuse.adapters.renderers.markdown_renderer import MarkdownRendererAdapter
from searchmuse.adapters.renderers.plain_renderer import PlainRendererAdapter

__all__ = [
    "JsonRendererAdapter",
    "MarkdownRendererAdapter",
    "PlainRendererAdapter",
    "create_renderer",
]
