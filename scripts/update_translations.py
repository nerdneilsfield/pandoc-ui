#!/usr/bin/env python
"""
Update Qt .ts translation files from translations.json

This script reads translations from a JSON file and updates Qt .ts files
with the translations, preserving all Qt metadata and structure.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Tuple
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TranslationUpdater:
    """Updates Qt .ts files with translations from JSON."""
    
    def __init__(self, json_path: Path, ts_dir: Path):
        """
        Initialize the updater.
        
        Args:
            json_path: Path to translations.json
            ts_dir: Directory containing .ts files
        """
        self.json_path = json_path
        self.ts_dir = ts_dir
        self.translations = {}
        
    def load_translations(self) -> bool:
        """Load translations from JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Remove metadata
            self.translations = {
                lang: trans for lang, trans in data.items() 
                if not lang.startswith('_')
            }
            
            logger.info(f"Loaded translations for {len(self.translations)} languages")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            return False
    
    def get_translation(self, lang: str, context: str, source: str) -> Optional[str]:
        """
        Get translation for a source string.
        
        Args:
            lang: Language code (e.g., 'zh_CN')
            context: Qt context name
            source: Source string to translate
            
        Returns:
            Translated string or None if not found
        """
        if lang not in self.translations:
            return None
            
        lang_trans = self.translations[lang]
        
        # Map empty context to CommandPreviewWidget for command_preview.py strings
        if context == "" or context is None:
            context = "CommandPreviewWidget"
        
        # Try context-specific translation first
        if context in lang_trans and source in lang_trans[context]:
            return lang_trans[context][source]
        
        # Fall back to global translations
        if '_global' in lang_trans and source in lang_trans['_global']:
            return lang_trans['_global'][source]
            
        return None
    
    def clean_duplicate_entries(self, root, lang: str) -> int:
        """
        Clean duplicate message entries with same source text.
        Remove entries with obsolete line references or incorrect translations.
        
        Args:
            root: XML root element
            lang: Language code to validate translations
        
        Returns:
            Number of entries removed
        """
        removed_count = 0
        
        for context_elem in root.findall('context'):
            messages = context_elem.findall('message')
            source_to_messages = {}
            
            # Group messages by source text
            for msg in messages:
                source_elem = msg.find('source')
                if source_elem is not None and source_elem.text:
                    source_text = source_elem.text
                    if source_text not in source_to_messages:
                        source_to_messages[source_text] = []
                    source_to_messages[source_text].append(msg)
            
            # Remove duplicates and incorrect translations
            for source_text, msg_list in source_to_messages.items():
                # Filter out messages with incorrect translations (Chinese in non-Chinese files)
                if not lang.startswith('zh_'):
                    filtered_msgs = []
                    for msg in msg_list:
                        trans_elem = msg.find('translation')
                        if trans_elem is not None and trans_elem.text:
                            # Check if translation contains Chinese characters
                            if self._contains_chinese(trans_elem.text):
                                context_elem.remove(msg)
                                removed_count += 1
                                logger.debug(f"Removed incorrect Chinese translation for: {source_text}")
                                continue
                        filtered_msgs.append(msg)
                    msg_list = filtered_msgs
                
                # Remove duplicates, keeping the best one
                if len(msg_list) > 1:
                    # Sort by preference: finished translations first, then by location relevance
                    def msg_priority(msg):
                        trans_elem = msg.find('translation')
                        if trans_elem is not None:
                            # Finished translation has highest priority
                            if 'type' not in trans_elem.attrib:
                                return 0
                            # Unfinished is lower priority
                            elif trans_elem.attrib['type'] == 'unfinished':
                                return 1
                        return 2
                    
                    msg_list.sort(key=msg_priority)
                    best_msg = msg_list[0]
                    
                    # Remove duplicates
                    for msg in msg_list[1:]:
                        context_elem.remove(msg)
                        removed_count += 1
                        logger.debug(f"Removed duplicate entry for: {source_text}")
        
        return removed_count
    
    def _contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters."""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False

    def update_ts_file(self, ts_path: Path) -> Tuple[int, int]:
        """
        Update a single .ts file with translations.
        
        Args:
            ts_path: Path to .ts file
            
        Returns:
            Tuple of (updated_count, total_count)
        """
        # Extract language code from filename
        # Expected format: pandoc_ui_zh_CN.ts
        lang = ts_path.stem.split('_', 2)[2]  # Get 'zh_CN' from 'pandoc_ui_zh_CN'
        
        if lang not in self.translations:
            logger.warning(f"No translations found for language: {lang}")
            return 0, 0
        
        # Register namespace to handle Qt's TS format
        ET.register_namespace('', 'http://www.w3.org/XML/1998/namespace')
        
        # Parse the .ts file
        try:
            tree = ET.parse(ts_path)
            root = tree.getroot()
        except Exception as e:
            logger.error(f"Failed to parse {ts_path}: {e}")
            return 0, 0
        
        # Clean duplicate entries and incorrect translations first
        removed_count = self.clean_duplicate_entries(root, lang)
        if removed_count > 0:
            logger.info(f"Cleaned {removed_count} duplicate/incorrect entries from {ts_path.name}")
        
        updated_count = 0
        total_count = 0
        
        # Process each context
        for context_elem in root.findall('context'):
            context_name_elem = context_elem.find('name')
            if context_name_elem is None:
                continue
                
            context_name = context_name_elem.text or ""
            
            # Process each message in the context
            for message_elem in context_elem.findall('message'):
                source_elem = message_elem.find('source')
                if source_elem is None or source_elem.text is None:
                    continue
                
                source_text = source_elem.text
                total_count += 1
                
                # Get translation from JSON
                translation_text = self.get_translation(lang, context_name, source_text)
                
                # Debug missing translations with context mapping info
                if not translation_text:
                    mapped_context = "CommandPreviewWidget" if context_name == "" else context_name
                    logger.debug(f"No translation found for {lang}.{mapped_context}.{source_text} (original context: '{context_name}')")
                
                if translation_text:
                    translation_elem = message_elem.find('translation')
                    if translation_elem is not None:
                        # Update translation
                        translation_elem.text = translation_text
                        
                        # Remove 'type' attribute if it's unfinished/vanished/obsolete
                        if 'type' in translation_elem.attrib:
                            if translation_elem.attrib['type'] in ['unfinished', 'vanished', 'obsolete']:
                                del translation_elem.attrib['type']
                        
                        updated_count += 1
                        logger.debug(f"Updated: {context_name}.{source_text} -> {translation_text}")
                    else:
                        # Create translation element if it doesn't exist
                        translation_elem = ET.SubElement(message_elem, 'translation')
                        translation_elem.text = translation_text
                        updated_count += 1
                        logger.debug(f"Added: {context_name}.{source_text} -> {translation_text}")
        
        # Write back the updated XML
        try:
            # Pretty print with proper indentation
            self._indent_xml(root)
            tree.write(ts_path, encoding='utf-8', xml_declaration=True)
            logger.info(f"Updated {ts_path.name}: {updated_count}/{total_count} translations")
        except Exception as e:
            logger.error(f"Failed to write {ts_path}: {e}")
            return 0, total_count
            
        return updated_count, total_count
    
    def _indent_xml(self, elem, level=0):
        """Add pretty-printing indentation to XML."""
        indent = "\n" + level * "    "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "    "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def validate_translations(self) -> None:
        """Validate and report translation coverage."""
        logger.info("📊 Translation Coverage Report:")
        logger.info("=" * 50)
        
        for lang, translations in self.translations.items():
            total_strings = 0
            contexts = []
            
            for context, strings in translations.items():
                if context.startswith('_'):
                    continue
                contexts.append(context)
                total_strings += len(strings)
            
            logger.info(f"🌍 {lang}: {total_strings} strings in {len(contexts)} contexts")
            for context in sorted(contexts):
                count = len(translations[context])
                logger.info(f"  - {context}: {count} strings")
        
        logger.info("=" * 50)

    def update_all_ts_files(self) -> None:
        """Update all .ts files in the directory with enhanced cleaning and validation."""
        ts_files = list(self.ts_dir.glob("pandoc_ui_*.ts"))
        
        if not ts_files:
            logger.error(f"No .ts files found in {self.ts_dir}")
            return
        
        # Show translation coverage first
        self.validate_translations()
        
        logger.info(f"🔄 Found {len(ts_files)} .ts files to update")
        
        total_updated = 0
        total_messages = 0
        total_cleaned = 0
        
        for ts_file in ts_files:
            updated, total = self.update_ts_file(ts_file)
            total_updated += updated
            total_messages += total
        
        logger.info("")
        logger.info("📋 Final Summary:")
        logger.info(f"✅ Updated {total_updated}/{total_messages} translations across all files")
        logger.info(f"🧹 Total duplicate entries cleaned: {total_cleaned}")
        
        if total_updated == total_messages:
            logger.info("🎉 All translations are complete!")
        else:
            missing = total_messages - total_updated
            logger.info(f"⚠️  {missing} translations still missing")
        
        logger.info("")
        logger.info("🔨 Next steps:")
        logger.info("1. Run 'lrelease' to compile .ts files to .qm format")
        logger.info("2. Test the application with updated translations")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update Qt .ts files with translations from JSON"
    )
    parser.add_argument(
        '--json',
        type=Path,
        help='Path to translations.json (default: pandoc_ui/translations/translations.json)'
    )
    parser.add_argument(
        '--ts-dir',
        type=Path,
        help='Directory containing .ts files (default: pandoc_ui/translations/)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    json_path = args.json or project_root / 'pandoc_ui' / 'translations' / 'translations.json'
    ts_dir = args.ts_dir or project_root / 'pandoc_ui' / 'translations'
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate paths
    if not json_path.exists():
        logger.error(f"translations.json not found at: {json_path}")
        sys.exit(1)
    
    if not ts_dir.exists():
        logger.error(f"Translation directory not found: {ts_dir}")
        sys.exit(1)
    
    # Run the updater
    updater = TranslationUpdater(json_path, ts_dir)
    
    if not updater.load_translations():
        sys.exit(1)
    
    updater.update_all_ts_files()
    
    logger.info("\n✅ Translation update complete!")
    logger.info("Run 'lrelease' to compile the updated .ts files to .qm format")


if __name__ == "__main__":
    main()