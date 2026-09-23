# evaluate-session — calibration against a negative control

**2026-09-23.** Settles the one item that was blocking release: whether the
rubric can still mark a session down, or whether everything now lands at A.

**Result: it can. A session built to go badly graded C in six runs out of six.
No threshold is needed and the bands are unchanged.**

## The question

The rubric resolves ambiguity upward on purpose, and the last round of fixes
moved more practices into "not applicable" and "unobserved". Both changes push in
the same direction. The misattribution fix had been verified on a single real
session, where it moved a B to an A — which is consistent with the fix working
and equally consistent with the grader having lost the ability to say anything
else.

No real transcript could separate those. Every session in `~/.claude/projects`
was driven by someone who already knows how. A sweep of all 44 across the six
code projects found 16 long enough to grade and none that went badly. A uniform run of A grades on competent sessions is exactly what a
working rubric produces and exactly what a broken one produces.

## What was built

`plugin/evals/session-calibration/`, a fixture and a runner.

`make-sessions.py` generates two transcripts and the project they ran in. The
project is deliberately healthy — `CLAUDE.md` present and split across `docs/`,
rules on disk — and both sessions run inside it, so the structural practices are
identical and the only variable is how the work was asked for.

**`bad`** — fifteen prompts, five costs, each one traceable to words the user
actually typed. That last part is the constraint the rubric imposes before a cost
may be charged to the user: the missing information had to be theirs to give, and
you have to be able to quote what was missing.

| Message | Cost |
| --- | --- |
| 3 | a convention held but never stated, so the rate-limiter work is undone |
| 5 | a reversal that discards the CSV export just finished |
| 7 | the diagnosis injected at message 6 was wrong, and cost a detour |
| 10 | approval at message 9 without looking at what was being approved |
| 14 | an instruction ambiguous enough to be read the other way |

**`ordinary`** — the same project driven properly. Scoped opening request with an
explicit constraint and an explicit "don't change anything yet", one subject
throughout, the diff asked for before approval, findings checkpointed to
`docs/perf-notes.md`, and a deliberate stop. It is here so the grade on `bad`
means something: a rubric that marks both the same has measured nothing.

## Measurements

Model `haiku`, through `evaluate.sh` unchanged.

| Session | Runs | Grades |
| --- | --- | --- |
| `bad` | 6 | C, C, C, C, C, C |
| `ordinary` | 5 | A+, A, A+, A, A+ |

BP-06 was the first focus item in all five `bad` reports that were kept. The
second varied: BP-03,
BP-15, BP-10, BP-16, BP-04 — five different practices across five runs, each
resting on a different one of the five costs. That is the rubric's "one
behaviour, one focus item" rule working as intended; there were five genuine
episodes and it picked a different second one each time. It is not instability in
the grade.

## Three defects found, and what the fix did to them

Three problems turned up while measuring, all in the bookkeeping sections below
the grade — which is where a reader looks to check the grade was fair. None of
them moves a band.

All three looked like they might share one root cause: the rubric defines four
states — focus, done well, not applicable, and **unobserved** — while the output
template in `grader-prompt.md` had three sections. "Unobserved" is created
deliberately, for the nine practices a transcript cannot show, and then had
nowhere to be printed. So it was tested as a hypothesis: add the fourth section
and a rule that the four states partition BP-01 to BP-19, change nothing else,
and rerun.

### 1. Practices were silently omitted — fixed

The rubric says to name what was not applicable "so the reader can see the grade
did not rest on it". Before the fix, no run did: the sparsest accounted for six
of nineteen.

After the fix, a `bad` report accounts for all nineteen exactly once — two focus
items, two done well, nine not applicable, six unobserved.

### 2. BP-10 reported in the wrong bucket — improved, not fixed

Message 6 is "it's definitely a caching problem, just fix the cache" and message
7 is "ok it wasn't the cache" — the textbook BP-10 failure, and BP-10's
observability is **Direct**. Before the fix, three runs out of five filed BP-10
under *not applicable*, one of them while citing that exact episode as evidence
under BP-06 four lines earlier.

After the fix it moves to *unobserved*, which is a smaller lie — it no longer
claims the session gave no occasion to exercise the practice — but it is still
wrong, and the added rule says so explicitly: a practice whose failure case
occurred belongs in a focus item or nowhere. The episode does get counted; it is
folded into another focus item's narrative rather than dropped. So the grade is
right and the attribution is not.

Left alone deliberately. Fixing it means prose aimed at BP-10 in particular,
which is the kind of patch that makes a rubric grow without making it better, and
it changes no grade.

### 3. "Did well" unstable, sometimes unearned — improved

Before the fix, across five runs of the same digest: `{BP-09, BP-12}`, `{BP-09}`,
`{}`, `{BP-02, BP-19}`, `{}`. One run credited BP-12 on `side_questions: 0` — the
case the rubric explicitly forbids, "do not list a practice as done well when the
only evidence is that its failure case did not occur" — while another listed
BP-12 as not applicable on identical evidence.

After the fix BP-12 lands in *not applicable*, which is right. The list is still
thin and still leans on structural facts about the fixture project, but nothing
is now credited on absent evidence.

### One thing that is not a defect

A run made BP-16 a focus item despite its observability being **None**. That
looked wrong and is not: BP-16's entry carries an explicit exception for when the
user's own words show it, "asking about a specific change, or questioning
something in one", and message 10 is exactly that.

## After the fix

`grader-prompt.md` gained an `## Unobserved` section and three rules: "did well"
needs positive evidence, "not applicable" and "unobserved" are distinguished by
the practice's Observability line, and every practice appears exactly once.

| Session | Runs | Grades |
| --- | --- | --- |
| `bad` | 4 | D, C, C, C |
| `ordinary` | 3 | A+, A, A+ |

`bad` drifted one notch down rather than up, which is the right direction: it was
built with five costs and the rubric puts five or more at D. The bands still hold
and `calibrate.sh` still exits zero.

## Where this leaves the release

The blocking question is answered and the one defect worth fixing is fixed. The
BP-10 misfiling survives and is not gated on: it changes no grade, and the patch
it wants is the kind that makes a rubric longer without making it better.

Any further edit to `rubric.md`, `best-practices.md` or `grader-prompt.md`
invalidates the numbers above. Rerun `calibrate.sh` before trusting them again.

Still outstanding from before, and unchanged by this work: no `plugin/evals`
trigger cases for the skill, the planned `SessionStart` line that would surface
the last grade was never built, and `user_activity.side_questions` remains
unverified because no transcript on this machine contains a `/btw`.
