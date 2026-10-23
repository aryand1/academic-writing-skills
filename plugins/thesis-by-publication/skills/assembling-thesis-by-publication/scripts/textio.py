"""Load thesis and paper files as plain text with the Python standard library.

Reads .txt, .md, .markdown, .tex, and .docx files. PDF files are read only
when the optional pypdf package is installed; otherwise they are skipped
with a message that explains how to convert them. LaTeX comments, math, and
commands are removed so that matching works on the prose.
"""
from __future__ import annotations

import io
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".tex"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | {".docx", ".pdf"}

_WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

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
_TEX_UNWRAP_COMMAND = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}")
_TEX_BARE_COMMAND = re.compile(r"\\[a-zA-Z]+\*?")


class UnreadableFile(Exception):
    """A file could not be turned into text. The message says why and what to do."""


def _same_line_count(match):
    # Replace removed text with the same number of line breaks, so line
    # numbers in reports still point at the right place in the source file.
    return "\n" * match.group(0).count("\n") or " "


def strip_tex(text):
    """Remove LaTeX comments, math, and commands, keeping the prose."""
    text = _TEX_COMMENT.sub("", text)
    for pattern in (_TEX_DISPLAY_MATH, _TEX_DOUBLE_DOLLAR, _TEX_BRACKET_MATH, _TEX_DROP_COMMAND):
        text = pattern.sub(_same_line_count, text)
    text = _TEX_INLINE_MATH.sub(" ", text)
    for _ in range(3):  # unwrap nested commands such as \emph{\textbf{x}}
        text = _TEX_UNWRAP_COMMAND.sub(r"\1", text)
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
            if element.tag == _WORD + "p":
                if event == "start":
                    open_paragraphs.append([])
                else:
                    paragraphs.append("".join(open_paragraphs.pop()))
            elif event == "end" and open_paragraphs:
                if element.tag == _WORD + "t" and element.text:
                    open_paragraphs[-1].append(element.text)
                elif element.tag in (_WORD + "tab", _WORD + "br", _WORD + "cr"):
                    open_paragraphs[-1].append(" ")
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


def collect_paths(arguments):
    """Expand folders into the supported files they contain, sorted by name."""
    paths = []
    for argument in arguments:
        path = Path(argument)
        if path.is_dir():
            paths.extend(sorted(
                child for child in path.iterdir()
                if child.is_file()
                and child.suffix.lower() in SUPPORTED_SUFFIXES
                and not child.name.startswith((".", "~$"))  # hidden files and Word lock files
            ))
        else:
            paths.append(path)
    return paths


def load_documents(arguments):
    """Return [(label, text)] for every readable file; report the rest on stderr."""
    paths = collect_paths(arguments)
    names = [path.name for path in paths]
    documents = []
    for path in paths:
        if not path.is_file():
            print(f"Skipped {path}: file not found.", file=sys.stderr)
            continue
        try:
            text = load_text(path)
        except UnreadableFile as exc:
            print(f"Skipped {exc}", file=sys.stderr)
            continue
        label = path.name if names.count(path.name) == 1 else path.as_posix()
        documents.append((label, text))
    return documents
