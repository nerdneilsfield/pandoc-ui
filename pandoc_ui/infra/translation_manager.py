"""
Translation manager for pandoc-ui multi-language support.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QCoreApplication, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages."""
    
    CHINESE = ("zh_CN", "简体中文", "Chinese (Simplified)")
    CHINESE_TW = ("zh_TW", "繁體中文", "Chinese (Traditional)")
    ENGLISH = ("en_US", "English", "English")
    JAPANESE = ("ja_JP", "日本語", "Japanese")
    SPANISH = ("es_ES", "Español", "Spanish")
    FRENCH = ("fr_FR", "Français", "French")
    GERMAN = ("de_DE", "Deutsch", "German")
    KOREAN = ("ko_KR", "한국어", "Korean")
    RUSSIAN = ("ru_RU", "Русский", "Russian")
    
    def __init__(self, code: str, native_name: str, english_name: str):
        self.code = code
        self.native_name = native_name
        self.english_name = english_name
    
    @classmethod
    def from_code(cls, code: str) -> Optional['Language']:
        """Get Language enum from language code."""
        for lang in cls:
            if lang.code == code:
                return lang
        return None
    
    @classmethod
    def get_system_language(cls) -> 'Language':
        """Get system default language, fallback to English."""
        import os
        
        logger.debug("Detecting system language...")
        
        # Method 1: Qt QLocale (most reliable in Qt apps)
        try:
            system_locale = QLocale.system()
            locale_name = system_locale.name()
            logger.debug(f"Qt locale detected: {locale_name}")
            
            # Try exact match first
            for lang in cls:
                if lang.code == locale_name:
                    logger.info(f"Exact locale match: {locale_name} -> {lang.native_name}")
                    return lang
            
            # Try language prefix match with special handling for Chinese variants
            language_prefix = locale_name.split('_')[0]
            if language_prefix == 'zh':
                # Special handling for Chinese variants
                region = locale_name.split('_')[1] if '_' in locale_name else ''
                if region.upper() in ['TW', 'HK', 'MO']:
                    # Traditional Chinese regions
                    for lang in cls:
                        if lang.code == 'zh_TW':
                            logger.info(f"Chinese Traditional match: {locale_name} -> {lang.native_name}")
                            return lang
                else:
                    # Simplified Chinese (default)
                    for lang in cls:
                        if lang.code == 'zh_CN':
                            logger.info(f"Chinese Simplified match: {locale_name} -> {lang.native_name}")
                            return lang
            else:
                # For other languages, match by prefix
                for lang in cls:
                    if lang.code.startswith(language_prefix):
                        logger.info(f"Language prefix match: {locale_name} -> {lang.native_name}")
                        return lang
        except Exception as e:
            logger.warning(f"Qt locale detection failed: {e}")
        
        # Method 2: Environment variables (for better Linux/Unix support)
        try:
            for env_var in ['LC_ALL', 'LC_MESSAGES', 'LANG', 'LANGUAGE']:
                if env_var in os.environ:
                    env_locale = os.environ[env_var]
                    if env_locale and env_locale != 'C' and env_locale != 'POSIX':
                        # Clean up locale string (remove encoding and modifiers)
                        clean_locale = env_locale.split('.')[0].split('@')[0]
                        logger.debug(f"Environment locale from {env_var}: {env_locale} -> {clean_locale}")
                        
                        # Try exact match
                        for lang in cls:
                            if lang.code == clean_locale:
                                logger.info(f"Environment exact match: {clean_locale} -> {lang.native_name}")
                                return lang
                        
                        # Try language prefix match
                        language_prefix = clean_locale.split('_')[0]
                        for lang in cls:
                            if lang.code.startswith(language_prefix):
                                logger.info(f"Environment prefix match: {clean_locale} -> {lang.native_name}")
                                return lang
                        break
        except Exception as e:
            logger.warning(f"Environment locale detection failed: {e}")
        
        # Default to English
        logger.info("No supported system language detected, defaulting to English")
        return cls.ENGLISH


class TranslationManager:
    """Manages application translations and language switching."""
    
    def __init__(self):
        """Initialize translation manager."""
        self.current_language: Language = Language.ENGLISH
        self.translator: Optional[QTranslator] = None
        self.callbacks: list = []
        
        # Detect system language and automatically load translation
        detected_language = Language.get_system_language()
        logger.info(f"System language detected: {detected_language.native_name}")
        
        # Automatically set the detected language (this will load translations)
        if detected_language != Language.ENGLISH:
            success = self.set_language(detected_language)
            if not success:
                logger.warning(f"Failed to load translation for {detected_language.native_name}, falling back to English")
                self.current_language = Language.ENGLISH
        else:
            self.current_language = Language.ENGLISH
    
    def register_callback(self, callback):
        """Register callback for language change events."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """Unregister callback for language change events."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_available_languages(self) -> list[Language]:
        """Get list of available languages."""
        return list(Language)
    
    def get_current_language(self) -> Language:
        """Get current language."""
        return self.current_language
    
    def set_language(self, language: Language) -> bool:
        """
        Set current language and load translations.
        
        Args:
            language: Target language
            
        Returns:
            True if translation loaded successfully
        """
        if language == self.current_language and self.translator:
            return True
        
        logger.info(f"Switching to language: {language.native_name} ({language.code})")
        
        # Remove old translator
        if self.translator:
            QCoreApplication.removeTranslator(self.translator)
            self.translator = None
        
        # Load new translation
        success = self._load_translation(language)
        
        if success:
            self.current_language = language
            logger.info(f"Language switched to: {language.native_name}")
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(language)
                except Exception as e:
                    logger.error(f"Error in language change callback: {e}")
        else:
            logger.warning(f"Failed to load translation for: {language.native_name}")
        
        return success
    
    def _load_translation(self, language: Language) -> bool:
        """
        Load translation file for specified language.
        
        Args:
            language: Target language
            
        Returns:
            True if translation loaded successfully
        """
        if language == Language.ENGLISH:
            # English is the source language, no translation needed
            return True
        
        # Try to load from Qt resources first
        qm_path = f":/i18n/pandoc_ui_{language.code}.qm"
        
        translator = QTranslator()
        if translator.load(qm_path):
            self.translator = translator
            QCoreApplication.installTranslator(self.translator)
            logger.debug(f"Loaded translation from Qt resources: {qm_path}")
            return True
        
        # Fallback to file system
        translations_dir = Path(__file__).parent.parent / "translations"
        qm_file = translations_dir / f"pandoc_ui_{language.code}.qm"
        
        if qm_file.exists():
            translator = QTranslator()
            if translator.load(str(qm_file)):
                self.translator = translator
                QCoreApplication.installTranslator(self.translator)
                logger.debug(f"Loaded translation from file: {qm_file}")
                return True
        
        logger.warning(f"Translation file not found for {language.code}")
        return False
    
    def tr(self, source_text: str, context: str = "TranslationManager") -> str:
        """
        Translate text using current language.
        
        Args:
            source_text: Text to translate
            context: Translation context
            
        Returns:
            Translated text or original if no translation found
        """
        return QCoreApplication.translate(context, source_text)


# Global translation manager instance
_translation_manager: Optional[TranslationManager] = None


def get_translation_manager() -> TranslationManager:
    """Get global translation manager instance."""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def tr(source_text: str, context: str = "Global") -> str:
    """
    Global translation function.
    
    Args:
        source_text: Text to translate
        context: Translation context
        
    Returns:
        Translated text
    """
    return QCoreApplication.translate(context, source_text)