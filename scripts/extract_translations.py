#!/usr/bin/env python
"""Extract translations from Python and UI files."""

import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Translation patterns to find
PATTERNS = [
    # tr() function calls
    re.compile(r'\btr\s*\(\s*["\']([^"\']+)["\']\s*\)', re.MULTILINE),
    # self.tr() method calls
    re.compile(r'self\.tr\s*\(\s*["\']([^"\']+)["\']\s*\)', re.MULTILINE),
    # QCoreApplication.translate() calls
    re.compile(r'QCoreApplication\.translate\s*\(\s*["\'][^"\']+["\']\s*,\s*["\']([^"\']+)["\']\s*\)', re.MULTILINE),
]

def extract_from_python(file_path: Path) -> set[str]:
    """Extract translatable strings from a Python file."""
    strings = set()
    try:
        content = file_path.read_text(encoding='utf-8')
        for pattern in PATTERNS:
            matches = pattern.findall(content)
            strings.update(matches)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return strings

def extract_from_ui(file_path: Path) -> set[str]:
    """Extract translatable strings from a Qt UI file."""
    strings = set()
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Find all string properties
        for string_elem in root.iter('string'):
            text = string_elem.text
            if text and text.strip():
                strings.add(text.strip())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return strings

def create_ts_file(strings: set[str], output_path: Path, language: str):
    """Create or update a .ts file with the extracted strings."""
    
    # Create root element
    root = ET.Element('TS', version='2.1', language=language)
    
    # Create context
    context = ET.SubElement(root, 'context')
    name = ET.SubElement(context, 'name')
    name.text = 'pandoc_ui'
    
    # Add messages
    for string in sorted(strings):
        message = ET.SubElement(context, 'message')
        source = ET.SubElement(message, 'source')
        source.text = string
        translation = ET.SubElement(message, 'translation', type='unfinished')
        translation.text = ''
    
    # Pretty print XML
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='    ')
    
    # Remove extra blank lines
    lines = pretty_xml.split('\n')
    lines = [line for line in lines if line.strip() or not line]
    pretty_xml = '\n'.join(lines)
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(pretty_xml, encoding='utf-8')
    print(f"Created/updated {output_path}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: extract_translations.py <language_code>")
        sys.exit(1)
    
    language = sys.argv[1]
    project_root = Path(__file__).parent.parent
    pandoc_ui_dir = project_root / 'pandoc_ui'
    
    # Collect all translatable strings
    all_strings = set()
    
    # Find all Python files
    for py_file in pandoc_ui_dir.rglob('*.py'):
        if '__pycache__' not in str(py_file):
            strings = extract_from_python(py_file)
            if strings:
                print(f"Found {len(strings)} strings in {py_file.relative_to(project_root)}")
                all_strings.update(strings)
    
    # Find all UI files
    for ui_file in pandoc_ui_dir.rglob('*.ui'):
        strings = extract_from_ui(ui_file)
        if strings:
            print(f"Found {len(strings)} strings in {ui_file.relative_to(project_root)}")
            all_strings.update(strings)
    
    print(f"\nTotal unique strings: {len(all_strings)}")
    
    # Create .ts file
    ts_path = pandoc_ui_dir / 'translations' / f'pandoc_ui_{language}.ts'
    create_ts_file(all_strings, ts_path, language)

if __name__ == "__main__":
    main()