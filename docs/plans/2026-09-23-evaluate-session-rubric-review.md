# evaluate-session — where the catalogue and rubric produce wrong grades

Review of `references/best-practices.md` and `references/rubric.md` against what
`scripts/digest.py` actually emits and what `assets/grader-prompt.md` asks for.
Ordered by likelihood × how wrong the resulting grade is. Every finding below
would change a band or a focus item; wording preferences are left out.

The grader is Haiku with ~6,000 tokens of prompt. Guardrails have to be short,
concrete and stated where the model is already looking.

---

## 1. The digest has one visible actor, so every bad outcome has one candidate cause

**Rubric § What is being graded / § Evidence rules. Root cause of the observed
BP-06 misfire.**

Assistant prose and tool output are excluded by design. The user's messages are
therefore the only *text* available to explain anything that went wrong, and a
small model will explain everything with them. The counterweight is one sentence
— "Do not grade the assistant's responses" — which reads as "don't critique
Claude's writing", not "don't attribute Claude's decisions to the user".

Session: 7 messages, 180 tool calls, 3 files edited, 2 commits, one topic. The
work was redone once. Nothing in the digest says why. Grade: B with "BP-06 — the
mechanism was not specified upfront (message 3)". That is the hook-installation
case verbatim, and it will recur on every session where the assistant chose
badly.

**Change — replace, in § What is being graded:**

> The subject is the person's side of the conversation. Do not grade the
> assistant's responses, and do not grade the codebase.

**with:**

> The subject is the person's side of the conversation. Do not grade the
> assistant's responses, its decisions, or the codebase. An assistant-side
> mistake does not become a user-side one because the user is the only person
> visible in the evidence.

**Change — add as a bullet in § Evidence rules:**

> - The digest shows one actor. Assistant prose and tool output are absent, so
>   the user's messages are the only text available to explain anything that went
>   wrong, and the pull is to explain everything with them. Resist it. Rework, a
>   reversal or a wrong turn counts against a prompt only when the missing
>   information was the user's to give and the words that were missing can be
>   quoted from their message. A design decision, a mechanism, a file layout or
>   an implementation detail the assistant chose is the assistant's, and its
>   failure is not a finding against any practice. Where you cannot tell whose
>   decision it was, there is no finding.

---

## 2. BP-06 invites reasoning backwards from the outcome

"Every gap left open is filled with an assumption, and the assumptions are
invisible until the output is wrong" reads in reverse as: output was wrong →
there was a gap → BP-06. Nothing in the entry bounds "gap" to information the
user held. This is the sentence the failed run was standing on.

Session: "add a SessionEnd hook that grades the session, opt-in". The assistant
picks `settings.json`, it breaks, it is redone with a marker file. Focus item:
"BP-06 — the installation mechanism was not specified (message 3), costing a
rewrite." The mechanism *was the delegated work*.

**Change — append to BP-06 "Doing it well":**

> Specific means the information you held when you asked: the goal, the
> constraints, the audience, what done looks like. It does not mean pre-deciding
> the work you are delegating. A prompt that names the outcome and leaves the
> mechanism open is specific; when the mechanism then turns out wrong, that is
> the answer being wrong, not the question.

**Change — replace BP-06's observability line:**

> **Observability:** Direct, and from the message alone. A prompt is vague when
> you can point at what it left open while the user was in a position to state
> it — never because something downstream of it had to be redone.

---

## 3. Everything in `activity` is an assistant action; four practices score the user on it

The user cannot launch a subagent, write a script, run a test or make a commit.
`activity.subagents`, `tools`, `test_runs`, `commits` and `files_edited` are all
assistant tool calls. BP-12 is marked **Direct** on this basis, which is simply
wrong: delegation is the assistant's call, made or missed regardless of how the
prompt was written. BP-13, BP-15 and BP-05 have the same problem.

