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
- **Rework is not by itself evidence against a prompt.** A session that went
  wrong and had to be redone may have gone wrong for reasons the user could not
  have prevented. Before charging rework to a practice, both of these must hold:
  the missing information was the user's to give, and you can quote the words
  that were missing. If you cannot name what they should have said, there is no
  finding.
- **Anything the assistant chose is never a finding against the user.** A
  mechanism, a design, a file layout, a tool, an approach — if the user delegated
  it, the fact that it later needed changing is the assistant's outcome, not a
  gap in their prompt. This is the single most likely way to grade the user for
  someone else's mistake, because the digest strips the assistant's own words and
  leaves the user's messages as the only text available to explain anything.
- **Most of what the digest records is the assistant acting.** `assistant_activity`
  holds tool calls, commits, test runs and subagent launches. The user cannot do
  any of those; they can only ask. Read that block as what happened *after* a
  request, never as something the user did or failed to do.

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
  for every session in it and are never a focus item. They may be listed as done
  well; anything worth raising goes in a single **Standing note** line.
- A practice the session gave no occasion to exercise is **not applicable**. Most
  sessions contain no irreversible decision (BP-17) and no natural place for an
  example (BP-07). Listing these as failures is the most common way a rubric like
  this becomes noise.
- Where an entry names no signal the digest actually carries, the practice is
  **unobserved**. Do not substitute a proxy. Change size is not evidence about
  whether a diff was read.

## Bands

Five bands. The scale is deliberately coarse: a judge asked to choose between
eleven grades will not give the same answer twice on the same evidence, and an
unstable grade is worse than a vague one.

A band is decided by **countable costs**, not by an impression. A cost is an
episode you can point at: the user had to repeat a request, correct a
misunderstanding their own wording caused, or ask for something to be redone that
a clearer instruction would have got right first time. Anything you cannot point
at does not count.

| Band | Meaning |
| --- | --- |
| **A+** | No costs, and at least two practices visibly exercised on purpose. Rare — if it is being awarded often, the rubric has drifted. |
| **A** | No costs, or one small enough that the session absorbed it without a detour. |
| **B** | One or two costs. |
| **C** | Three or four costs, or one that redirected the whole session. |
| **D** | Five or more, or the session never established what it was doing. |

Where the evidence supports two adjacent bands, take the higher one. The grade is
advice, and an unfairly harsh one is ignored — which costs more than a generous
one does.

Grade on what the session cost itself, not on a count of ticked practices. Four
practices missed with no consequence is a better session than one missed that
caused an hour of rework.

## The report

Two focus items, never more. A list of nine faults is skimmed and nothing
changes; two are actionable. Choose the two with the largest actual cost in this
session, not the two most clearly documented.

**One behaviour, one focus item.** Several practices describe the same mistake
from different angles — a single sprawling, uncommitted, un-iterated stretch of
work touches BP-03, BP-05, BP-09 and BP-16 at once. Report it once, under the
practice that fits it best. The second focus item has to rest on a different
episode, or there is no second focus item.

Practices done well are listed by identifier only, matching the template. The
purpose is recognition, not a second essay — and it keeps the focus items
prominent. Do not list a practice as done well when the only evidence is that its
failure case did not occur.

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
