"""
Modern Python i18n system for pandoc-ui using gettext.

This module provides a clean, simple internationalization system using
Python's standard gettext library, replacing the complex Qt translation system.

Usage:
    from pandoc_ui.i18n import _, ngettext, setup_translation
    
    # Setup translation for a language
    setup_translation('ja_JP')
    
    # Translate strings
    title = _("Document Converter")
    message = ngettext("1 file", "{n} files", count).format(n=count)
"""

import gettext
import logging
import os
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

# Global translator instance
_current_translator: Optional[gettext.GNUTranslations] = None
_current_language: str = "en"

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh_CN": "简体中文", 
    "ja_JP": "日本語",
    "ko_KR": "한국어",
    "fr_FR": "Français",
    "de_DE": "Deutsch", 
    "es_ES": "Español",
    "zh_TW": "繁體中文"
}

def get_locales_dir() -> Path:
    """Get the locales directory path."""
    return Path(__file__).parent.parent / "locales"

def setup_translation(language: str = "en") -> bool:
    """
    Setup translation for the given language.
    
    Args:
        language: Language code (e.g., 'ja_JP', 'zh_CN')
        
    Returns:
        True if translation was loaded successfully, False otherwise
    """
    global _current_translator, _current_language
    
    if language == "en":
        # English is the default, no translation needed
        _current_translator = gettext.NullTranslations()
        _current_language = language
        logger.info("Using default English locale")
        return True
    
    if language not in SUPPORTED_LANGUAGES:
        logger.warning(f"Unsupported language: {language}, falling back to English")
        return setup_translation("en")
    
    locales_dir = get_locales_dir()
    
    try:
        # Try to load the translation
        translator = gettext.translation(
            domain="pandoc_ui",
            localedir=locales_dir,
            languages=[language],
            fallback=False
        )
        
        _current_translator = translator
        _current_language = language
        
        logger.info(f"Successfully loaded translation for {language}")
        return True
        
    except FileNotFoundError:
        logger.warning(f"Translation file not found for {language}, falling back to English")
        return setup_translation("en")
    except Exception as e:
        logger.error(f"Failed to load translation for {language}: {e}")
        return setup_translation("en")

def _(text: str) -> str:
    """
    Translate a string using the current language.
    
    Args:
        text: Text to translate
        
    Returns:
        Translated text, or original text if no translation available
    """
    if _current_translator is None:
        setup_translation()
    
    try:
        return _current_translator.gettext(text)
    except Exception as e:
        logger.debug(f"Translation failed for '{text}': {e}")
        return text

def ngettext(singular: str, plural: str, n: int) -> str:
    """
    Translate a string with plural forms.
    
    Args:
        singular: Singular form
        plural: Plural form  
        n: Number to determine which form to use
        
    Returns:
        Translated text with appropriate plural form
    """
    if _current_translator is None:
        setup_translation()
    
    try:
        return _current_translator.ngettext(singular, plural, n)
    except Exception as e:
        logger.debug(f"Plural translation failed for '{singular}'/'{plural}': {e}")
        return singular if n == 1 else plural

def get_current_language() -> str:
    """Get the currently active language code."""
    return _current_language

def get_language_name(language: str = None) -> str:
    """
    Get the display name for a language.
    
    Args:
        language: Language code, or None for current language
        
    Returns:
        Human-readable language name
    """
    if language is None:
        language = _current_language
    
    return SUPPORTED_LANGUAGES.get(language, language)

def list_available_languages() -> dict:
    """
    List all languages that have translation files available.
    
    Returns:
        Dict mapping language codes to display names
    """
    available = {"en": "English"}  # English is always available
    
    locales_dir = get_locales_dir()
    if not locales_dir.exists():
        return available
    
    for lang_code in SUPPORTED_LANGUAGES:
        if lang_code == "en":
            continue
            
        mo_file = locales_dir / lang_code / "LC_MESSAGES" / "pandoc_ui.mo"
        if mo_file.exists():
            available[lang_code] = SUPPORTED_LANGUAGES[lang_code]
    
    return available

# Initialize with English by default
setup_translation("en")