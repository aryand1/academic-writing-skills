#!/usr/bin/env python3
"""Check a thesis-plan.json file against the rules it records.

Usage:
    python scripts/validate_plan.py thesis-plan.json [--strict]

The plan's "rules" section holds the university's requirements. This script
tests the papers and chapters against those rules, reports what is still
missing for submission, and lists every value marked TODO.

Exit codes:
    0  no errors (and, with --strict, no warnings)
    1  errors found (or, with --strict, warnings found)
    2  the plan could not be read
"""
from __future__ import annotations

import argparse
import json
import sys

STATUSES = ("published", "accepted", "submitted", "in-preparation")
STATUS_ALIASES = {
    "in press": "accepted",
    "in-press": "accepted",
    "forthcoming": "accepted",
    "under review": "submitted",
    "under-review": "submitted",
    "in review": "submitted",
    "in preparation": "in-preparation",
    "in prep": "in-preparation",
}
COUNTS_AS_PUBLISHED = ("published", "accepted")
CHAPTER_TYPES = ("introduction", "literature-review", "methods", "paper", "linking",
                 "discussion", "conclusion", "appendix", "other")
REFORMATTING = ("as-published", "allowed", "required")
STATEMENT_STATES = ("not-started", "drafted", "sent", "signed", "not-needed")
PERMISSION_STATES = ("not-checked", "requested", "confirmed", "not-needed")
PERMISSION_BASES = ("open-license", "author-rights", "publisher-permission", "not-needed", "unknown")
LINKING_STATES = ("not-needed", "not-started", "drafted", "done")
VERSIONS = ("version-of-record", "accepted-manuscript", "submitted-manuscript", "reformatted")
GUIDE = "references/authorship-and-permissions.md"


def is_todo(value):
    return isinstance(value, str) and value.strip().upper().startswith("TODO")


def known(value):
    """True when a value is filled in: not missing, empty, or TODO."""
    return value not in (None, "", []) and not is_todo(value)


class Report:
    def __init__(self):
        self.errors, self.warnings, self.todos = [], [], []

    def error(self, where, message):
        self.errors.append(f"{where}: {message}")

    def warn(self, where, message):
        self.warnings.append(f"{where}: {message}")


def collect_todos(node, path, report):
    if isinstance(node, dict):
        for key, value in node.items():
            if not str(key).startswith("_"):
                collect_todos(value, f"{path}.{key}" if path else str(key), report)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            collect_todos(value, f"{path}[{index}]", report)
    elif is_todo(node):
        report.todos.append(path)


def rule(rules, key):
    """A rule's value, or None when the policy sets no such rule or it is still TODO."""
    value = rules.get(key)
    return value if known(value) else None


