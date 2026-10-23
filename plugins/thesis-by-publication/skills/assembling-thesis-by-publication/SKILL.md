---
name: assembling-thesis-by-publication
description: Plans, checks, and writes the connecting material for a thesis by publication (also called a PhD by publication, article-based or paper-based dissertation, compilation thesis, or thesis with publications). Builds a chapter plan from the candidate's papers and university rules, drafts the critical introduction, linking sections, and synthesis conclusion, prepares co-author contribution statements and copyright permission records, and runs scripts that find text repeated across papers and conflicting acronym definitions. Use whenever someone is turning published, accepted, or submitted papers into a thesis or dissertation, asks how to link or bridge paper chapters, needs authorship statements for a thesis, or asks whether a paper-based thesis meets graduate school rules, even if they never say 'thesis by publication'. Not for conventional monograph theses or for turning a thesis chapter into a journal article.
---

# Assembling a thesis by publication

Examiners judge a thesis by publication as one piece of work, so binding the papers together is not enough. Universities expect a critical introduction, sections that link the papers, a conclusion that synthesizes them, a statement of the candidate's contribution to each co-authored paper, and little repetition. This skill covers that connecting layer and the paperwork around it.

## Ground rules

- The university's own policy is the authority. Rules differ on how many papers count, which statuses count, first authorship, reformatting, and required statements. Get the policy (link, PDF, or pasted text) before applying any rule, and record where each rule came from. Do not fill a rule from memory or from another university.
- Mark anything unknown as TODO. Never invent a DOI, venue, author order, contribution role, co-author approval, or permission. A wrong detail in a signed statement or permission record causes problems at submission.
- Leave the text of published papers alone unless the user decides otherwise. Put corrections and updates in the chapter preface or a note, unless the rules allow edited versions and the user wants one. Silent edits create a version that matches neither the journal nor the thesis record.
- Present contribution statements as drafts. They describe what the candidate reports, and co-authors must confirm them.

## Choose the task

Start at the step that matches the request. Partial requests are common, so do not force the full workflow.

| Request | Start at |
|---|---|
| Putting the whole thesis together, or a new plan | Step 1 |
| "Does my thesis meet the rules?" | Steps 1, 2, and 7 |
| Repeated text or acronym consistency across chapters | Step 4 |
| An introduction, linking section, or conclusion | Step 5 (needs each paper's role from Step 3) |
| Contribution statements or copyright permissions | Step 6 |

## Workflow

Copy this checklist into the response and track progress:

```
Thesis assembly progress:
- [ ] Step 1: Collect the rules and the papers
- [ ] Step 2: Build and validate thesis-plan.json
- [ ] Step 3: Set the argument and the chapter order
- [ ] Step 4: Check repeated text and acronyms across papers
- [ ] Step 5: Draft the connecting material
- [ ] Step 6: Prepare contribution statements and permissions
- [ ] Step 7: Final check against the rules
```

### Step 1: Collect the rules and the papers

Collect the institution's thesis-by-publication policy, the details of each paper (title, authors and the candidate's position, venue, status, DOI), and the paper files if available. Use [references/institutional-rules.md](references/institutional-rules.md) for the questions the policy must answer. When the policy is silent on a question, record TODO and suggest asking the graduate school or thesis examinations office.

### Step 2: Build and validate thesis-plan.json

Copy [assets/thesis-plan.template.json](assets/thesis-plan.template.json) to `thesis-plan.json` next to the user's thesis files and fill it from Step 1. Then run:

```bash
python scripts/validate_plan.py path/to/thesis-plan.json
```

The report lists errors (rule breaches, broken references), warnings (missing statements, unchecked permissions, missing linking material), and open TODO items. Fill what the user can answer, ask about the rest, and run it again until no new errors appear. State rule breaches plainly. A second-author paper under a first-author rule needs a ruling from the graduate school, not a workaround.

### Step 3: Set the argument and the chapter order