Session: one research question; the assistant reads 14 files itself. Digest:
`Read: 22`, `subagents.launched: 0`. Focus item: "BP-12 — a dozen files read into
the main conversation instead of delegating (message 2)." The user asked one
question and had no say.

**Change — replace BP-12's observability line:**

> **Observability:** Indirect. `activity.subagents.launched` shows whether
> delegation happened, not who chose it — the assistant delegates on its own and
> fails to delegate despite a good prompt. This is a user-side finding only where
> a message asks for broad reading in the main thread after context was visibly
> tight, or where the user turned a subagent down. A low count on its own is
> unobserved.

**Change — add a bullet to § Observability rules:**

> - Everything under `activity` is an action the assistant took. Tool counts,
>   subagents, test runs and commits show what happened, never who decided it.
>   Read them as the shape of the session, and pair a count with the user message
>   that asked for it before treating it as evidence about the user.

---

## 4. BP-05: `commits: 0` is the *correct* outcome in this project, and is scored as a failing

The repo's own instructions tell the assistant not to commit unless asked. A
careful user reviews and commits by hand — in another terminal, after the
session, invisible to the transcript. Digest: `commits: 0`, `files_edited: 3`,
wall 90 minutes.

Focus item: "BP-05 — nothing checkpointed across a 90-minute session." The action
it pushes the user toward is *letting Claude commit more*, against their own
rule. Perverse incentive and a false finding from the same line.

**Change — replace BP-05's observability line:**

> **Observability:** Indirect, and weakly. The digest shows files the assistant
> wrote and `git commit` calls the assistant ran. It cannot see commits the user
> made themselves, in another terminal or after the session, and many projects
> deliberately forbid the assistant from committing at all, so `commits: 0` is
> unobserved rather than a failing. The signal that does support a finding is a
> user message asking for status, decisions or a plan to be held in the
> conversation instead of in a file.

---

## 5. Slash commands are redacted to their name, then graded as if verbatim

`digest.py` rewrites any `<command-name>` message to `/name` and drops the
arguments and the expanded prompt. The grader prompt tells the model the messages
are "every real user message in order, verbatim", so it grades a redaction as
though it were what the user typed.

Session driven through `/code-review high`, `/release-version 1.9.2`,
`/context-handover`. The digest shows three contentless messages. Focus item:
"BP-08 — several turns named no format or scope (messages 2, 4, 7)." The user's
most disciplined turns are graded as their vaguest. (Related: `user_prompts`
excludes commands, so a command-driven session can fall under `--min-turns 5` and
be dropped silently.)

**Change — add a bullet to § Evidence rules:**

> - A message with `kind: command` carries the command's name and nothing else;
>   its arguments and the prompt it expands to are stripped before you see it.
>   Never cite one as evidence of vagueness, a missing format or a missing
>   example — you are looking at a redaction, not at what the user typed. Where
>   commands are a large share of the messages, say the session is only partly
>   observable and grade the prompts that remain.

**Change — in `grader-prompt.md`, replace:**

> `messages` — every real user message in order, verbatim.

**with:**

> `messages` — every real user message in order, verbatim, except slash commands:
> those appear as `/name` with their arguments and expansion stripped.

---

## 6. BP-07 and BP-10 grade the same observable in opposite directions, and BP-10 turns on a belief

BP-10's failure condition is "doing the second while believing you are doing the
first" — internal state — while the entry is marked **Direct** and the rubric
forbids inferring intent. The single observable is "the message contains
examples", and it supports a credit (BP-07) or a fault (BP-10) with equal
justification. Two runs on the same JSON produce different focus items.

Session: "here are three scorecard layouts I like — what should ours look like?"
Reading A: BP-07, did well. Reading B: BP-10, open question with the answer
injected, focus item. Both are defensible from the text as written.

**Change — replace BP-10's third paragraph and observability line:**