def int_rule(rules, key):
    value = rule(rules, key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def bool_rule(rules, key):
    value = rule(rules, key)
    return value if isinstance(value, bool) else None


def normalize_status(raw):
    if not isinstance(raw, str):
        return None
    key = raw.strip().lower()
    key = STATUS_ALIASES.get(key, key)
    return key if key in STATUSES else None


def check_enum(report, where, field, value, allowed):
    if known(value) and value not in allowed:
        report.warn(where, f"{field} is '{value}'; expected one of: {', '.join(allowed)}.")


def check_rules(rules, report):
    if not known(rules.get("source")):
        report.warn("rules.source", "record the policy document, section, and link the rules come "
                    "from, so the plan can be checked against it.")
    check_enum(report, "rules", "reformatting", rules.get("reformatting"), REFORMATTING)
    allowed = rule(rules, "allowed_statuses")
    if allowed is not None:
        if not isinstance(allowed, list):
            report.error("rules.allowed_statuses", 'must be a list, for example ["published", "accepted"].')
        else:
            for value in allowed:
                if normalize_status(value) is None:
                    report.error("rules.allowed_statuses",
                                 f"unknown status '{value}'. Use: {', '.join(STATUSES)}.")
    for key in ("min_papers", "max_papers", "min_published_or_accepted"):
        value = rule(rules, key)
        if value is not None and int_rule(rules, key) is None:
            report.error(f"rules.{key}", "must be a whole number or null.")
    for key in ("candidate_first_author_required", "papers_must_be_from_candidature",
                "contribution_statement_required", "co_author_signatures_required"):
        if rule(rules, key) is not None and bool_rule(rules, key) is None:
            report.error(f"rules.{key}", "must be true, false, or null.")


def check_papers(papers, rules, report):
    """Check each paper. Return ({id: status}, number of papers)."""
    allowed = rule(rules, "allowed_statuses")
    allowed = ({normalize_status(s) for s in allowed} - {None}) if isinstance(allowed, list) else None
    first_author = bool_rule(rules, "candidate_first_author_required")
    candidature = bool_rule(rules, "papers_must_be_from_candidature")
    statement_required = bool_rule(rules, "contribution_statement_required")
    signatures_required = bool_rule(rules, "co_author_signatures_required")
    reformatting = rule(rules, "reformatting")

    statuses, total = {}, 0
    for index, paper in enumerate(papers):
        where = f"papers[{index}]"
        if not isinstance(paper, dict):
            report.error(where, "each paper must be a JSON object.")
            continue
        total += 1
        paper_id = paper.get("id")
        if known(paper_id):
            where = f"{where} ({paper_id})"
        for field in ("id", "title", "authors", "status", "chapter"):
            if paper.get(field) in (None, "", []):
                report.error(where, f"'{field}' is missing.")

        raw_status = paper.get("status")
        status = normalize_status(raw_status)
        if known(raw_status) and status is None:
            report.error(where, f"unknown status '{raw_status}'. Use one of: {', '.join(STATUSES)} "
                         "(a preprint is usually 'submitted' or 'in-preparation').")
        if known(paper_id):
            if paper_id in statuses:
                report.error(where, f"id '{paper_id}' is used by more than one paper.")
            statuses[paper_id] = status
        if status and allowed is not None and status not in allowed:
            report.error(where, f"status '{status}' does not count under the rules "
                         f"(allowed: {', '.join(sorted(allowed))}).")

        authors = paper.get("authors") if isinstance(paper.get("authors"), list) else []
        co_authored = len(authors) > 1

        position = paper.get("candidate_author_position")
        if position is not None and not is_todo(position) and (
                isinstance(position, bool) or not isinstance(position, int)):
            report.error(where, "candidate_author_position must be a number (1 for first author) or null.")
            position = None
        elif not isinstance(position, int):
            position = None
        if position is not None and authors and not 1 <= position <= len(authors):
            report.error(where, f"candidate_author_position is {position}, but the paper lists "
                         f"{len(authors)} author(s).")
        if first_author is True:
            if position is None:
                report.warn(where, "candidate_author_position is unknown, and the rules require first authorship.")
            elif position != 1:
                report.error(where, f"the candidate is author {position}, but the rules require first "
                             "authorship. Ask the graduate school whether this paper can count (some "
                             "policies accept equal-first or principal authorship) before relying on it.")

        during = paper.get("research_during_candidature")
        if candidature is True:
            if during is False:
                report.error(where, "the rules require research done during candidature, and this "
                             "paper is marked as not.")
            elif during is not True:
                report.warn(where, "research_during_candidature is unknown, and the rules require it.")

        statement = paper.get("contribution_statement")
        statement = statement if isinstance(statement, dict) else {}
        state = statement.get("status")
        check_enum(report, where, "contribution_statement.status", state, STATEMENT_STATES)
        if co_authored:
            if statement_required is True and state not in ("drafted", "sent", "signed"):
                report.warn(where, f"this co-authored paper needs a contribution statement "
                            f"(now '{state or 'not recorded'}'). See {GUIDE}.")
            elif statement_required is None and state in (None, "not-started"):
                report.warn(where, "this co-authored paper has no contribution statement yet. Most "
                            "policies require one; confirm the rule and start a draft.")
            if signatures_required is True and state != "signed":
                report.warn(where, f"the rules require all authors to sign the statement "
                            f"(now '{state or 'not recorded'}').")

        permission = paper.get("permission")
        permission = permission if isinstance(permission, dict) else {}
        check_enum(report, where, "permission.status", permission.get("status"), PERMISSION_STATES)
        check_enum(report, where, "permission.basis", permission.get("basis"), PERMISSION_BASES)
        if status in COUNTS_AS_PUBLISHED:
            permission_state = permission.get("status")
            if permission_state not in ("confirmed", "not-needed"):
                report.warn(where, f"permission to include this {status} paper is "
                            f"'{permission_state or 'not recorded'}'. See {GUIDE}.")
            elif permission_state == "confirmed" and not known(permission.get("source")):
                report.warn(where, "permission is marked confirmed but has no source "
                            "(link, agreement clause, or email date).")
            if status == "published" and "doi" not in paper:
                report.warn(where, "add the DOI, or 'none' if the paper has no DOI.")

        version = paper.get("version_in_thesis")
        check_enum(report, where, "version_in_thesis", version, VERSIONS)
        if version == "version-of-record" and status in ("submitted", "in-preparation"):
            report.error(where, f"a {status} paper has no version of record yet.")
        if reformatting == "as-published" and version == "reformatted":
            report.error(where, "the rules require papers as published, but this one is marked reformatted.")
        if reformatting == "required" and known(version) and version != "reformatted":
            report.warn(where, "the rules require papers to be reformatted into the thesis style.")
        if paper.get("role_in_argument") in (None, ""):
            report.warn(where, "add role_in_argument: the question this paper answers and what "
                        "later chapters take from it.")
    return statuses, total


def check_counts(statuses, total, rules, report):
    minimum, maximum = int_rule(rules, "min_papers"), int_rule(rules, "max_papers")
    if minimum is not None and total < minimum:
        report.error("papers", f"{total} paper(s) listed; the rules require at least {minimum}.")
    if maximum is not None and total > maximum:
        report.error("papers", f"{total} paper(s) listed; the rules allow at most {maximum}.")
    needed = int_rule(rules, "min_published_or_accepted")
    if needed is not None:
        done = sum(1 for status in statuses.values() if status in COUNTS_AS_PUBLISHED)
        if done < needed:
            report.error("papers", f"{done} paper(s) are published or accepted; the rules require at "
                         f"least {needed}. Papers under review may change this before submission.")


def check_chapters(chapters, papers, statuses, report):
    placed, ordered, seen_numbers = {}, [], set()
    for index, chapter in enumerate(chapters):
        where = f"chapters[{index}]"
        if not isinstance(chapter, dict):
            report.error(where, "each chapter must be a JSON object.")
            continue
        number = chapter.get("number")
        if isinstance(number, bool) or not isinstance(number, int):
            report.error(where, "'number' must be a whole number.")
            continue
        where = f"chapter {number}"
        if number in seen_numbers:
            report.error(where, "this chapter number is used twice.")
            continue
        seen_numbers.add(number)
        kind = chapter.get("type")
        if kind not in CHAPTER_TYPES:
            report.warn(where, f"type is '{kind}'; expected one of: {', '.join(CHAPTER_TYPES)}.")
        if kind == "paper":
            paper_id = chapter.get("paper_id")
            if paper_id not in statuses:
                report.error(where, f"paper_id '{paper_id}' does not match any paper id.")
            elif paper_id in placed:
                report.error(where, f"paper '{paper_id}' is already placed in chapter {placed[paper_id]}.")
            else:
                placed[paper_id] = number
            check_enum(report, where, "linking", chapter.get("linking"), LINKING_STATES)
        ordered.append((number, kind, chapter))

    for index, paper in enumerate(papers):
        if not isinstance(paper, dict) or not known(paper.get("id")):
            continue
        paper_id, where = paper["id"], f"papers[{index}] ({paper['id']})"
        if paper_id not in placed:
            report.error(where, f"not placed in any chapter. Add a chapter with type 'paper' and "
                         f"paper_id '{paper_id}'.")
        elif known(paper.get("chapter")) and paper.get("chapter") != placed[paper_id]:
            report.error(where, f"chapter is {paper.get('chapter')}, but chapter {placed[paper_id]} "
                         "holds this paper.")

    kinds = {kind for _, kind, _ in ordered}
    if "introduction" not in kinds:
        report.warn("chapters", "no introduction chapter; examiners expect a critical introduction.")
    if not kinds & {"conclusion", "discussion"}:
        report.warn("chapters", "no conclusion or discussion chapter; examiners expect a synthesis "
                    "that draws the papers together.")

    seen_paper, previous_kind = False, None
    for number, kind, chapter in sorted(ordered, key=lambda item: item[0]):
        if kind == "paper":
            linking = chapter.get("linking")
            if seen_paper and previous_kind != "linking" and linking not in ("drafted", "done"):
                if linking == "not-needed":
                    report.warn(f"chapter {number}", "linking is marked not-needed; examiners expect "
                                "material that links each paper to the one before. Confirm this is intended.")
                else:
                    report.warn(f"chapter {number}", "no linking material yet. Add a preface or a "
                                "linking chapter before it.")
            seen_paper = True
        previous_kind = kind


def cell(value):
    return "?" if value in (None, "") else str(value).replace("|", "/")


def render(sections, report, strict, failed):
    title = sections["thesis"].get("title")
    source = sections["rules"].get("source")
    lines = [
        f"# Thesis plan check: {title if known(title) else '(untitled)'}",
        "",
        f"Result{' (strict)' if strict else ''}: {'FAIL' if failed else 'PASS'}. "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s), "
        f"{len(report.todos)} open TODO item(s).",
        f"Rules source: {source if known(source) else 'not recorded'}",
    ]
    for heading, items in (("Errors", report.errors), ("Warnings", report.warnings)):
        lines += ["", f"## {heading}", ""]
        lines += [f"{number}. {item}" for number, item in enumerate(items, start=1)] or ["None."]
    lines += ["", "## Open TODO items", ""]
    lines += [f"- {path}" for path in report.todos] or ["None."]
    lines += ["", "## Papers", "",
              "| ID | Chapter | Status | Candidate position | Statement | Permission |",
              "|---|---|---|---|---|---|"]
    for paper in sections["papers"]:
        if not isinstance(paper, dict):
            continue
        statement = paper.get("contribution_statement")
        permission = paper.get("permission")
        lines.append("| {} | {} | {} | {} | {} | {} |".format(
            cell(paper.get("id")), cell(paper.get("chapter")), cell(paper.get("status")),
            cell(paper.get("candidate_author_position")),
            cell(statement.get("status") if isinstance(statement, dict) else None),
            cell(permission.get("status") if isinstance(permission, dict) else None)))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a thesis-plan.json file against the rules it records.")
    parser.add_argument("plan", help="path to thesis-plan.json")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as failures (use for the final pre-submission check)")
    args = parser.parse_args(argv)

    try:
        with open(args.plan, encoding="utf-8") as handle:
            plan = json.load(handle)
    except FileNotFoundError:
        print(f"Plan not found: {args.plan}. Copy assets/thesis-plan.template.json to start one.",
              file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"{args.plan} is not valid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}.",
              file=sys.stderr)
        return 2
    if not isinstance(plan, dict):
        print(f"{args.plan} must contain a JSON object at the top level.", file=sys.stderr)
        return 2

    report = Report()
    sections = {}
    for key, kind in (("thesis", dict), ("rules", dict), ("papers", list), ("chapters", list)):
        value = plan.get(key)
        if not isinstance(value, kind):
            report.error(key, f"missing or not a JSON {'object' if kind is dict else 'list'}. "
                         "Start from assets/thesis-plan.template.json.")
            value = kind()
        sections[key] = value

    collect_todos(plan, "", report)
    check_rules(sections["rules"], report)
    statuses, total = check_papers(sections["papers"], sections["rules"], report)
    check_counts(statuses, total, sections["rules"], report)
    check_chapters(sections["chapters"], sections["papers"], statuses, report)

    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    print(render(sections, report, args.strict, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
