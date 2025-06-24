"""
Data models for pandoc-ui application.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class InputFormat(Enum):
    """Supported input formats for pandoc."""

    BIBLATEX = "biblatex"
    BIBTEX = "bibtex"
    COMMONMARK = "commonmark"
    COMMONMARK_X = "commonmark_x"
    CREOLE = "creole"
    CSLJSON = "csljson"
    CSV = "csv"
    DOCBOOK = "docbook"
    DOCX = "docx"
    DOKUWIKI = "dokuwiki"
    ENDNOTEXML = "endnotexml"
    EPUB = "epub"
    FB2 = "fb2"
    GFM = "gfm"
    HADDOCK = "haddock"
    HTML = "html"
    IPYNB = "ipynb"
    JATS = "jats"
    JIRA = "jira"
    JSON = "json"
    LATEX = "latex"
    MAN = "man"
    MARKDOWN = "markdown"
    MARKDOWN_GITHUB = "markdown_github"
    MARKDOWN_MMD = "markdown_mmd"
    MARKDOWN_PHPEXTRA = "markdown_phpextra"
    MARKDOWN_STRICT = "markdown_strict"
    MEDIAWIKI = "mediawiki"
    MUSE = "muse"
    NATIVE = "native"
    ODT = "odt"
    OPML = "opml"
    ORG = "org"
    RIS = "ris"
    RST = "rst"
    RTF = "rtf"
    T2T = "t2t"
    TEXTILE = "textile"
    TIKIWIKI = "tikiwiki"
    TSV = "tsv"
    TWIKI = "twiki"
    TYPST = "typst"
    VIMWIKI = "vimwiki"


class OutputFormat(Enum):
    """Supported output formats for pandoc."""

    ASCIIDOC = "asciidoc"
    ASCIIDOCTOR = "asciidoctor"
    BEAMER = "beamer"
    BIBLATEX = "biblatex"
    BIBTEX = "bibtex"
    CHUNKEDHTML = "chunkedhtml"
    COMMONMARK = "commonmark"
    COMMONMARK_X = "commonmark_x"
    CONTEXT = "context"
    CSLJSON = "csljson"
    DOCBOOK = "docbook"
    DOCBOOK4 = "docbook4"
    DOCBOOK5 = "docbook5"
    DOCX = "docx"
    DOKUWIKI = "dokuwiki"
    DZSLIDES = "dzslides"
    EPUB = "epub"
    EPUB2 = "epub2"
    EPUB3 = "epub3"
    FB2 = "fb2"
    GFM = "gfm"
    HADDOCK = "haddock"
    HTML = "html"
    HTML4 = "html4"
    HTML5 = "html5"
    ICML = "icml"
    IPYNB = "ipynb"
    JATS = "jats"
    JATS_ARCHIVING = "jats_archiving"
    JATS_ARTICLEAUTHORING = "jats_articleauthoring"
    JATS_PUBLISHING = "jats_publishing"
    JIRA = "jira"
    JSON = "json"
    LATEX = "latex"
    MAN = "man"
    MARKDOWN = "markdown"
    MARKDOWN_GITHUB = "markdown_github"
    MARKDOWN_MMD = "markdown_mmd"
    MARKDOWN_PHPEXTRA = "markdown_phpextra"
    MARKDOWN_STRICT = "markdown_strict"
    MARKUA = "markua"
    MEDIAWIKI = "mediawiki"
    MS = "ms"
    MUSE = "muse"
    NATIVE = "native"
    ODT = "odt"
    OPENDOCUMENT = "opendocument"
    OPML = "opml"
    ORG = "org"
    PDF = "pdf"
    PLAIN = "plain"
    PPTX = "pptx"
    REVEALJS = "revealjs"
    RST = "rst"
    RTF = "rtf"
    S5 = "s5"
    SLIDEOUS = "slideous"
    SLIDY = "slidy"
    TEI = "tei"
    TEXINFO = "texinfo"
    TEXTILE = "textile"
    TYPST = "typst"
    XWIKI = "xwiki"
    ZIMWIKI = "zimwiki"


@dataclass
class ConversionProfile:
    """Configuration for a pandoc conversion."""

    input_path: Path
    output_path: Path | None = None
    input_format: InputFormat | None = None
    output_format: OutputFormat = OutputFormat.HTML
    options: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.options is None:
            self.options = {}

        # Auto-generate output path if not provided
        if self.output_path is None:
            suffix = f".{self.output_format.value}"
            self.output_path = self.input_path.with_suffix(suffix)


@dataclass
class ConversionResult:
    """Result of a pandoc conversion operation."""

    success: bool
    output_path: Path | None = None
    error_message: str | None = None
    duration_seconds: float = 0.0
    command: str | None = None
