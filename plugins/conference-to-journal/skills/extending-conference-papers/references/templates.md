# Templates

## Contents
- Introduction disclosure
- Title-page footnote or acknowledgment
- Statement of the increment
- Summary of differences
- Cover letter paragraph
- Example summary of differences

Fill every bracket from the papers, the comparison report, or the authors. Write TODO where the information is missing.

## Introduction disclosure

```
This article extends our earlier conference paper [N], which [one sentence on what it did].
Compared with that paper, this article makes the following new contributions:
(1) [new contribution, with its section];
(2) [new contribution, with its section];
(3) [new contribution, with its section].
[Optional: Sections X and Y revise and expand material from [N].]
```

## Title-page footnote or acknowledgment

```
A preliminary version of this work appeared in [full citation of the conference paper, with DOI].
```

## Statement of the increment

For venues that ask for an explicit statement (for example, extensions of Springer proceedings papers):

```
This journal version extends [conference paper citation] with [new results / new methods / new evaluation].
Specifically, it adds [list], and it revises [list].
```

## Summary of differences

Use the venue's format if it gives one. Otherwise:

```
Summary of differences between
  Conference paper: [full citation, DOI]
  Journal submission: [title]

1. Overview
[Two sentences: what the journal version adds and why it matters.]

2. New material
| Journal section | What is new | Type (new results, new method, new analysis, new data, elaboration) |
|---|---|---|

3. Revised material
| Journal section | Conference section | What changed |
|---|---|---|

4. Unchanged material
[Sections carried over with minor edits, and why they are kept.]

5. Text measure
[From compare_versions.py: about X% of the counted journal text is new or reworded,
measured in runs of N identical words. This is a text measure; section 2 lists the
substantive additions.]
```

## Cover letter paragraph

```
This manuscript is an extended version of our paper [citation], published in [venue] in [year].
The journal version adds [main new contributions in one sentence]. A summary of the differences
[is attached / is uploaded as a supplementary file], and [the conference paper is included for reference].
```

## Example summary of differences

Input from the authors: the conference paper proposed a cache replacement policy and evaluated it in simulation. The journal version adds a proof of a competitive-ratio bound, an evaluation on a production trace, and a sensitivity study.

```
1. Overview
The journal version proves a bound on the policy's competitive ratio and evaluates the policy
on a production storage trace, which the conference paper listed as future work.

2. New material
| Journal section | What is new | Type |
|---|---|---|
| 4 Analysis | Proof of the competitive-ratio bound | New theory |
| 6.3 Production trace | Evaluation on [TODO: trace name and source] | New data |
| 6.4 Sensitivity | Effect of cache size and warm-up period | New analysis |

3. Revised material
| Journal section | Conference section | What changed |
|---|---|---|
| 1 Introduction | 1 Introduction | Contributions list updated; disclosure added |
| 2 Related work | 2 Related work | Adds work published since the conference paper |

4. Unchanged material
Section 3 (policy description) is carried over with minor edits so the article reads on its own.
```

The example uses only what the authors supplied, marks the missing trace details as TODO, and separates new contributions from revisions.
