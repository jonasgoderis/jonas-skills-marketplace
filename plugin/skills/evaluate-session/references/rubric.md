# Rubric — how a session is graded

Read alongside `best-practices.md`, which defines BP-01 through BP-19 and the
observability tier of each. This file governs how evidence becomes a grade.

## What is being graded

How the session was driven, not what it produced. A session that shipped working
code through six vague prompts and no review graded badly; a session that
carefully scoped a task which then turned out to be unnecessary graded well. The
output has its own feedback loop — this one is about method.

The subject is the person's side of the conversation. Do not grade the
assistant's responses, and do not grade the codebase.

## Evidence rules

Every finding cites a specific practice identifier and a specific moment. A
finding that cannot point at something in the digest is not a finding.

- Quote or reference the turn the judgement rests on. "BP-06, turn 4" is
  checkable; "prompts were often vague" is not.
- Grade only what the digest contains. It carries the user's messages verbatim
  and the shape of what followed — tool names, counts, files touched, commits,
  compaction events. It deliberately does not carry assistant prose, tool output
  or file contents. Absence of evidence is not evidence of a failing.
- Do not infer intent. A short prompt is not automatically a vague one; a long
  one is not automatically specific.

## Observability rules

These exist because the alternative — quietly penalising whatever the transcript
cannot show — produces a grade that punishes the wrong things and cannot be
argued with.

- **Direct** practices are graded normally.
- **Indirect** practices are graded only on the signals named in their entry, and
  the finding says what the signal was. Where the signal is absent, the practice
  is unobserved, not failed.
- **Structural** practices are decided from the filesystem facts in the digest,
  never from the conversation. They describe the project, so they are identical
  for every session in that project and should never appear as a focus item —
  report them once, as a standing note.
- A practice the session gave no occasion to exercise is **not applicable**. Most
  sessions contain no irreversible decision (BP-17) and no natural place for an
  example (BP-07). Listing these as failures is the most common way a rubric like
  this becomes noise.

## Bands

Five bands. The scale is deliberately coarse: a judge asked to choose between
eleven grades will not give the same answer twice on the same evidence, and an
unstable grade is worse than a vague one.

| Band | Meaning |
| --- | --- |
| **A+** | Exceptional. Several practices exercised deliberately and visibly, none neglected. Rare — if it is being awarded often, the rubric has drifted. |
| **A** | Strong throughout. Minor room to improve, nothing that cost anything. |
| **B** | Solid. One or two practices were neglected in ways that visibly cost time, rework or clarity. |
| **C** | Mixed. Several neglected, or one neglected badly enough to shape the whole session. |
| **D** | Poor. The session worked against itself — sprawling scope, no verification, no checkpoints. |

Grade on what the session cost itself, not on a count of ticked practices. Four
practices missed with no consequence is a better session than one missed that
caused an hour of rework.

## The report

Two focus items, never more. A list of nine faults is skimmed and nothing
changes; two are actionable. Choose the two with the largest actual cost in this
session, not the two most clearly documented.

Practices done well are listed by identifier and name only. The purpose is
recognition, not a second essay — and it keeps the focus items prominent.

Say what is not applicable rather than silently omitting it, so the reader can
see the grade did not rest on it.

## Tone

Write to someone competent who wants to get better, and who will read this at the
end of a long day.

- State what happened and what it cost. Skip the encouragement and skip the
  scolding.
- No padding. A clean session gets a short report.
- Never invent a fault to fill the second focus slot. One focus item, or none, is
  a legitimate result and a more honest one than a manufactured second.
