#!/usr/bin/env python3
"""Compare acronym definitions across the papers and chapters of a thesis.

Finds definitions written as "long form (SHORT)" or "SHORT (long form)" and
reports:
  1. one acronym given different long forms,
  2. one long form given different acronyms,
  3. acronyms used in a file that does not define them, although another file does,
  4. acronym-like terms that no file defines.

Usage:
    python scripts/check_acronyms.py PATH [PATH ...] [--json acronyms.json]

Each PATH is a file or a folder. Definitions are found with the algorithm of
Schwartz and Hearst (2003), "A simple algorithm for identifying abbreviation
definitions in biomedical text".
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from collections import Counter, defaultdict

from textio import load_documents

# Schwartz and Hearst search at most min(len(short) + 5, 2 * len(short))
# words before the parenthesis for the long form.
EXTRA_WORDS = 5

# Short forms: 2 to 10 characters, starting with a letter, with at least two
# capitals ("NLP", "LLMs", "ConvNet"). This skips "(i)", "(Fig)", "(Smith)".
SHORT_FORM_RE = re.compile(r"^[A-Za-z][A-Za-z0-9&/\-]{1,9}$")
MIN_CAPITALS = 2

PARENTHESIS_RE = re.compile(r"\(([^()\n]{1,150})\)")

# Never-defined candidates: words of up to 6 characters (7 with a plural s)
# with two or more capitals. Longer all-capital words are usually headings.
TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9]{1,6}(?![A-Za-z0-9])")
CANDIDATE_MAX_LENGTH = 6
ROMAN_NUMERALS = {"II", "III", "IV", "VI", "VII", "VIII", "IX", "XI", "XII", "XIII", "XIV", "XV"}

# Enough candidates to act on without burying the conflicts above them.
MAX_CANDIDATES = 25


def short_key(short):
    """Treat 'LLMs' and 'LLM' as one acronym."""
    if len(short) > 2 and short.endswith("s") and short[-2].isupper():
        return short[:-1]
    return short


def long_key(long_form):
    """Normalize a long form for comparison: case, hyphens, spacing, final plural."""
    text = re.sub(r"[\-‐-―/]", " ", long_form.lower())
    words = [word.strip(".,;:\"'()[]") for word in text.split()]
    words = [word for word in words if word]
    if words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith("ss"):
        words[-1] = words[-1][:-1]
    return " ".join(words)


def is_short_form(text):
    return bool(SHORT_FORM_RE.match(text)) and sum(ch.isupper() for ch in text) >= MIN_CAPITALS


def match_long_form(short, candidate):
    """Schwartz and Hearst: find the shortest end of `candidate` that contains the
    letters of `short` in order, with the first letter at the start of a word."""
    s_index, l_index = len(short) - 1, len(candidate) - 1
    while s_index >= 0:
        char = short[s_index].lower()
        if not char.isalnum():
            s_index -= 1
            continue
        while l_index >= 0 and (
            candidate[l_index].lower() != char
            or (s_index == 0 and l_index > 0 and candidate[l_index - 1].isalnum())
        ):
            l_index -= 1
        if l_index < 0:
            return None
        l_index -= 1
        s_index -= 1
    start = candidate.rfind(" ", 0, l_index + 1) + 1
    long_form = candidate[start:].strip(" \"'([{")
    if len(long_form) <= len(short) or (" " not in long_form and "-" not in long_form):
        return None
    return long_form


def find_definitions(text):
    """Return [(short, long_form, line_number)] for each definition in `text`."""
    newlines = [index for index, ch in enumerate(text) if ch == "\n"]
    found = []
    for match in PARENTHESIS_RE.finditer(text):
        inside = re.split(r"[;,]", match.group(1))[0].strip()
        before_words = text[max(0, match.start() - 400):match.start()].split()
        line = bisect.bisect_right(newlines, match.start()) + 1
        if is_short_form(inside):  # long form (SHORT)
            limit = min(len(inside) + EXTRA_WORDS, 2 * len(inside))
            long_form = match_long_form(inside, " ".join(before_words[-limit:]))
            if long_form:
                found.append((inside, long_form, line))
        elif before_words and len(inside.split()) >= 2:  # SHORT (long form)
            short = before_words[-1].strip(".,;:\"'")
            if is_short_form(short):
                long_form = match_long_form(short, inside)
                if long_form:
                    found.append((short, long_form, line))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare acronym definitions across thesis papers and chapters.")
    parser.add_argument("paths", nargs="+", help="files or folders to check")
    parser.add_argument("--json", dest="json_path", help="also write full results to this JSON file")
    args = parser.parse_args(argv)

    documents = load_documents(args.paths)
    if not documents:
        print("No readable files to check.", file=sys.stderr)
        return 2

    definitions = defaultdict(lambda: defaultdict(list))  # acronym -> long form key -> entries
    by_long_form = defaultdict(lambda: defaultdict(set))  # long form key -> acronym -> files
    defined_in = defaultdict(set)                         # acronym -> files
    for label, text in documents:
        for short, long_form, line in find_definitions(text):
            acronym, form = short_key(short), long_key(long_form)
            definitions[acronym][form].append({"file": label, "line": line, "long_form": long_form})
            by_long_form[form][acronym].add(label)
            defined_in[acronym].add(label)

    same_acronym = {a: forms for a, forms in definitions.items() if len(forms) > 1}
    same_long_form = {f: acronyms for f, acronyms in by_long_form.items() if len(acronyms) > 1}

    used_without_definition = []
    for acronym in sorted(defined_in):
        pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(acronym) + r"s?(?![A-Za-z0-9])")
        for label, text in documents:
            if label in defined_in[acronym]:
                continue
            uses = len(pattern.findall(text))
            if uses:
                used_without_definition.append({"acronym": acronym, "file": label, "uses": uses,
                                                "defined_in": sorted(defined_in[acronym])})

    never_defined, never_files = Counter(), defaultdict(set)
    for label, text in documents:
        for token in TOKEN_RE.findall(text):
            term = short_key(token)
            if (len(term) <= CANDIDATE_MAX_LENGTH
                    and sum(ch.isupper() for ch in term) >= MIN_CAPITALS
                    and term not in defined_in
                    and term not in ROMAN_NUMERALS):
                never_defined[term] += 1
                never_files[term].add(label)

    total = sum(len(entries) for forms in definitions.values() for entries in forms.values())
    out = [f"# Acronym check across {len(documents)} files", "",
           f"Found {total} definitions of {len(definitions)} acronyms, written as "
           "'long form (SHORT)' or 'SHORT (long form)'.", "",
           "## One acronym, different long forms", ""]
    if same_acronym:
        out += ["| Acronym | Long form | Defined in |", "|---|---|---|"]
        for acronym in sorted(same_acronym):
            for entries in same_acronym[acronym].values():
                places = ", ".join(f"{e['file']} (line {e['line']})" for e in entries)
                out.append(f"| {acronym} | {entries[0]['long_form']} | {places} |")
    else:
        out.append("None found.")

    out += ["", "## One long form, different acronyms", ""]
    if same_long_form:
        out += ["| Long form | Acronym | Defined in |", "|---|---|---|"]
        for form in sorted(same_long_form):
            for acronym, files in sorted(same_long_form[form].items()):
                out.append(f"| {form} | {acronym} | {', '.join(sorted(files))} |")
    else:
        out.append("None found.")

    out += ["", "## Used without a definition in the same file", "",
            "Each paper chapter usually needs its own definitions, or the thesis needs an abbreviations list.", ""]
    if used_without_definition:
        out += ["| Acronym | Used in | Uses | Defined in |", "|---|---|---|---|"]
        for item in used_without_definition:
            out.append(f"| {item['acronym']} | {item['file']} | {item['uses']} | {', '.join(item['defined_in'])} |")
    else:
        out.append("None found.")

    out += ["", "## Never defined in any file (candidates)", "",
            "Many of these are standard terms (units, country codes, degree names) that need no "
            "definition. Check the rest.", ""]
    if never_defined:
        out += ["| Term | Uses | Files |", "|---|---|---|"]
        for term, uses in never_defined.most_common(MAX_CANDIDATES):
            out.append(f"| {term} | {uses} | {', '.join(sorted(never_files[term]))} |")
    else:
        out.append("None found.")
    print("\n".join(out))

    if args.json_path:
        result = {
            "files": [label for label, _ in documents],
            "definitions": {a: dict(forms) for a, forms in definitions.items()},
            "same_acronym_different_long_forms": sorted(same_acronym),
            "same_long_form_different_acronyms": {
                f: {a: sorted(files) for a, files in acronyms.items()} for f, acronyms in same_long_form.items()
            },
            "used_without_definition": used_without_definition,
            "never_defined": [{"term": t, "uses": u, "files": sorted(never_files[t])}
                              for t, u in never_defined.most_common()],
        }
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        print(f"\nFull results written to {args.json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
