"""Tests for searchmuse.adapters.renderers.plain_renderer."""

import dataclasses

from searchmuse.adapters.renderers.plain_renderer import PlainRendererAdapter


def test_format_name():
    renderer = PlainRendererAdapter()
    assert renderer.format_name == "plain"


def test_render_contains_answer(sample_search_result):
    renderer = PlainRendererAdapter()
    output = renderer.render(sample_search_result)
    assert "ANSWER" in output
    assert sample_search_result.synthesis in output


def test_render_contains_sources(sample_search_result):
    renderer = PlainRendererAdapter()
    output = renderer.render(sample_search_result)
    assert "SOURCES" in output
    for citation in sample_search_result.citations:
        assert citation.url in output


def test_render_contains_footer(sample_search_result):
    renderer = PlainRendererAdapter()
    output = renderer.render(sample_search_result)
    assert "Duration" in output


def test_render_empty_citations(sample_search_result):
    result = dataclasses.replace(sample_search_result, citations=())
    renderer = PlainRendererAdapter()
    output = renderer.render(result)
    assert "No sources were cited" in output
