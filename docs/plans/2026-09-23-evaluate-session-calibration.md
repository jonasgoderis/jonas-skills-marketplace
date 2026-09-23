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

## What this does not settle

Three defects turned up while measuring. None of them moves the band — the costs
are counted either way, just attributed differently — so none blocks release. All
three are in the bookkeeping sections below the grade, which is where a reader
looks to check the grade was fair.

### 1. BP-10 is reported "not applicable" on a session that violates it

Message 6 is "it's definitely a caching problem, just fix the cache" and message
7 is "ok it wasn't the cache" — the textbook BP-10 failure, and BP-10's
observability is **Direct**. Three runs out of five listed BP-10 under *Not
applicable*. One of those three simultaneously cited that exact episode as
evidence under BP-06, so the report contradicts itself within four lines.

Only one run made BP-10 a focus item, which is the correct read.

### 2. Most practices are silently omitted

The rubric says to say what is not applicable "so the reader can see the grade did
not rest on it". No run does. The sparsest accounted for six of nineteen.

The cause looks structural rather than a matter of the grader ignoring the
instruction. The rubric defines four states — focus, done well, not applicable,
and **unobserved** — and the output template in `grader-prompt.md` has three
sections. "Unobserved" is created deliberately, for the nine practices a
transcript cannot show, and then has nowhere to be printed. Practices in that
state disappear, and genuinely applicable ones get dropped into the same gap.

If this is fixed, the template needs the fourth bucket, not more prose telling
the grader to be thorough.

### 3. "Did well" is unstable, and sometimes unearned

Across five runs of the same digest: `{BP-09, BP-12}`, `{BP-09}`, `{}`,
`{BP-02, BP-19}`, `{}`.

Two specific problems inside that. One run credited BP-12 as done well on
`side_questions: 0` — the case the rubric explicitly forbids, "do not list a
practice as done well when the only evidence is that its failure case did not
occur" — and another run listed BP-12 as *not applicable* on the same evidence.
A different run's entire "did well" list was BP-02 and BP-19, both structural,
both facts about the fixture project rather than about the session.

### One thing that is not a defect

A run made BP-16 a focus item despite its observability being **None**. That
looked wrong and is not: BP-16's entry carries an explicit exception for when the
user's own words show it, "asking about a specific change, or questioning
something in one", and message 10 is exactly that.

## Where this leaves the release

The blocking question is answered. Release is not gated on the three defects
above; they degrade the report's bookkeeping, not its grade, and fixing any of
them changes the grader's output and invalidates the numbers in this document.
Rerun `calibrate.sh` after any such fix.

Still outstanding from before, and unchanged by this work: no `plugin/evals`
trigger cases for the skill, the planned `SessionStart` line that would surface
the last grade was never built, and `user_activity.side_questions` remains
unverified because no transcript on this machine contains a `/btw`.