> **Doing it well:** when you want options you have not thought of, ask open,
> then narrow once the range is on the table. When you want conformity to a
> pattern, seed it deliberately.
>
> **Observability:** Indirect, and only from the message itself: it asks for
> options *and* supplies them, and the messages that follow stay inside the range
> it supplied. An example given to fix a format or a shape is BP-07 done well,
> not this. Never separate the two by guessing what the user believed.

---

## 7. BP-16 names no signal, and the digest contains none

The rubric grants Indirect practices only "the signals named in their entry".
BP-16's entry names none — the line is "**Observability:** Indirect." and stops.
Reading a diff is not an event the transcript records: no assistant output, no
per-file edit counts (`files_edited` is a deduplicated set), no ordering, no
accept/reject events. With no signal to bind to, the grader proxies off size.

Session: 9 messages, 40 edits. Focus item: "BP-16 — changes accepted without
reading them (messages 3-9)." Unfalsifiable, and probably false — the user may
have read every diff in the terminal.

**Change — replace BP-16's observability line:**

> **Observability:** Indirect, and usually unobserved. Reading is not an event the
> transcript records: the digest holds no diff, no review step and no per-file
> edit count. The only usable signals are the user's own messages — asking what
> changed, quoting a line back, rejecting or correcting a specific edit. Where
> none of those appears, report BP-16 as unobserved. Never infer it from the size
> of the change or the number of edits.

---

## 8. BP-13 claims a signal the digest deliberately drops

"Repeated manual sequences are visible" is false for this pipeline. `digest.py`
builds a `sequence` list and never emits it; `activity.tools` is aggregate counts
only; Bash command text never leaves the script; and `structural` lists no
scripts, so "whether a script already existed" cannot be checked either.

Session: `Bash: 34`. Focus item: "BP-13 — a deterministic sequence run by hand
(messages 5-9)", resting on a count that says nothing about repetition.

**Change — replace BP-13's observability line:**

> **Observability:** Indirect, and rarely decidable. The digest carries tool
> counts, not the order or the content of the commands, so a repeated sequence
> cannot actually be seen in it, and it lists no scripts, so whether one already
> existed cannot be checked. Raise BP-13 only where a user message describes the
> same fixed procedure in prose for a second time. A high `Bash` count is not
> evidence.

---

## 9. Double counting: one habit, four entries, both focus slots

BP-03 (small steps), BP-09 (iterate), BP-11 (zoom out first) and BP-16 (which
itself says "Small steps (BP-03) are what make this affordable") all fire on the
single observable "few messages, many tool calls, large change". The rubric says
take the two largest costs; those two will be two views of one habit. The report
then says the same thing twice, a genuinely separate failure (BP-04, BP-18) is
crowded out, and the index — which stores only the two identifiers — shows the
cluster dominating the user's history.

This is the only real double-counting cluster. BP-02 / BP-14 / BP-19 also overlap
but are structural and confined to a standing note, so they cost nothing.

**Change — add to § The report:**

> One behaviour, one focus item. BP-03, BP-09, BP-11 and BP-16 describe a single
> habit from four sides — asking for too much at once and not looking at what
> came back. When an episode fits more than one, report the one the user would
> act on and leave the others out entirely. The second focus item has to rest on
> a different episode; where there is no second episode, there is no second focus
> item.

**Change — add to BP-09, after the first paragraph:**

> This is BP-03 from the other end: BP-03 is about the size of what you ask for,
> this is about what you do with the answer. A session that asked in steps and
> corrected as it went satisfies both — that is one credit, not two, and its
> absence is one fault, not two.

---

## 10. Bands A/B/C overlap, and the "cost" they turn on is not in the digest

"B — One or two practices were neglected in ways that visibly cost time, rework
or clarity" against "C — Several neglected, or one neglected badly enough to
shape the whole session". Three neglected practices fits neither cleanly, and
"one badly enough" versus "one or two that visibly cost" is the same fact at two
volumes. A, likewise: "nothing that cost anything" versus "one that visibly cost
time" has no threshold between them.

