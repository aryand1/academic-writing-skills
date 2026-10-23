# Institutional rules

## Contents
- Questions to answer from the policy
- Recording rules in thesis-plan.json
- Before submission

Rules for theses by publication differ between universities, faculties, and degrees, and they change over time. Answer the questions below from the user's own policy documents. When the policy does not answer a question, record TODO and suggest the user ask the graduate school or thesis examinations office.

## Questions to answer from the policy

Which papers can count:
1. How many papers are required or expected, and who decides (faculty, panel, supervisor)?
2. Which statuses count: published, accepted, submitted, in preparation? Is there a minimum number published or accepted?
3. Must the research be done during candidature? Are papers from before enrollment allowed?
4. Must the candidate be first or principal author? How are equal-first and second-author papers treated?
5. Do conference papers, book chapters, or preprints count?
6. May a paper also appear in someone else's thesis, such as a co-author's? Some policies forbid this or require a declaration.
7. Are there venue requirements, such as peer review or ranked journals?

How papers are presented:
8. Must papers appear exactly as published, may they be reformatted into the thesis style, or must they be?
9. Which version goes in: version of record, accepted manuscript, or either?
10. One reference list for the thesis, or one per paper?
11. Which components are required: critical introduction, literature review chapter, linking sections, methods chapter, synthesis conclusion?
12. Word or page limits, and do the papers count toward them?

Statements and forms:
13. Contribution statement: which form, what content (roles, percentages, or narrative), where it goes, and who signs.
14. Other declarations: originality, a list of publications, the status of each paper.
15. Copyright: what evidence of permission does the university want, and in what form?

Deposit:
16. Is the final thesis deposited open access? Can a chapter be embargoed, or replaced in the public copy by a citation and link?

## Recording rules in thesis-plan.json

Put the rules the validator can test in the `rules` object. Use null when the policy sets no such rule and "TODO" when the answer is not known yet. The validator enforces only filled-in rules and lists every TODO.

| Field | Value |
|---|---|
| `source` | Policy name, section, and link |
| `min_papers`, `max_papers` | Whole numbers, or null |
| `allowed_statuses` | List drawn from published, accepted, submitted, in-preparation |
| `min_published_or_accepted` | Whole number, or null |
| `candidate_first_author_required` | true or false |
| `papers_must_be_from_candidature` | true or false |
| `contribution_statement_required` | true or false |
| `co_author_signatures_required` | true or false |
| `reformatting` | "as-published", "allowed", or "required" |
| `notes` | Every other rule, as plain sentences |

## Before submission

- [ ] `validate_plan.py --strict` passes, or each remaining warning has a recorded reason
- [ ] Each co-authored paper has a contribution statement in the required form, signed if required
- [ ] Each published or accepted paper has a confirmed permission record with a source, and the required notice at the chapter start
- [ ] Each paper chapter gives the full citation and current status (update papers accepted since the plan was made)
- [ ] The critical introduction states the central claim and maps research questions to chapters
- [ ] Every paper chapter after the first has linking material
- [ ] The conclusion synthesizes across papers instead of summarizing them one by one
- [ ] Repeated text is trimmed or noted, and a thesis-level abbreviations list exists
- [ ] Material the papers left out (failed approaches, method detail, supplementary data) appears where useful
- [ ] The public deposit version meets each publisher's conditions
