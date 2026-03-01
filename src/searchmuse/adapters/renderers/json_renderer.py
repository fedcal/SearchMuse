"""JSON renderer adapter implementing ResultRendererPort.

Serialises a SearchResult into a structured JSON string suitable
for machine consumption or piping to other tools.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from searchmuse.domain.models import SearchResult


class JsonRendererAdapter:
    """Renders a SearchResult as a JSON document.

    Implements the ``ResultRendererPort`` protocol.
    """

    @property
    def format_name(self) -> str:
        return "json"

    def render(self, result: SearchResult) -> str:
        """Render a completed search result to a JSON string.

        Args:
            result: The frozen SearchResult to render.

        Returns:
            A pretty-printed JSON string.
        """
        data = {
            "session_id": result.session_id,
            "query": result.query.normalized_text,
            "synthesis": result.synthesis,
            "citations": [
                {
                    "index": c.index,
                    "text": c.formatted_text,
                    "url": c.url,
                }
                for c in result.citations
            ],
            "total_sources": result.total_sources_found,
            "iterations": result.iterations_performed,
            "duration_seconds": result.duration_seconds,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
