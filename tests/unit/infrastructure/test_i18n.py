"""Tests for searchmuse.infrastructure.i18n."""

from searchmuse.infrastructure.i18n import (
    SUPPORTED_LANGUAGES,
    get_language,
    set_language,
    t,
)


def test_supported_languages_contains_expected():
    assert "en" in SUPPORTED_LANGUAGES
    assert "it" in SUPPORTED_LANGUAGES
    assert "fr" in SUPPORTED_LANGUAGES
    assert "de" in SUPPORTED_LANGUAGES
    assert "es" in SUPPORTED_LANGUAGES


def test_set_and_get_language():
    set_language("it")
    assert get_language() == "it"
    set_language("en")
    assert get_language() == "en"


def test_set_unsupported_language_falls_back_to_en():
    set_language("xx")
    assert get_language() == "en"


def test_translate_en():
    set_language("en")
    assert t("welcome") == "Welcome to SearchMuse!"


def test_translate_it():
    set_language("it")
    assert t("welcome") == "Benvenuto in SearchMuse!"


def test_translate_fr():
    set_language("fr")
    assert t("welcome") == "Bienvenue dans SearchMuse !"


def test_translate_with_params():
    set_language("en")
    result = t("switched_model", model="llama3")
    assert "llama3" in result


def test_translate_missing_key_falls_back_to_en():
    set_language("de")
    # "no_models_installed" is not in DE catalog, should fall back to EN
    result = t("no_models_installed")
    assert result == "No models installed."


def test_translate_completely_unknown_key():
    set_language("en")
    result = t("this_key_does_not_exist_anywhere")
    assert result == "this_key_does_not_exist_anywhere"


def test_translate_goodbye_all_languages():
    for lang in ("en", "it", "fr", "de", "es"):
        set_language(lang)
        result = t("goodbye")
        assert len(result) > 0

    # Reset
    set_language("en")
