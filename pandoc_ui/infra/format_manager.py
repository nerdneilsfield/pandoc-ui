"""
Format compatibility manager based on official pandoc format support diagram.
"""

from enum import Enum
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


class FormatDirection(Enum):
    """Format conversion direction capabilities."""
    INPUT_ONLY = "input_only"      # ← 
    OUTPUT_ONLY = "output_only"    # →
    BIDIRECTIONAL = "bidirectional"  # ↔


@dataclass
class FormatInfo:
    """Information about a pandoc format."""
    name: str
    category: str
    direction: FormatDirection
    extensions: List[str]
    display_name: str


class FormatManager:
    """Manages pandoc format compatibility and categorization."""
    
    def __init__(self):
        self.formats = self._initialize_formats()
        self.categories = self._get_categories()
    
    def _initialize_formats(self) -> Dict[str, FormatInfo]:
        """Initialize format information based on official pandoc diagram."""
        formats = {}
        
        # Lightweight markup formats
        formats.update({
            'markdown': FormatInfo('markdown', 'Lightweight markup', FormatDirection.BIDIRECTIONAL, 
                                 ['.md', '.markdown'], 'Markdown'),
            'commonmark': FormatInfo('commonmark', 'Lightweight markup', FormatDirection.BIDIRECTIONAL,
                                   ['.md', '.markdown'], 'CommonMark'),
            'gfm': FormatInfo('gfm', 'Lightweight markup', FormatDirection.BIDIRECTIONAL,
                            ['.md', '.markdown'], 'GitHub-flavored Markdown'),
            'rst': FormatInfo('rst', 'Lightweight markup', FormatDirection.BIDIRECTIONAL,
                            ['.rst'], 'reStructuredText'),
            'asciidoc': FormatInfo('asciidoc', 'Lightweight markup', FormatDirection.BIDIRECTIONAL,
                                 ['.adoc', '.asciidoc'], 'AsciiDoc'),
            'org': FormatInfo('org', 'Lightweight markup', FormatDirection.BIDIRECTIONAL,
                            ['.org'], 'Emacs Org-Mode'),
            'muse': FormatInfo('muse', 'Lightweight markup', FormatDirection.BIDIRECTIONAL,
                             ['.muse'], 'Emacs Muse'),
            'textile': FormatInfo('textile', 'Lightweight markup', FormatDirection.BIDIRECTIONAL,
                                ['.textile'], 'Textile'),
            'markua': FormatInfo('markua', 'Lightweight markup', FormatDirection.OUTPUT_ONLY,
                               ['.markua'], 'Markua'),
            't2t': FormatInfo('t2t', 'Lightweight markup', FormatDirection.INPUT_ONLY,
                            ['.t2t'], 'txt2tags'),
        })
        
        # Word processor formats
        formats.update({
            'docx': FormatInfo('docx', 'Word processor', FormatDirection.BIDIRECTIONAL,
                             ['.docx'], 'Microsoft Word'),
            'rtf': FormatInfo('rtf', 'Word processor', FormatDirection.BIDIRECTIONAL,
                            ['.rtf'], 'Rich Text Format'),
            'odt': FormatInfo('odt', 'Word processor', FormatDirection.BIDIRECTIONAL,
                            ['.odt'], 'OpenOffice/LibreOffice'),
        })
        
        # Interactive notebook formats
        formats.update({
            'ipynb': FormatInfo('ipynb', 'Interactive notebook', FormatDirection.BIDIRECTIONAL,
                              ['.ipynb'], 'Jupyter notebook'),
        })
        
        # Page layout formats
        formats.update({
            'icml': FormatInfo('icml', 'Page layout', FormatDirection.OUTPUT_ONLY,
                             ['.icml'], 'InDesign ICML'),
            'typst': FormatInfo('typst', 'Page layout', FormatDirection.BIDIRECTIONAL,
                              ['.typ'], 'Typst'),
        })
        
        # HTML formats
        formats.update({
            'html': FormatInfo('html', 'HTML', FormatDirection.BIDIRECTIONAL,
                             ['.html', '.htm'], 'HTML'),
            'html4': FormatInfo('html4', 'HTML', FormatDirection.BIDIRECTIONAL,
                              ['.html', '.htm'], 'HTML 4'),
            'html5': FormatInfo('html5', 'HTML', FormatDirection.BIDIRECTIONAL,
                              ['.html', '.htm'], 'HTML 5'),
            'chunkedhtml': FormatInfo('chunkedhtml', 'HTML', FormatDirection.OUTPUT_ONLY,
                                    ['.html'], 'Chunked HTML'),
        })
        
        # Ebooks
        formats.update({
            'epub': FormatInfo('epub', 'Ebooks', FormatDirection.BIDIRECTIONAL,
                             ['.epub'], 'EPUB'),
            'epub2': FormatInfo('epub2', 'Ebooks', FormatDirection.BIDIRECTIONAL,
                              ['.epub'], 'EPUB version 2'),
            'epub3': FormatInfo('epub3', 'Ebooks', FormatDirection.BIDIRECTIONAL,
                              ['.epub'], 'EPUB version 3'),
            'fb2': FormatInfo('fb2', 'Ebooks', FormatDirection.BIDIRECTIONAL,
                            ['.fb2'], 'FictionBook2'),
        })
        
        # Documentation formats
        formats.update({
            'texinfo': FormatInfo('texinfo', 'Documentation', FormatDirection.OUTPUT_ONLY,
                                ['.texi', '.texinfo'], 'GNU TexInfo'),
            'man': FormatInfo('man', 'Documentation', FormatDirection.BIDIRECTIONAL,
                            ['.1', '.man'], 'roff man'),
            'haddock': FormatInfo('haddock', 'Documentation', FormatDirection.BIDIRECTIONAL,
                                ['.hs'], 'Haddock markup'),
        })
        
        # Wiki markup formats  
        formats.update({
            'mediawiki': FormatInfo('mediawiki', 'Wiki markup', FormatDirection.BIDIRECTIONAL,
                                  ['.wiki'], 'MediaWiki markup'),
            'dokuwiki': FormatInfo('dokuwiki', 'Wiki markup', FormatDirection.BIDIRECTIONAL,
                                 ['.wiki'], 'DokuWiki markup'),
            'tikiwiki': FormatInfo('tikiwiki', 'Wiki markup', FormatDirection.INPUT_ONLY,
                                 ['.wiki'], 'TikiWiki markup'),
            'twiki': FormatInfo('twiki', 'Wiki markup', FormatDirection.INPUT_ONLY,
                              ['.wiki'], 'TWiki markup'),
            'vimwiki': FormatInfo('vimwiki', 'Wiki markup', FormatDirection.INPUT_ONLY,
                                ['.wiki'], 'Vimwiki markup'),
            'xwiki': FormatInfo('xwiki', 'Wiki markup', FormatDirection.OUTPUT_ONLY,
                              ['.wiki'], 'XWiki markup'),
            'zimwiki': FormatInfo('zimwiki', 'Wiki markup', FormatDirection.OUTPUT_ONLY,
                                ['.wiki'], 'ZimWiki markup'),
            'jira': FormatInfo('jira', 'Wiki markup', FormatDirection.BIDIRECTIONAL,
                             ['.jira'], 'Jira wiki markup'),
            'creole': FormatInfo('creole', 'Wiki markup', FormatDirection.INPUT_ONLY,
                               ['.creole'], 'Creole'),
        })
        
        # Slide show formats
        formats.update({
            'beamer': FormatInfo('beamer', 'Slide show', FormatDirection.OUTPUT_ONLY,
                               ['.tex'], 'LaTeX Beamer'),
            'pptx': FormatInfo('pptx', 'Slide show', FormatDirection.OUTPUT_ONLY,
                             ['.pptx'], 'Microsoft PowerPoint'),
            'slidy': FormatInfo('slidy', 'Slide show', FormatDirection.OUTPUT_ONLY,
                              ['.html'], 'Slidy'),
            'revealjs': FormatInfo('revealjs', 'Slide show', FormatDirection.OUTPUT_ONLY,
                                 ['.html'], 'reveal.js'),
            'slideous': FormatInfo('slideous', 'Slide show', FormatDirection.OUTPUT_ONLY,
                                 ['.html'], 'Slideous'),
            's5': FormatInfo('s5', 'Slide show', FormatDirection.OUTPUT_ONLY,
                           ['.html'], 'S5'),
            'dzslides': FormatInfo('dzslides', 'Slide show', FormatDirection.OUTPUT_ONLY,
                                 ['.html'], 'DZSlides'),
        })
        
        # Data formats
        formats.update({
            'csv': FormatInfo('csv', 'Data', FormatDirection.INPUT_ONLY,
                            ['.csv'], 'CSV tables'),
            'tsv': FormatInfo('tsv', 'Data', FormatDirection.INPUT_ONLY,
                            ['.tsv'], 'TSV tables'),
        })
        
        # Terminal output
        formats.update({
            'plain': FormatInfo('plain', 'Terminal output', FormatDirection.OUTPUT_ONLY,
                              ['.txt'], 'ANSI-formatted text'),
        })
        
        # TeX formats
        formats.update({
            'latex': FormatInfo('latex', 'TeX', FormatDirection.BIDIRECTIONAL,
                              ['.tex', '.latex'], 'LaTeX'),
            'context': FormatInfo('context', 'TeX', FormatDirection.OUTPUT_ONLY,
                                ['.tex'], 'ConTeXt'),
        })
        
        # XML formats
        formats.update({
            'docbook': FormatInfo('docbook', 'XML', FormatDirection.BIDIRECTIONAL,
                                ['.xml'], 'DocBook'),
            'docbook4': FormatInfo('docbook4', 'XML', FormatDirection.BIDIRECTIONAL,
                                 ['.xml'], 'DocBook version 4'),
            'docbook5': FormatInfo('docbook5', 'XML', FormatDirection.BIDIRECTIONAL,
                                 ['.xml'], 'DocBook version 5'),
            'jats': FormatInfo('jats', 'XML', FormatDirection.BIDIRECTIONAL,
                             ['.xml'], 'JATS'),
            'jats_archiving': FormatInfo('jats_archiving', 'XML', FormatDirection.BIDIRECTIONAL,
                                       ['.xml'], 'JATS Archiving'),
            'jats_articleauthoring': FormatInfo('jats_articleauthoring', 'XML', FormatDirection.BIDIRECTIONAL,
                                              ['.xml'], 'JATS Article Authoring'),
            'jats_publishing': FormatInfo('jats_publishing', 'XML', FormatDirection.BIDIRECTIONAL,
                                        ['.xml'], 'JATS Publishing'),
            'tei': FormatInfo('tei', 'XML', FormatDirection.OUTPUT_ONLY,
                            ['.xml'], 'TEI Simple'),
            'opendocument': FormatInfo('opendocument', 'XML', FormatDirection.OUTPUT_ONLY,
                                     ['.xml'], 'OpenDocument XML'),
        })
        
        # Outline formats
        formats.update({
            'opml': FormatInfo('opml', 'Outline', FormatDirection.BIDIRECTIONAL,
                             ['.opml'], 'OPML'),
        })
        
        # Bibliography formats
        formats.update({
            'bibtex': FormatInfo('bibtex', 'Bibliography', FormatDirection.BIDIRECTIONAL,
                               ['.bib'], 'BibTeX'),
            'biblatex': FormatInfo('biblatex', 'Bibliography', FormatDirection.BIDIRECTIONAL,
                                 ['.bib'], 'BibLaTeX'),
            'csljson': FormatInfo('csljson', 'Bibliography', FormatDirection.BIDIRECTIONAL,
                                ['.json'], 'CSL JSON'),
            'ris': FormatInfo('ris', 'Bibliography', FormatDirection.INPUT_ONLY,
                            ['.ris'], 'RIS'),
            'endnotexml': FormatInfo('endnotexml', 'Bibliography', FormatDirection.INPUT_ONLY,
                                   ['.xml'], 'EndNote XML'),
        })
        
        # PDF - special case
        formats.update({
            'pdf': FormatInfo('pdf', 'PDF', FormatDirection.OUTPUT_ONLY,
                            ['.pdf'], 'PDF'),
        })
        
        return formats
    
    def _get_categories(self) -> List[str]:
        """Get list of format categories."""
        categories = set()
        for format_info in self.formats.values():
            categories.add(format_info.category)
        return sorted(list(categories))
    
    def get_input_formats(self) -> List[Tuple[str, str]]:
        """Get list of (format_key, display_name) for input formats."""
        input_formats = []
        for key, info in self.formats.items():
            if info.direction in [FormatDirection.INPUT_ONLY, FormatDirection.BIDIRECTIONAL]:
                input_formats.append((key, info.display_name))
        return sorted(input_formats, key=lambda x: x[1])
    
    def get_output_formats(self) -> List[Tuple[str, str]]:
        """Get list of (format_key, display_name) for output formats."""
        output_formats = []
        for key, info in self.formats.items():
            if info.direction in [FormatDirection.OUTPUT_ONLY, FormatDirection.BIDIRECTIONAL]:
                output_formats.append((key, info.display_name))
        return sorted(output_formats, key=lambda x: x[1])
    
    def get_formats_by_category(self, category: str) -> List[Tuple[str, str]]:
        """Get formats in a specific category."""
        category_formats = []
        for key, info in self.formats.items():
            if info.category == category:
                category_formats.append((key, info.display_name))
        return sorted(category_formats, key=lambda x: x[1])
    
    def can_convert(self, input_format: str, output_format: str) -> bool:
        """Check if conversion from input to output format is supported."""
        if input_format not in self.formats or output_format not in self.formats:
            return False
        
        input_info = self.formats[input_format]
        output_info = self.formats[output_format]
        
        # Input format must support input or bidirectional
        input_ok = input_info.direction in [FormatDirection.INPUT_ONLY, FormatDirection.BIDIRECTIONAL]
        # Output format must support output or bidirectional  
        output_ok = output_info.direction in [FormatDirection.OUTPUT_ONLY, FormatDirection.BIDIRECTIONAL]
        
        return input_ok and output_ok
    
    def detect_format_from_extension(self, file_path: str) -> str:
        """Detect format from file extension."""
        import os
        ext = os.path.splitext(file_path.lower())[1]
        
        for key, info in self.formats.items():
            if ext in info.extensions:
                return key
        
        # Default fallback
        if ext in ['.md', '.markdown']:
            return 'markdown'
        elif ext in ['.txt']:
            return 'plain'
        
        return 'markdown'  # Default to markdown for unknown extensions
    
    def get_file_filters(self) -> list[str]:
        """Generate comprehensive file filters for QFileDialog."""
        # Group extensions by category and format
        filter_groups = {}
        
        for key, info in self.formats.items():
            # Only include input-capable formats
            if info.direction in [FormatDirection.INPUT_ONLY, FormatDirection.BIDIRECTIONAL]:
                category = info.category
                if category not in filter_groups:
                    filter_groups[category] = []
                
                # Create filter string for this format
                if info.extensions:
                    ext_pattern = ' '.join(f'*{ext}' for ext in info.extensions)
                    filter_str = f"{info.display_name} ({ext_pattern})"
                    filter_groups[category].append(filter_str)
        
        # Build final filter list
        filters = []
        
        # Add most common formats first
        common_formats = [
            "Markdown files (*.md *.markdown)",
            "Text files (*.txt)",
            "HTML files (*.html *.htm)",
            "Word documents (*.docx)",
            "EPUB files (*.epub)",
            "PDF files (*.pdf)",
            "LaTeX files (*.tex *.latex)",
            "ReStructuredText (*.rst)",
            "Jupyter notebooks (*.ipynb)"
        ]
        
        # Add category-based filters
        category_order = [
            'Lightweight markup',
            'Word processor', 
            'HTML',
            'Ebooks',
            'TeX',
            'Wiki markup',
            'XML',
            'Bibliography',
            'Data',
            'Interactive notebook',
            'Documentation',
            'Page layout'
        ]
        
        for category in category_order:
            if category in filter_groups:
                filters.extend(filter_groups[category])
        
        # Add any remaining categories
        for category, format_filters in filter_groups.items():
            if category not in category_order:
                filters.extend(format_filters)
        
        # Add special filters
        filters.append("All supported files (*.md *.markdown *.txt *.html *.htm *.docx *.epub *.tex *.latex *.rst *.ipynb *.odt *.rtf *.org *.adoc *.textile *.wiki *.bib *.csv *.tsv *.opml *.xml *.json)")
        filters.append("All files (*.*)")
        
        return filters