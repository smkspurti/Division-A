# modules/language_manager.py
import streamlit as st
from .translations import TRANSLATIONS


def init_language():
    """Initialize language session state if not set."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"


def set_language(lang: str):
    """Set language explicitly and persist to session state.

    Falls back to English when an unknown language code is provided.
    """
    if lang in TRANSLATIONS:
        st.session_state["lang"] = lang
    else:
        st.session_state["lang"] = "en"


def toggle_language():
    """Toggle language between English and Kannada."""
    set_language("kn" if st.session_state.get("lang", "en") == "en" else "en")


def get_language() -> str:
    """Return current language code from session state."""
    return st.session_state.get("lang", "en")


def t(key: str, *args) -> str:
    """Get translated string for the given key based on current language.

    Positional args are passed to `str.format()` for dynamic formatting.
    Falls back to English or the key itself when a translation is missing.
    """
    lang = get_language()
    translation = TRANSLATIONS.get(lang, {}).get(key)
    if not translation:
        translation = TRANSLATIONS.get("en", {}).get(key, key)

    if args:
        return translation.format(*args)
    return translation
