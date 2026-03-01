"""Tests for searchmuse.cli.container."""

import os

import pytest

from searchmuse.cli.container import Container, build_container


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove SEARCHMUSE_ env vars to get clean config."""
    for key in list(os.environ):
        if key.startswith("SEARCHMUSE_"):
            monkeypatch.delenv(key)


def test_build_container_returns_container():
    container = build_container()
    assert isinstance(container, Container)


def test_container_has_orchestrator():
    container = build_container()
    assert container.orchestrator is not None


def test_container_has_renderer():
    container = build_container()
    assert hasattr(container.renderer, "render")
    assert hasattr(container.renderer, "format_name")


def test_container_config(test_config):
    container = Container(test_config)
    assert container.config is test_config


def test_container_renderer_format():
    container = build_container()
    assert container.renderer.format_name in ("markdown", "json", "plain")


@pytest.mark.asyncio
async def test_container_close():
    container = build_container()
    await container.close()
