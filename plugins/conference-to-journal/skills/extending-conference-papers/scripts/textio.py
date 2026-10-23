"""Load paper files as plain text with the Python standard library.

Reads .txt, .md, .markdown, .tex, and .docx files. PDF files are read only
when the optional pypdf package is installed; otherwise they are refused with
a message that explains how to convert them. For LaTeX, the title and section
commands become Markdown headings so that sections can be compared, and
comments, math, and other commands are removed. For Word files, Title and
Heading styles become Markdown headings.
"""
from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".tex", ".docx", ".pdf"}

_WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_DOCUMENT_START = "\\begin{document}"

_TEX_TITLE = re.compile(r"\\title(?:\[[^\]]*\])?\{([^{}]*)\}")
_TEX_COMMENT = re.compile(r"(?<!\\)%.*")
_TEX_DISPLAY_MATH = re.compile(
    r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath)(\*?)\}"
    r".*?\\end\{\1\2\}",
    re.S,
)
_TEX_DOUBLE_DOLLAR = re.compile(r"\$\$.*?\$\$", re.S)
_TEX_BRACKET_MATH = re.compile(r"\\\[.*?\\\]", re.S)
_TEX_INLINE_MATH = re.compile(r"(?<!\\)\$[^$\n]*\$")
_TEX_DROP_COMMAND = re.compile(
    r"\\(?:cite[a-zA-Z]*|ref|eqref|autoref|cref|Cref|label|url|href|"
    r"includegraphics|input|include|bibliography|bibliographystyle)\*?"
    r"(?:\[[^\]]*\])*\{[^}]*\}"
)
_TEX_ABSTRACT = re.compile(r"\\begin\{abstract\}")
_TEX_ENVIRONMENT = re.compile(r"\\(?:begin|end)\{[^{}]*\}(?:\[[^\]]*\])?")
_TEX_UNWRAP_COMMAND = re.compile(
    r"\\(?!(?:section|subsection|subsubsection)\*?[\[{])[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}"
)
_TEX_SECTION = re.compile(r"\\(section|subsection|subsubsection)\*?(?:\[[^\]]*\])?\{([^{}]*)\}")
_HEADING_MARK = {"section": "##", "subsection": "###", "subsubsection": "####"}
_TEX_BARE_COMMAND = re.compile(r"\\[a-zA-Z]+\*?")


class UnreadableFile(Exception):
    """A file could not be turned into text. The message says why and what to do."""


def _same_line_count(match):
    # Replace removed text with the same number of line breaks, so line
    # numbers in reports still point at the right place in the source file.
    return "\n" * match.group(0).count("\n") or " "


def strip_tex(text):
    """Turn LaTeX into plain prose with Markdown headings."""
    title = _TEX_TITLE.search(text)
    if _DOCUMENT_START in text:
        preamble, body = text.split(_DOCUMENT_START, 1)
        heading = "# " + title.group(1).replace("\\\\", " ") if title else ""
        # The preamble becomes blank lines (title first) so line numbers still match the file.
        text = heading + "\n" * preamble.count("\n") + body
    text = _TEX_COMMENT.sub("", text)
    for pattern in (_TEX_DISPLAY_MATH, _TEX_DOUBLE_DOLLAR, _TEX_BRACKET_MATH, _TEX_DROP_COMMAND):
        text = pattern.sub(_same_line_count, text)
    text = _TEX_INLINE_MATH.sub(" ", text)
    text = _TEX_ABSTRACT.sub("## Abstract", text)
    text = _TEX_ENVIRONMENT.sub(" ", text)
    for _ in range(3):  # unwrap nested commands such as \emph{\textbf{x}}
        text = _TEX_UNWRAP_COMMAND.sub(r"\1", text)
    text = _TEX_SECTION.sub(lambda m: f"{_HEADING_MARK[m.group(1)]} {m.group(2)}", text)
    text = _TEX_BARE_COMMAND.sub(" ", text)
    return text.replace("{", " ").replace("}", " ").replace("~", " ")


def _read_docx(path):
    try:
        with zipfile.ZipFile(path) as archive:
            xml_bytes = archive.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise UnreadableFile(f"{path}: not a readable .docx file ({exc}).") from exc
    paragraphs, open_paragraphs = [], []
    try:
        for event, element in ElementTree.iterparse(io.BytesIO(xml_bytes), events=("start", "end")):
            tag = element.tag
            if tag == _WORD + "p":
                if event == "start":
                    open_paragraphs.append({"prefix": "", "parts": []})
                else:
                    paragraph = open_paragraphs.pop()
                    paragraphs.append(paragraph["prefix"] + "".join(paragraph["parts"]))
            elif event == "end" and open_paragraphs:
                if tag == _WORD + "pStyle":
                    style = element.get(_WORD + "val", "").lower()
                    if style == "title":
                        open_paragraphs[-1]["prefix"] = "# "
                    elif style.startswith("heading"):
                        open_paragraphs[-1]["prefix"] = "## "
                elif tag == _WORD + "t" and element.text:
                    open_paragraphs[-1]["parts"].append(element.text)
                elif tag in (_WORD + "tab", _WORD + "br", _WORD + "cr"):
                    open_paragraphs[-1]["parts"].append(" ")
    except ElementTree.ParseError as exc:
        raise UnreadableFile(f"{path}: the document XML is damaged ({exc}).") from exc
    return "\n".join(paragraphs)


def _read_pdf(path):
    try:
        from pypdf import PdfReader  # optional dependency
    except ImportError as exc:
        raise UnreadableFile(
            f"{path}: reading PDF needs the optional pypdf package (pip install pypdf). "
            f'Or convert it first: pdftotext -layout "{path}" "{path.with_suffix(".txt")}"'
        ) from exc
    try:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # pypdf raises many exception types for damaged files
        raise UnreadableFile(f"{path}: could not extract text ({exc}).") from exc


def load_text(path):
    """Return the text of one file, or raise UnreadableFile."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise UnreadableFile(
            f"{path}: unsupported file type '{suffix}'. Use .txt, .md, .tex, .docx, or .pdf."
        )
    if suffix == ".docx":
        return _read_docx(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Older files are often Latin-1 or Windows-1252; Latin-1 never fails to decode.
        text = path.read_text(encoding="latin-1")
    except OSError as exc:
        raise UnreadableFile(f"{path}: {exc.strerror or exc}.") from exc
    return strip_tex(text) if suffix == ".tex" else text