Write the thesis's central claim in one or two sentences and store it in `thesis.central_claim`. Give each paper a `role_in_argument`: the question it answers and what later chapters take from it. Order chapters by the argument, not by publication date. If a paper does not serve the claim, say so. The fix may be a broader claim, an added chapter, or moving the paper to an appendix if the rules allow.

List what the papers left out that examiners expect: a deeper literature review, method detail cut for word limits, approaches that failed, and supplementary data. Decide where each goes (introduction, linking section, methods chapter, or appendix).

### Step 4: Check repeated text and acronyms across papers

Papers written to stand alone repeat introductions and methods, and they often define the same acronym differently. Run both scripts on all paper files and any drafted chapters:

```bash
python scripts/find_overlap.py path/to/chapters/
python scripts/check_acronyms.py path/to/chapters/
```

Agree with the user on how to handle each finding. The options depend on `rules.reformatting` in the plan:

- `as-published`: keep the text, add a reading note to the chapter preface (for example, "Section 2 repeats the method in Chapter 3"), and reconcile acronyms in a thesis-level abbreviations list.
- `allowed` or `required`: trim repeated passages and cross-reference, or move shared methods into one chapter. Unify acronyms and record each change in the chapter preface.

### Step 5: Draft the connecting material

Read [references/connecting-material.md](references/connecting-material.md) for structure, templates, and an example. Draft the linking sections first, because they force the argument into the open. Draft the synthesis conclusion next and the critical introduction last, so the introduction promises exactly what the thesis delivers. Match the candidate's spelling, citation style, and discipline conventions. Every statement about a paper's content must come from the paper or the user.

### Step 6: Prepare contribution statements and permissions

Read [references/authorship-and-permissions.md](references/authorship-and-permissions.md). Use the university's own form when one exists. Otherwise draft one statement per co-authored paper using CRediT roles, and one permission record per published or accepted paper. Update `contribution_statement` and `permission` in the plan as each item moves forward.

### Step 7: Final check against the rules

Run the validator in strict mode, which treats warnings as failures:

```bash
python scripts/validate_plan.py path/to/thesis-plan.json --strict
```

Then work through "Before submission" in references/institutional-rules.md. Report what passes, what fails, and what still needs a person: signatures, permissions, or a ruling from the graduate school.

## Scripts

The scripts need Python 3.8 or later and only the standard library. Run them from this skill's directory, or prefix the script paths with it. Run them instead of reading them; read a script only if it fails in an unexpected way.

| Script | Purpose | Output |
|---|---|---|
| `scripts/validate_plan.py PLAN [--strict]` | Checks thesis-plan.json against the rules it records | Report; exit code 0 pass, 1 fail, 2 unreadable plan |
| `scripts/find_overlap.py PATH... [--min-words 12] [--json OUT]` | Finds runs of 12 or more identical words shared by two files | Summary per file pair, then passages with line numbers |
| `scripts/check_acronyms.py PATH... [--json OUT]` | Compares "long form (SHORT)" definitions across files | Conflicts, uses without a definition, never-defined candidates |

Each PATH can be a file or a folder. The scripts read .txt, .md, .tex, and .docx. For .docx files, a line in the output is a paragraph. PDF works only with the optional `pypdf` package; otherwise the script skips the PDF and prints how to convert it. Ask for source files first, since PDF text extraction is less reliable. If the user pasted text, save each paper to its own .txt file before running a script. If the thesis uses the LaTeX glossaries package, include the glossary file in the acronym check, because its definitions are not in the chapters.

## Reference files

- [references/institutional-rules.md](references/institutional-rules.md): questions to answer from the policy, how to record rules in the plan, and the before-submission checklist.
- [references/connecting-material.md](references/connecting-material.md): critical introduction, linking sections with an example, synthesis conclusion, and handling repeated text.
- [references/authorship-and-permissions.md](references/authorship-and-permissions.md): contribution statements, CRediT roles, permission paths, trackers, and message templates.
