#!/usr/bin/env python3
"""Compare a conference paper with its extended journal version.

Reports how much of each journal section is carried over word for word from
the conference paper and how much is new, an overall estimate of new text
against a threshold, which conference sections were kept, and quick checks on
the title, the abstract, and the disclosure of the conference paper.

Usage:
    python scripts/compare_versions.py CONFERENCE JOURNAL [--threshold 30]
        [--min-words 8] [--conference-doi DOI] [--json report.json]

Files can be .txt, .md, .tex, .docx, or .pdf (PDF needs the optional pypdf
package). Headings come from Markdown, LaTeX section commands, Word heading
styles, numbered lines such as "3.1 Results", and common section names.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from textio import UnreadableFile, load_text

# Text the authors reuse is often lightly edited, so the window is shorter
# than for unrelated papers. Eight identical words in a row from the same
# authors on the same topic is almost always reuse, not coincidence.
DEFAULT_MIN_WORDS = 8

# Below five words, stock phrases ("the results of the") count as reuse.
SMALLEST_MIN_WORDS = 5

# More than half of the abstract carried over word for word reads as the old
# abstract with a sentence added, which several venues explicitly reject.
ABSTRACT_REUSE_WARNING = 50

# Lines longer than this are body text, not headings.
HEADING_MAX_WORDS = 10

# These parts never count as new material, so they are left out of all counts.
NOT_COUNTED = {
    "front matter", "keywords", "index terms", "references", "bibliography",
    "acknowledgments", "acknowledgements", "acknowledgment", "acknowledgement",
}
REFERENCE_SECTIONS = {"references", "bibliography"}

KNOWN_SECTIONS = NOT_COUNTED | {
    "abstract", "introduction", "background", "related work", "related works", "prior work",
    "preliminaries", "problem statement", "problem formulation", "method", "methods",
    "methodology", "approach", "design", "implementation", "system", "model", "experiments",
    "experimental setup", "evaluation", "results", "discussion", "limitations",
    "threats to validity", "future work", "conclusion", "conclusions", "summary", "appendix",
}

STOPWORDS = {"a", "an", "the", "of", "for", "and", "or", "in", "on", "with", "to", "via", "by",
             "from", "at", "using"}

WORD_RE = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*$")
NUMBERED_HEADING_RE = re.compile(r"^(?:\d{1,2}(?:\.\d{1,2})*\.?|[IVX]{1,5}\.)\s+([A-Z][^.!?]*)$")
INLINE_HEADING_RE = re.compile(r"^(abstract|index terms|keywords)\s*[—–:.\-]+\s*(.+)$", re.I)
DISCLOSURE_RE = re.compile(
    r"\b(?:extended version|extends (?:our|the|an?) (?:earlier|previous|prior|preliminary|conference)"
    r"|extension of (?:our|the|an?)|preliminary version|earlier version|conference version"
    r"|previous version|appeared in|presented at|this (?:paper|article|work) (?:extends|expands|builds on))\b",
    re.I,
)


def normalize_heading(text):
    text = re.sub(r"^(?:\d{1,2}(?:\.\d{1,2})*\.?|[IVX]{1,5}\.)\s+", "", text.strip())
    return re.sub(r"\s+", " ", text.rstrip(":").strip().lower())


def heading_of(line):
    """Return the heading text if the line looks like a section heading, else None."""
    if not line or len(line.split()) > HEADING_MAX_WORDS:
        return None
    for pattern in (MARKDOWN_HEADING_RE, NUMBERED_HEADING_RE):
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    if normalize_heading(line) in KNOWN_SECTIONS:
        return line.rstrip(":").strip()
    return None


def split_sections(text):
    """Return (title, sections). The first non-empty line is the title. Each section
    is a dict with name, key, line, counted, lines, and words."""
    title = None
    sections = [{"name": "Front matter", "line": 1, "lines": []}]
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if title is None:
            if stripped:
                match = MARKDOWN_HEADING_RE.match(stripped)
                title = (match.group(1) if match else stripped).strip()
            continue
        inline = INLINE_HEADING_RE.match(stripped)
        if inline and len(inline.group(2).split()) > 3:
            sections.append({"name": inline.group(1).title(), "line": number,
                             "lines": [(number, inline.group(2))]})
            continue
        name = heading_of(stripped)
        if name:
            sections.append({"name": name, "line": number, "lines": []})
        else:
            sections[-1]["lines"].append((number, line))
    if len(sections) == 1:
        sections[0]["name"] = "Body"  # no headings found: count the whole text as one section
    kept = []
    for section in sections:
        section["key"] = normalize_heading(section["name"])
        section["counted"] = section["key"] not in NOT_COUNTED
        section["words"] = [m.group(0) for _, line in section["lines"]
                            for m in WORD_RE.finditer(line.lower())]
        if section["words"] or section["name"] != "Front matter":
            kept.append(section)
    return title or "(no title found)", kept


def window_index(sections, size):
    """Map every run of `size` words in counted sections to the sections it occurs in."""
    index = defaultdict(set)
    for number, section in enumerate(sections):
        if not section["counted"]:
            continue
        words = section["words"]
        for start in range(len(words) - size + 1):
            index[tuple(words[start:start + size])].add(number)
    return index


def mark_carried(words, index, size):
    """Return (one carried-over flag per word, Counter of source sections)."""
    carried, sources = [False] * len(words), Counter()
    for start in range(len(words) - size + 1):
        hits = index.get(tuple(words[start:start + size]))
        if hits:
            for position in range(start, start + size):
                carried[position] = True
            sources.update(hits)
    return carried, sources


def percent(part, whole):
    return round(100 * part / whole, 1) if whole else 0.0


def flat(text):
    return " ".join(WORD_RE.findall(text.lower()))


def content_words(text):
    return [word for word in WORD_RE.findall(text.lower()) if word not in STOPWORDS]


def compare(conference_text, journal_text, size, conference_doi=None):
    conf_title, conf_sections = split_sections(conference_text)
    jour_title, jour_sections = split_sections(journal_text)
    conf_index = window_index(conf_sections, size)
    jour_index = window_index(jour_sections, size)

    journal_rows, total, carried_total = [], 0, 0
    for section in jour_sections:
        if not section["counted"]:
            continue
        carried, sources = mark_carried(section["words"], conf_index, size)
        words, kept = len(section["words"]), sum(carried)
        total += words
        carried_total += kept
        journal_rows.append({
            "section": section["name"], "line": section["line"], "words": words,
            "carried": kept, "new": words - kept, "new_percent": percent(words - kept, words),
            "source": conf_sections[sources.most_common(1)[0][0]]["name"] if sources else None,
        })

    conference_rows, conference_total = [], 0
    for section in conf_sections:
        if not section["counted"]:
            continue
        carried, _ = mark_carried(section["words"], jour_index, size)
        words = len(section["words"])
        conference_total += words
        conference_rows.append({"section": section["name"], "words": words, "kept": sum(carried),
                                "kept_percent": percent(sum(carried), words)})

    journal_abstract = next((s for s in jour_sections if s["key"] == "abstract"), None)
    conference_abstract = next((s for s in conf_sections if s["key"] == "abstract"), None)
    abstract_reuse = None
    if journal_abstract and conference_abstract and journal_abstract["words"]:
        carried, _ = mark_carried(journal_abstract["words"], conf_index, size)
        abstract_reuse = percent(sum(carried), len(journal_abstract["words"]))

    disclosures = []
    for section in jour_sections:
        if section["key"] in REFERENCE_SECTIONS:
            continue
        for number, line in section["lines"]:
            match = DISCLOSURE_RE.search(line)
            if match:
                disclosures.append({"line": number, "phrase": match.group(0)})

    title_a, title_b = content_words(conf_title), content_words(jour_title)
    identical = title_a == title_b
    title = {"identical": identical,
             "shared_percent": 100.0 if identical else
             percent(len(set(title_a) & set(title_b)), len(set(title_a) | set(title_b)))}

    title_found = None
    if conf_title != "(no title found)" and len(title_a) >= 3 and not identical:
        title_found = flat(conf_title) in flat(journal_text)
    doi_found = None
    if conference_doi:
        doi_found = conference_doi.strip().lower() in journal_text.lower()

    notes = []
    for label, sections in (("conference", conf_sections), ("journal", jour_sections)):
        if any(s["name"] == "Body" for s in sections):
            notes.append(f"No headings were found in the {label} file, so it is treated as one section.")

    return {
        "conference_title": conf_title, "journal_title": jour_title,
        "journal_words": total, "carried_words": carried_total, "new_words": total - carried_total,
        "new_percent": percent(total - carried_total, total), "conference_words": conference_total,
        "length_ratio": round(total / conference_total, 2) if conference_total else None,
        "journal_sections": journal_rows, "conference_sections": conference_rows,
        "title": title, "abstract_reuse_percent": abstract_reuse, "disclosures": disclosures,
        "conference_title_found": title_found, "conference_doi_found": doi_found, "notes": notes,
    }


def share(part, whole):
    return f"{part} ({percent(part, whole)}%)"


def render(result, conference_label, journal_label, size, threshold):
    r = result
    out = ["# Conference to journal comparison", "",
           f"- Conference version: {conference_label}, titled \"{r['conference_title']}\"",
           f"- Journal version: {journal_label}, titled \"{r['journal_title']}\"",
           f"- Reuse is counted in runs of {size} or more identical words, ignoring case and "
           "punctuation. Front matter, keywords, references, and acknowledgments are left out of all counts.",
           ""]
    for note in r["notes"]:
        out += [f"Note: {note}", ""]

    out += ["## Overall", "", "| Measure | Value |", "|---|---|",
            f"| Journal words counted | {r['journal_words']} |",
            f"| Carried over word for word | {share(r['carried_words'], r['journal_words'])} |",
            f"| New or reworded | {share(r['new_words'], r['journal_words'])} |"]
    if r["length_ratio"] is not None:
        out.append(f"| Length compared with the conference version | {r['length_ratio']}x |")
    if threshold is not None:
        verdict = "meets" if r["new_percent"] >= threshold else "falls short of"
        out.append(f"| Threshold | {threshold:g}% new: the text estimate {verdict} it |")
    out += ["", "This is a text measure. Reworded text counts as new here, while editors judge new "
            "contributions (results, methods, analysis, data), not new words. Use it as a floor check, "
            "not as proof of compliance.", ""]

    out += ["## Journal sections", "",
            "| Journal section | Line | Words | Carried over | New or reworded | Main source in conference version |",
            "|---|---|---|---|---|---|"]
    for row in r["journal_sections"]:
        out.append(f"| {row['section']} | {row['line']} | {row['words']} | "
                   f"{share(row['carried'], row['words'])} | {share(row['new'], row['words'])} | "
                   f"{row['source'] or 'none (new)'} |")

    out += ["", "## Conference sections in the journal version", "",
            "| Conference section | Words | Kept word for word |", "|---|---|---|"]
    for row in r["conference_sections"]:
        out.append(f"| {row['section']} | {row['words']} | {share(row['kept'], row['words'])} |")

    out += ["", "## Required-change checks", ""]
    if r["title"]["identical"]:
        out.append("- Title: identical to the conference title. Most venues expect a new or at least "
                   "different title.")
    else:
        out.append(f"- Title: differs from the conference title ({r['title']['shared_percent']}% of "
                   "content words shared).")
    reuse = r["abstract_reuse_percent"]
    if reuse is None:
        out.append("- Abstract: not compared (no section named Abstract in one of the files).")
    elif reuse > ABSTRACT_REUSE_WARNING:
        out.append(f"- Abstract: {reuse}% carried over word for word. Above {ABSTRACT_REUSE_WARNING}%, it "
                   "reads as the conference abstract with additions; rewrite it around the journal "
                   "version's contributions.")
    else:
        out.append(f"- Abstract: {reuse}% carried over word for word.")
    if r["disclosures"]:
        first = r["disclosures"][0]
        out.append(f"- Disclosure sentence: found at line {first['line']} (\"{first['phrase']}\").")
    else:
        out.append("- Disclosure sentence: none found outside the references. Add one to the introduction "
                   "that names the conference paper and says how this version extends it.")
    found = r["conference_title_found"]
    if found is None:
        out.append("- Conference paper cited: not checked (no usable conference title, or the titles are identical).")
    elif found:
        out.append("- Conference paper cited: its title appears in the journal text.")
    else:
        out.append("- Conference paper cited: its title was not found in the journal text. Check the reference list.")
    if r["conference_doi_found"] is not None:
        out.append(f"- Conference DOI: {'found' if r['conference_doi_found'] else 'not found'} in the journal text.")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compare a conference paper with its extended journal version.")
    parser.add_argument("conference", help="the published conference paper")
    parser.add_argument("journal", help="the journal version (draft or final)")
    parser.add_argument("--threshold", type=float, help="required share of new material, in percent")
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS,
                        help=f"shortest run of identical words counted as carried over (default {DEFAULT_MIN_WORDS})")
    parser.add_argument("--conference-doi", help="DOI of the conference paper, to check that it appears")
    parser.add_argument("--json", dest="json_path", help="also write full results to this JSON file")
    args = parser.parse_args(argv)
    if args.min_words < SMALLEST_MIN_WORDS:
        parser.error(f"--min-words below {SMALLEST_MIN_WORDS} counts stock phrases as reuse; "
                     f"use {SMALLEST_MIN_WORDS} or more.")
    if args.threshold is not None and not 0 <= args.threshold <= 100:
        parser.error("--threshold is a percentage between 0 and 100.")

    texts = []
    for name in (args.conference, args.journal):
        path = Path(name)
        if not path.is_file():
            print(f"File not found: {path}", file=sys.stderr)
            return 2
        try:
            texts.append(load_text(path))
        except UnreadableFile as exc:
            print(str(exc), file=sys.stderr)
            return 2

    result = compare(texts[0], texts[1], args.min_words, args.conference_doi)
    print(render(result, Path(args.conference).name, Path(args.journal).name, args.min_words, args.threshold))
    if args.json_path:
        payload = dict(result, min_words=args.min_words, threshold=args.threshold)
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        print(f"\nFull results written to {args.json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
