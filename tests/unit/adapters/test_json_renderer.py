"""Tests for searchmuse.adapters.renderers.json_renderer."""

import json

from searchmuse.adapters.renderers.json_renderer import JsonRendererAdapter


def test_format_name():
    renderer = JsonRendererAdapter()
    assert renderer.format_name == "json"


def test_render_produces_valid_json(sample_search_result):
    renderer = JsonRendererAdapter()
    output = renderer.render(sample_search_result)
    data = json.loads(output)
    assert "session_id" in data
    assert "query" in data
    assert "synthesis" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)


def test_render_contains_all_fields(sample_search_result):
    renderer = JsonRendererAdapter()
    output = renderer.render(sample_search_result)
    data = json.loads(output)
    assert data["total_sources"] == sample_search_result.total_sources_found
    assert data["iterations"] == sample_search_result.iterations_performed
    assert data["duration_seconds"] == sample_search_result.duration_seconds


def test_render_citations_structure(sample_search_result):
    renderer = JsonRendererAdapter()
    output = renderer.render(sample_search_result)
    data = json.loads(output)
    for citation in data["citations"]:
        assert "index" in citation
        assert "text" in citation
        assert "url" in citation


def test_render_empty_citations(sample_search_result):
    import dataclasses
    result = dataclasses.replace(sample_search_result, citations=())
    renderer = JsonRendererAdapter()
    output = renderer.render(result)
    data = json.loads(output)
    assert data["citations"] == []
