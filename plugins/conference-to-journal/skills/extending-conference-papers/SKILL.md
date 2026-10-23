---
name: extending-conference-papers
description: Plans and checks the journal version of a published conference paper. Compares the two versions section by section with a bundled script, estimates the share of new text against the target venue's threshold, checks the changes publishers require (different title, rewritten abstract, citation and disclosure of the conference paper), and drafts the summary of differences, the introduction disclosure, and the cover letter paragraph. Use whenever someone is extending, expanding, or turning a conference, workshop, or proceedings paper into a journal article, is invited to submit an extended version to a special issue, asks how much new material a journal version needs (such as ACM's 25% or Springer's 30% guideline), or must write a summary of differences, even if they never say 'extension'. Not for porting a rejected paper to another venue or for general similarity-report questions about unrelated papers.
---

# Extending a conference paper into a journal article

Journals accept extended conference papers when the journal version adds real contributions and discloses the conference paper openly. Rules differ by publisher, journal, and special issue. Some set a share of new material (ACM's guideline is 25%, Springer proceedings and several other venues use 30%, and some IEEE venues ask for more), and most ask for a different title, a citation of the conference paper, and a statement of what is new. This skill plans the extension, measures how the draft differs from the conference paper, and drafts the documents editors ask for.

## Ground rules

- The target venue's current policy decides. [references/venue-policies.md](references/venue-policies.md) is a starting point with sources, but journals and special-issue calls often set their own rules, and publishers change them. Verify the current policy and record its source and the date checked.
- Treat a percentage as a floor, not the goal. Editors judge new contributions (results, methods, analysis, data), not new words. The comparison script measures text, and reworded old text counts as new there, so never present its number as proof of compliance.
- Disclose the conference paper fully: cite it, say how the journal version differs, and use the venue's disclosure format. Never suggest rewording reused text to lower a similarity score. It adds nothing and can look like concealment. If asked, explain why and help with disclosure instead.
- Do not invent results. New content comes from the authors; mark gaps as TODO.

## Choose the task

| Request | Start at |
|---|---|
| Planning an extension that is not written yet | Steps 1 to 3 |
| Checking a draft journal version | Steps 1, 2, 4, and 5 |
| Writing the summary of differences, disclosure, or cover letter | Steps 4 and 6 |
| "How much new material does venue X need?" | Step 1 |

## Workflow

Copy this checklist into the response and track progress:

```
Extension progress:
- [ ] Step 1: Find the venue's rules
- [ ] Step 2: Collect both versions
- [ ] Step 3: Plan the new contribution
- [ ] Step 4: Compare the versions
- [ ] Step 5: Check the required changes
- [ ] Step 6: Draft the disclosure documents
- [ ] Step 7: Final check
```

### Step 1: Find the venue's rules

Identify two publishers. The conference paper's publisher controls reuse rights, and some (such as Springer for its proceedings) set an extension rule. The journal's publisher sets the threshold and the required items. Start from references/venue-policies.md, then check the journal's current author guidelines and any special-issue call. With web search, search for the journal's name plus "extended conference paper"; otherwise ask the user for the link or text. Record the threshold (if any), every required item, the source, and the date checked. Confirm that the journal accepts extended conference papers at all.

### Step 2: Collect both versions

Get the published conference paper and the journal draft, as source files if possible (.tex, .docx, .md), since PDF text extraction is less reliable. Ask for the conference reviews too: requests the page limit forced the authors to defer are good extension material. If there is no journal draft yet, go to Step 3.

### Step 3: Plan the new contribution

Read [references/extension-guide.md](references/extension-guide.md). List candidate additions from the conference paper's limitations and future work, the reviews, material cut for the page limit, and new data the authors have. Mark each as a contribution or an elaboration. Write a two-sentence statement of what is new. If the only honest answer is "more detail", tell the user plainly that the extension may not meet the venue's bar.

### Step 4: Compare the versions

Run the comparison with the threshold from Step 1 (leave out `--threshold` if the venue sets none):

```bash
python scripts/compare_versions.py path/to/conference.tex path/to/journal.tex --threshold 30
```

The report shows each journal section's carried-over and new text with the conference section it came from, how much of each conference section was kept, an overall new-text estimate, and checks on the title, abstract, disclosure sentence, and citation. Add `--conference-doi DOI` to check that the DOI appears. Read the numbers alongside the authors' description of what is new: a section can be mostly new text and still add nothing, and a reused section can sit next to a new result.

### Step 5: Check the required changes

Check each item recorded in Step 1 against the draft and the report: a different title, a rewritten abstract, a disclosure in the introduction (and a footnote or acknowledgment if the venue wants one), a citation in the references, related work updated with papers published since the conference, new contributions listed in the introduction, and the files the venue wants (conference copy, summary of differences, cover letter). Report each item as done, missing, or needing the authors.

### Step 6: Draft the disclosure documents

Use [references/templates.md](references/templates.md) for the introduction disclosure, the footnote or acknowledgment, the statement of the increment, the summary of differences, and the cover letter paragraph. Build the summary of differences from the Step 4 report and the authors' description of each change. Every number and section name in these documents must match the paper and the report.

### Step 7: Final check

After the authors revise, run the comparison again. Confirm that the summary of differences still matches the final sections and numbers, and list what still needs the authors: new results, permissions, or uploads.

## Script

`scripts/compare_versions.py` needs Python 3.8 or later and only the standard library. Run it from this skill's directory, or prefix the path with it. Run it instead of reading it; read it only if it fails in an unexpected way.

| Option | Meaning |
|---|---|
| `--threshold N` | Required share of new material, in percent; the report says whether the text estimate meets it |
| `--min-words N` | Shortest run of identical words counted as carried over (default 8) |
| `--conference-doi DOI` | Also checks that this DOI appears in the journal text |
| `--json OUT` | Writes the full results as JSON |

The script reads .txt, .md, .tex, and .docx. PDF needs the optional `pypdf` package, or convert it first with `pdftotext -layout paper.pdf paper.txt`. Front matter, keywords, references, and acknowledgments are left out of the counts. If the report shows a single section called Body, no headings were found: ask for source files, or add Markdown headings (`## Introduction`) to a text copy.

## Reference files

- [references/venue-policies.md](references/venue-policies.md): sourced table of publisher and journal rules, and how to verify them.
- [references/extension-guide.md](references/extension-guide.md): what counts as new material, finding the extension, required changes, reused text, reuse rights, and special cases.
- [references/templates.md](references/templates.md): disclosure, statement of the increment, summary of differences, cover letter, and an example.
