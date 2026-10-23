# Connecting material

## Contents
- Critical introduction
- Linking sections
- Example linking preface
- Synthesis conclusion
- Handling repeated text
- Voice and accuracy

The papers carry the findings. The connecting material carries the thesis. It shows that the papers answer one set of questions, that the candidate knows the field beyond what journal word limits allowed, and that the whole adds up to more than its parts.

## Critical introduction

Write it last. Adapt these parts to the discipline:

1. The problem and why it matters, in the field's own terms.
2. A literature review deeper than any single paper's. Papers have short reviews, and examiners want to see command of the field. Some theses put this in its own chapter.
3. The gap and the central claim of the thesis, in one or two sentences.
4. Research questions mapped to chapters:

   | Research question | Answered in | Paper status |
   |---|---|---|
   | RQ1: ... | Chapter 3 (Paper 1) | Published |

5. The overall design or methods, if the papers share one, and why it fits the questions.
6. Thesis structure: a short paragraph per chapter, including linking and non-paper chapters.
7. A publication list with full citations and status, and a pointer to the contribution statements.

## Linking sections

A linking section can be a chapter preface (half a page to two pages before a paper), a short chapter between papers, or bridging paragraphs at the end of the previous chapter. Use the form the rules and the user prefer, and keep it consistent across the thesis.

Each linking section answers these questions, in roughly this order:

1. Where are we in the argument? Name the research question this chapter addresses.
2. What did the previous chapter find or leave open that makes this chapter necessary?
3. What does this paper do? Give its full citation, its status, and the version included.
4. What changed since the paper was written? Corrections, newer results, later literature, responses to criticism, and changes in notation or terms. Skip this if nothing changed.
5. How should the reader approach it? Point out repeated material ("Section 2 repeats the setup from Chapter 3") and where the contribution statement is.

Do not restate the abstract. The reader is about to read the paper; the preface explains why it is here.

## Example linking preface

Input from the candidate: Chapter 2 (published) surveyed 412 secondary teachers and found that those who used formative quizzes weekly reported higher student engagement, but the survey could not say why. Chapter 3 (under review) interviewed 18 of those teachers. After submission, a second coder joined, and two themes were recoded and renamed.

Output:

> Preface to Chapter 3
>
> Chapter 2 found that teachers who used formative quizzes every week reported higher student engagement than those who did not. A survey can show that link but not the reasons for it, and the reasons matter for anyone designing teacher training. This chapter takes up that question (RQ2): how do teachers explain the link between frequent quizzing and engagement?
>
> The chapter is the manuscript submitted to [journal, TODO: confirm] and now under review. It reports interviews with 18 of the survey respondents. Its account of quizzing as a feedback routine is the basis for the training framework in Chapter 4.
>
> One change since submission: after a second coder joined the project, two themes were recoded and renamed. This chapter uses the new names, and Appendix C maps them to the names in the submitted manuscript. Section 2 summarizes the survey design from Chapter 2 and can be skipped. My contribution to this paper is set out in the statement at the start of the chapter.

The example names the open question, places the paper in the argument, uses only numbers the candidate supplied, marks the missing citation as TODO, and discloses the change made after submission.

## Synthesis conclusion

Examiners look here for the thesis's contribution. Do not summarize the papers one at a time. Instead:

1. Answer each research question, drawing on every paper that bears on it.
2. State findings that appear only when the papers are read together: a pattern across studies, a method validated in one paper and applied in another, or a tension between two results and how it resolves.
3. Address inconsistencies between papers openly, for example a later paper revising an earlier estimate.
4. State the contribution to knowledge of the thesis as a whole.
5. Give limitations of the whole program, not a repeat of each paper's limitations.
6. Suggest future work that follows from the combined findings.

## Handling repeated text

Use the find_overlap.py and check_acronyms.py output with the plan's `rules.reformatting` value.

| Rules say | Repeated introduction text | Repeated methods | Conflicting acronyms |
|---|---|---|---|
| as-published | Keep; note in the preface | Keep; note in the preface | Reconcile in the thesis abbreviations list |
| allowed or required | Trim and cross-reference | Keep in the first paper, or move to a methods chapter, and cross-reference | Unify; record changes in the preface |

When trimming, keep each chapter readable on its own. Replace cut text with a one-line pointer instead of leaving a gap.

## Voice and accuracy

- Write in the candidate's voice and spelling convention, and use the thesis citation style (or each paper's own style when papers stay as published).
- Follow discipline norms for first person and tense.
- Mark any claim that needs a citation the papers do not already provide with [CITATION NEEDED].
- Keep every number, date, and result to what the papers or the candidate state. If the text needs a figure that is not available, write TODO.