Worse, the deciding quantity is unobservable. `files_edited` is a deduplicated
sorted set, so a file edited twelve times is indistinguishable from one edited
once; there is no ordering, no error, no revert, no assistant output. "Visibly
cost rework" has almost nothing in the digest to rest on, so two runs land on B
and C from identical JSON and the index records movement that is noise.

Note also that the band definitions count practices while the report format
allows at most two focus items — a C or D cannot actually be shown, which pulls
graders toward B.

**Change — replace the B, C and D rows:**

> | **B** | Solid. One practice was neglected and the digest shows what it cost — a repeated request, a correction, a rewrite the user had to ask for. |
> | **C** | Mixed. Two or more neglected with visible cost, or one that shaped every turn of the session. |
> | **D** | Poor. The session worked against itself: scope that moved every few messages, no checkpoint of any kind, and no visible verification. All three, not one of them. |

**Change — replace the paragraph after the table:**

> Grade on what the session cost itself, not on a count of ticked practices. Four
> practices missed with no consequence is a better session than one missed that
> caused an hour of rework. Cost has to be visible in the digest to count: a
> repeated or rephrased request, a correction, a message asking again for
> something already agreed, an abandoned thread. The digest carries no diffs, no
> errors and no per-file edit counts, so a cost you cannot point at is not a
> cost. Where the evidence supports two adjacent bands, take the higher one — an
> unstable grade is worse than a coarse one, and an overstated one gets ignored.

---

## 11. BP-01 penalises exactly what BP-03 and BP-09 reward, on a signal the user does not control

BP-01's named signals are turn count, duration and compaction events. BP-03 and
BP-09 push the user toward more, smaller turns. So disciplined stepwise work
raises the very numbers BP-01 reads as decay. Compaction is worse: it follows
from context the *assistant* consumed — one large read, one skill body — and can
fire in a ten-message session the user drove perfectly.

Session: wall 120 min, active 48, 14 prompts, 1 compaction. Focus item: "BP-01 —
the session ran past its useful life". Nothing in the digest supports "past its
useful life", and a handover written outside the project never appears in
`files_edited` at all.

**Change — replace BP-01's observability line:**

> **Observability:** Indirect. Turn count, wall and active minutes and compaction
> events are visible, and a handover file appears in `files_edited` only when it
> was written inside the project. None of them says the session had gone bad: a
> compaction can follow a single large read, and a high turn count is what BP-03
> and BP-09 look like when they are done well. The finding needs degradation in
> the user's own messages — re-explaining something already settled, correcting a
> drift back to an earlier decision, asking again for what was agreed. Without
> one of those, this is unobserved.

---

## 12. The structural checks measure the wrong thing, and they repeat on every scorecard

- **BP-02.** `context_files` counts markdown files anywhere in the tree whose
  *filename* contains "claude". A project doing exactly what BP-02 asks — root
  `CLAUDE.md` pointing at `docs/testing.md`, `docs/deploy.md` — scores 1 and looks
  unsplit. A project with one 900-line `CLAUDE.md` plus a stray `claude-notes.md`
  scores 2 and looks split. The metric is close to anti-correlated with the
  practice.
- **BP-19.** `rules_dir` is `<project>/.claude/rules` only. Rules kept where this
  practice actually wants them — user level, or a dotfiles repo — are invisible,
  so a user who follows BP-19 perfectly gets `present: false` in every project,
  forever.
- **BP-14.** `skills.with_references` over `skills.count`: a skill short enough to
  need no reference files is indistinguishable from one that should have them.

Standing notes recur on every scorecard for that project, so a wrong one is wrong
many times over.

**Change — replace the three observability lines:**

BP-02:

> **Observability:** Structural, and partial. The digest reports `claude_md.lines`
> and a count of markdown files whose *filename* contains "claude". It cannot see
> whether the root file points at anything, so context split into files named for
> their concern — `testing.md`, `deploy.md` — is invisible to it. Raise this only
> where `claude_md.lines` is large; never conclude from the count alone that
> nothing was split.

