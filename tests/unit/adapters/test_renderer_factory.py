"""Tests for searchmuse.adapters.renderers.factory."""

import pytest

from searchmuse.adapters.renderers.factory import create_renderer
from searchmuse.adapters.renderers.json_renderer import JsonRendererAdapter
from searchmuse.adapters.renderers.markdown_renderer import MarkdownRendererAdapter
from searchmuse.adapters.renderers.plain_renderer import PlainRendererAdapter


def test_create_markdown_renderer():
    renderer = create_renderer("markdown")
    assert isinstance(renderer, MarkdownRendererAdapter)


def test_create_json_renderer():
    renderer = create_renderer("json")
    assert isinstance(renderer, JsonRendererAdapter)


def test_create_plain_renderer():
    renderer = create_renderer("plain")
    assert isinstance(renderer, PlainRendererAdapter)


def test_create_default_is_markdown():
    renderer = create_renderer()
    assert isinstance(renderer, MarkdownRendererAdapter)


def test_create_unknown_raises():
    with pytest.raises(ValueError, match="Unknown output format"):
        create_renderer("xml")


def test_all_renderers_have_format_name():
    for fmt in ("markdown", "json", "plain"):
        renderer = create_renderer(fmt)
        assert renderer.format_name == fmt


def test_all_renderers_have_render_method():
    for fmt in ("markdown", "json", "plain"):
        renderer = create_renderer(fmt)
        assert callable(getattr(renderer, "render", None))
