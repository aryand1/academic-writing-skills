# Academic writing skills

Agent Skills for academic research and writing, packaged as a Claude Code plugin marketplace. The first plugin is `thesis-by-publication`.

## thesis-by-publication

A thesis by publication (also called a PhD by publication or an article-based dissertation) is examined as one piece of work, not a stack of papers. Universities expect a critical introduction, sections that link the papers, a conclusion that synthesizes them, a statement of the candidate's contribution to each co-authored paper, and little repetition. This skill helps Claude with that work:

- It builds a thesis plan from the candidate's papers and their university's own rules, then checks the plan with a script.
- It drafts linking sections, the synthesis conclusion, and the critical introduction.
- It drafts contribution statements with CRediT roles and tracks copyright permissions.
- It finds text repeated across papers and conflicting acronym definitions with scripts.

It never fills in a university rule, DOI, author order, co-author approval, or permission from memory. Unknown values stay marked TODO.

## Install

Claude Code, as a plugin:

```
/plugin marketplace add aryand1/academic-writing-skills
/plugin install thesis-by-publication@academic-writing-skills
```

Claude Code, as a personal skill without the plugin:

```
cp -r plugins/thesis-by-publication/skills/assembling-thesis-by-publication ~/.claude/skills/
```

Claude.ai: zip the `assembling-thesis-by-publication` folder and upload it in the Skills section of your settings. The scripts need code execution turned on.

## Try it

- "I'm doing a PhD by publication with four papers. Here is our graduate school policy. Set up my thesis plan and tell me what's missing."
- "Check my three paper chapters for repeated text and acronym problems."
- "Write the linking preface between my chapter 3 and chapter 4."
- "Draft the authorship statements my co-authors need to sign."

## Run the scripts directly

The scripts need Python 3.8 or later and only the standard library. PDF input also needs `pip install pypdf`, or convert the PDF first with `pdftotext -layout paper.pdf paper.txt`.

```
cd plugins/thesis-by-publication/skills/assembling-thesis-by-publication
python scripts/validate_plan.py assets/thesis-plan.template.json
python scripts/find_overlap.py evals/files/
python scripts/check_acronyms.py evals/files/
```

## Testing

- Run `claude plugin validate .` from the repository root to check both manifests.
- `evals/evals.json` holds three test scenarios in the format from Anthropic's skill authoring guide.
- The sample papers in `evals/files/` contain one known repeated passage and three known acronym problems, so the script output can be checked by eye.
- Try the skill with each model you plan to use (Haiku, Sonnet, Opus), since smaller models may need more guidance.

## Limits

- University rules vary and change. The skill depends on the policy the user provides.
- Permission guidance is general and not legal advice. The publisher's agreement and the university's copyright office decide.
- The scripts are heuristics. Overlap matching finds identical wording, not paraphrase. Acronym detection finds "long form (SHORT)" and "SHORT (long form)" patterns, not every definition style.

## License

MIT. See [LICENSE](LICENSE).
