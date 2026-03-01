"""Tests for searchmuse.cli.display."""

from searchmuse.application.progress import ProgressEvent
from searchmuse.cli.display import Display
from searchmuse.domain.enums import SearchPhase


def test_display_quiet_suppresses_banner(test_config):
    display = Display(quiet=True)
    # Should not raise
    display.show_banner(test_config)


def test_display_show_banner_no_config():
    display = Display(quiet=False)
    # Should not raise even with None config
    display.show_banner(None)


def test_display_show_banner_with_config(test_config):
    display = Display(quiet=False)
    display.show_banner(test_config)


def test_display_start_stop_progress():
    display = Display(quiet=False)
    display.start_progress()
    display.stop_progress()
    # Double stop is safe
    display.stop_progress()


def test_display_update_progress_quiet():
    display = Display(quiet=True)
    event = ProgressEvent(
        phase=SearchPhase.SCRAPING,
        message="test",
        iteration=1,
        detail="detail",
    )
    display.update_progress(event)


def test_display_update_progress_with_status():
    display = Display(quiet=False)
    display.start_progress()
    event = ProgressEvent(
        phase=SearchPhase.SYNTHESIZING,
        message="Synthesizing",
        iteration=1,
        detail="",
    )
    display.update_progress(event)
    display.stop_progress()


def test_display_show_error():
    display = Display()
    display.show_error("Test Error", "Something went wrong")


def test_display_show_info():
    display = Display()
    display.show_info("An info message")


def test_display_show_info_quiet():
    display = Display(quiet=True)
    display.show_info("Should be suppressed")


def test_display_make_progress_callback():
    display = Display()
    callback = display.make_progress_callback()
    assert callable(callback)


def test_display_show_result(sample_search_result):
    display = Display()
    display.show_result(sample_search_result, "# Test markdown")


def test_display_show_result_raw():
    display = Display()
    display.show_result_raw("Plain text output")
