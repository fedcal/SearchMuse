"""Renderer factory for creating format-specific renderer adapters.

Maps format names to their corresponding adapter classes. All adapters
implement the ResultRendererPort protocol.
"""

from __future__ import annotations

from searchmuse.adapters.renderers.json_renderer import JsonRendererAdapter
from searchmuse.adapters.renderers.markdown_renderer import MarkdownRendererAdapter
from searchmuse.adapters.renderers.plain_renderer import PlainRendererAdapter

_RENDERERS: dict[str, type[MarkdownRendererAdapter | JsonRendererAdapter | PlainRendererAdapter]] = {
    "markdown": MarkdownRendererAdapter,
    "json": JsonRendererAdapter,
    "plain": PlainRendererAdapter,
}


def create_renderer(
    format_name: str = "markdown",
) -> MarkdownRendererAdapter | JsonRendererAdapter | PlainRendererAdapter:
    """Create a renderer adapter for the given output format.

    Args:
        format_name: One of ``"markdown"``, ``"json"``, or ``"plain"``.
            Defaults to ``"markdown"`` if not specified.

    Returns:
        An adapter implementing the ResultRendererPort protocol.

    Raises:
        ValueError: When the format name is not recognised.
    """
    renderer_cls = _RENDERERS.get(format_name)
    if renderer_cls is None:
        supported = ", ".join(sorted(_RENDERERS))
        raise ValueError(
            f"Unknown output format {format_name!r}. Supported: {supported}"
        )
    return renderer_cls()