BP-19:

> **Observability:** Structural, and project-scoped. The digest looks only for
> `.claude/rules/` inside the project. Rules kept where this practice wants them —
> user level, or a dotfiles repo — are not visible to it, so an absent rules
> directory is unobserved, never a failing. Report BP-19 as not applicable unless
> the project's own instructions visibly restate cross-project rules.

BP-14:

> **Observability:** Structural, and a count only. The digest reports how many
> skills exist and how many have a `references/` directory. A skill short enough
> to need none is indistinguishable from one that should have them, so a low ratio
> is not by itself a failing.

---

## 13. "Did well" needs no evidence, and BP-18 in it is circular

The evidence rule binds "findings"; the template makes "Did well" bare
identifiers with no commentary and therefore no citation, so the grader fills it
to look balanced. BP-18 is the harmful case: `digest.py` exits 4 and emits
*nothing* when a secret pattern matches, so the grader only ever sees sessions
that already passed the scan. Listing BP-18 as done well tells the user their
handling of sensitive material was checked when the evidence was withheld by
construction — and the pattern file covers keys and tokens only, not personal
data, client names or internal documents, which is most of what BP-18 is about.

**Change — add to § The report:**

> An identifier goes under "Did well" on the same evidence a focus item needs: the
> digest shows the practice being exercised. With no positive evidence the
> practice is unobserved or not applicable, not done well. BP-18 never goes there
> — a digest exists only because the session's messages passed a secret scan, so
> the absence of secrets in it is the tooling's doing, not the user's. BP-18 is a
> finding only when sensitive material is visible in a message.

---

## 14. Smaller, still grade-affecting

- **BP-04, forced detours.** Topic drift is often the work's doing — a broken
  build, a failed install, a dependency discovered mid-task — or the assistant's.
  Append: "**Observability:** Direct, with one exception: a detour the work forced
  — a broken build, a failed install, something the task turned out to depend on —
  is not a second subject. Drift counts when the user introduced a topic the
  session did not require."
- **Structural in "Did well".** The rubric says structural practices "should never
  appear as a focus item"; the grader prompt says they "belong in neither list".
  As written the grader has to disobey one of its two authorities, and whether
  BP-02/14/19 show up as credits varies run to run. Make the rubric say "never
  appear as a focus item or under practices done well — report them once, as a
  standing note."
- **Names in "Did well".** Rubric: "listed by identifier and name only". Template:
  `BP-nn, BP-nn, BP-nn`. Same conflict, same fix — pick one; the template is the
  cheaper one to keep.
- **Message numbers after truncation.** `digest.py` renumbers `i` from 1 *after*
  dropping the oldest messages, so "message 4" in a scorecard is not the user's
  fourth message, and the user never sees the digest anyway. The rubric's
  checkability claim does not hold. Either keep original indices in `digest.py`,
  or require a quote alongside: replace "\"BP-06, turn 4\" is checkable" with
  "\"BP-06, message 4 — 'make the hook work'\" is checkable; a bare number is not,
  because the reader never sees the digest."
- **BP-17 subject versus session.** A session spent building something that scores
  or classifies people — this skill included — can be marked down although no
  decision inside the session was delegated to a model. Append to BP-17: "This
  concerns decisions taken in the session, not the subject matter of the code.
  Building something that scores or classifies people raises BP-17 about that
  system's design, which is a note about the work, not a mark against how the
  session was driven."

---

## Categories that produced nothing further

Nothing beyond the above under perverse incentives: the two real ones are already
listed (BP-05 pushing the user to let Claude commit against their own rule, §4;
BP-01 punishing the extra turns BP-03/BP-09 ask for, §11). Nothing in either file
rewards terse prompting for its own sake, and nothing discourages asking
questions — BP-11 is about the shape of the *answer*, not the length of the
prompt. No further contradictions between the three documents beyond §5, §12 and
§14.
