#!/usr/bin/env python3
"""Find passages that repeat across the papers and chapters of a thesis.

Papers written to stand alone often reuse introduction and methods text. This
script reports every run of N or more identical words (default 12) that two
different files share, with line numbers, so the author can decide whether to
trim, cross-reference, or keep each passage.

Usage:
    python scripts/find_overlap.py PATH [PATH ...] [--min-words 12]
        [--max-passages 40] [--json overlap.json]

Each PATH is a file or a folder. Matching ignores case and punctuation.
In .docx files, one line is one paragraph.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from itertools import combinations

from textio import load_documents

# Twelve identical words in a row almost never occur by chance in academic
# prose, while stock phrases ("the results of this study show that") are
# shorter. Lower the value to catch shorter reuse; raise it to cut noise.
DEFAULT_MIN_WORDS = 12

# Below six words, ordinary phrases ("in the case of the") flood the report.
SMALLEST_MIN_WORDS = 6

# Small edits (a changed word, an inserted clause) split a reused paragraph
# into pieces. Pieces separated by at most this many words on both sides are
# reported as one near-verbatim passage.
JOIN_GAP_WORDS = 8

# A word sequence found this many times across all files is boilerplate, such
# as a running header. Skipping it keeps the run time predictable.
MAX_OCCURRENCES = 50

# Enough words to recognize a passage; the line numbers are the real pointer.
EXCERPT_WORDS = 30

DEFAULT_MAX_PASSAGES = 40

WORD_RE = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")


def tokenize(text):
    """Return lowercase words and the 1-based line number of each word."""
    words, lines = [], []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in WORD_RE.finditer(line.lower()):
            words.append(match.group(0))
            lines.append(line_number)
    return words, lines


def shared_runs(word_lists, min_words):
    """Yield (doc_a, doc_b, start_a, start_b, length) for each maximal run of
    identical words shared by two different documents, with doc_a < doc_b."""
    index = defaultdict(list)
    for doc, words in enumerate(word_lists):
        for start in range(len(words) - min_words + 1):
            index[tuple(words[start:start + min_words])].append((doc, start))

    # Shared windows on the same diagonal (same start_a - start_b) that follow
    # each other form one continuous run.
    diagonals = defaultdict(list)
    for occurrences in index.values():
        if len(occurrences) < 2 or len(occurrences) > MAX_OCCURRENCES:
            continue
        for (doc_a, start_a), (doc_b, start_b) in combinations(occurrences, 2):
            if doc_a == doc_b:
                continue
            if doc_a > doc_b:
                doc_a, start_a, doc_b, start_b = doc_b, start_b, doc_a, start_a
            diagonals[(doc_a, doc_b, start_a - start_b)].append(start_a)

    for (doc_a, doc_b, offset), starts in diagonals.items():
        starts.sort()
        run_start = previous = starts[0]
        for start in starts[1:] + [None]:
            if start is not None and start == previous + 1:
                previous = start
                continue
            yield doc_a, doc_b, run_start, run_start - offset, previous - run_start + min_words
            if start is not None:
                run_start = previous = start


def join_runs(runs):
    """Join runs for one file pair that sit within JOIN_GAP_WORDS of each other
    on both sides, so a lightly edited paragraph is reported once."""
    passages = []
    for start_a, start_b, length in sorted(runs):
        end_a, end_b = start_a + length, start_b + length
        for passage in reversed(passages):
            if (passage["start_a"] <= start_a <= passage["end_a"] + JOIN_GAP_WORDS
                    and passage["start_b"] <= start_b <= passage["end_b"] + JOIN_GAP_WORDS):
                passage["end_a"] = max(passage["end_a"], end_a)
                passage["end_b"] = max(passage["end_b"], end_b)
                passage["matched_a"].update(range(start_a, end_a))
                passage["matched_b"].update(range(start_b, end_b))
                passage["pieces"] += 1
                break
        else:
            passages.append({
                "start_a": start_a, "end_a": end_a,
                "start_b": start_b, "end_b": end_b,
                "matched_a": set(range(start_a, end_a)),
                "matched_b": set(range(start_b, end_b)),
                "pieces": 1,
            })
    return passages


def location(label, lines, start, end):
    first, last = lines[start], lines[end - 1]
    return f"{label} line {first}" if first == last else f"{label} lines {first}-{last}"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find passages repeated across thesis papers and chapters.")
    parser.add_argument("paths", nargs="+", help="files or folders to compare")
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS,
                        help=f"shortest repeated run to report (default {DEFAULT_MIN_WORDS})")
    parser.add_argument("--max-passages", type=int, default=DEFAULT_MAX_PASSAGES,
                        help=f"passages to print, longest first (default {DEFAULT_MAX_PASSAGES}); "
                             "the JSON file has all of them")
    parser.add_argument("--json", dest="json_path", help="also write full results to this JSON file")
    args = parser.parse_args(argv)
    if args.min_words < SMALLEST_MIN_WORDS:
        parser.error(f"--min-words below {SMALLEST_MIN_WORDS} reports ordinary phrases; "
                     f"use {SMALLEST_MIN_WORDS} or more.")

    documents = load_documents(args.paths)
    if len(documents) < 2:
        print("Need at least two readable files to compare.", file=sys.stderr)
        return 2

    labels = [label for label, _ in documents]
    tokens = [tokenize(text) for _, text in documents]

    runs_by_pair = defaultdict(list)
    for doc_a, doc_b, start_a, start_b, length in shared_runs([w for w, _ in tokens], args.min_words):
        runs_by_pair[(doc_a, doc_b)].append((start_a, start_b, length))

    passages, pairs = [], []
    for (doc_a, doc_b), runs in sorted(runs_by_pair.items()):
        words_a, lines_a = tokens[doc_a]
        words_b, lines_b = tokens[doc_b]
        joined = join_runs(runs)
        covered_a, covered_b = set(), set()
        for passage in joined:
            covered_a |= passage["matched_a"]
            covered_b |= passage["matched_b"]
            start_a, end_a = passage["start_a"], passage["end_a"]
            excerpt = " ".join(words_a[start_a:start_a + EXCERPT_WORDS])
            if end_a - start_a > EXCERPT_WORDS:
                excerpt += " ..."
            passages.append({
                "where_a": location(labels[doc_a], lines_a, start_a, end_a),
                "where_b": location(labels[doc_b], lines_b, passage["start_b"], passage["end_b"]),
                "words": end_a - start_a,
                "identical_words": len(passage["matched_a"]),
                "exact": passage["pieces"] == 1,
                "excerpt": excerpt,
            })
        pairs.append({
            "file_a": labels[doc_a],
            "file_b": labels[doc_b],
            "passages": len(joined),
            "repeated_words_a": len(covered_a),
            "share_a": round(100 * len(covered_a) / max(len(words_a), 1), 1),
            "share_b": round(100 * len(covered_b) / max(len(words_b), 1), 1),
        })
    passages.sort(key=lambda item: item["words"], reverse=True)

    out = [f"# Repeated text across {len(documents)} files", "",
           f"Runs of {args.min_words} or more identical words, ignoring case and punctuation. "
           "Line numbers refer to each file as read (in .docx files, one line is one paragraph).", ""]
    if not passages:
        out.append(f"No shared passages of {args.min_words} or more words were found.")
    else:
        out += ["## Summary by file pair", "",
                "| File A | File B | Passages | Words of A repeated | Share of A | Share of B |",
                "|---|---|---|---|---|---|"]
        for pair in pairs:
            out.append(f"| {pair['file_a']} | {pair['file_b']} | {pair['passages']} | "
                       f"{pair['repeated_words_a']} | {pair['share_a']}% | {pair['share_b']}% |")
        shown = passages[:args.max_passages]
        out += ["", f"## Passages, longest first ({len(shown)} of {len(passages)})", ""]
        for number, passage in enumerate(shown, start=1):
            kind = ("exact" if passage["exact"]
                    else f"near-verbatim, {passage['identical_words']} words identical")
            out.append(f"{number}. {passage['where_a']} and {passage['where_b']}: "
                       f"{passage['words']} words ({kind})")
            out.append(f"   > {passage['excerpt']}")
    print("\n".join(out))

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump({"min_words": args.min_words, "files": labels,
                       "pairs": pairs, "passages": passages}, handle, indent=2)
        print(f"\nFull results written to {args.json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
