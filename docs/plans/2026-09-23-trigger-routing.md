# Which of the three end-of-session skills fires

**2026-09-23.** A solution for the description-collision risk raised before the
1.10.0 release.

## Correcting the framing

I said `evaluate-session` competes with `context-handover` and `session-handoff`
for "wrap this up" phrasing. Reading the three descriptions side by side, that is
overstated. `evaluate-session` is fenced on feedback language throughout — "how
they did", "how their prompting was", "evaluated, scored, graded", "what they
should do differently". None of it reaches for ending a session.

It leaks in exactly one place, and it is the hook clause:

> Also covers installing the hook that produces a scorecard automatically **at
> the end of every session**.

That is the only end-of-session phrase in the description, and it is there to
describe an installation option rather than a trigger.

The collision that is actually load-bearing is the other pair, and it predates
this release: **`context-handover` and `session-handoff` both claim ending a
session and both claim moving to another machine.**

| | context-handover | session-handoff |
| --- | --- | --- |
| | "stopping for the day to resume tomorrow" | "wrapping up or closing out a session" |
| | "handing the work to a different session or machine" | "is moving to another machine, another account or another subscription" |

## The discriminator

One question separates all three: **what is lost if you do nothing?**

| Skill | What is at risk | Where the output goes |
| --- | --- | --- |
| `context-handover` | the reasoning — it exists only in the conversation | a briefing in `.claude/handover/`, read once then deleted |
| `session-handoff` | the files — they exist only in the cloud container | a durable archive in a connected folder |
| `evaluate-session` | nothing; it is feedback about the person | a scorecard in `~/.claude/scorecards/` |

Both handover skills already say this in their bodies. Neither says it in the
description, which is the only part that decides whether they fire.

## Why the existing eval suite cannot catch this

Every case in `plugin/evals/` asserts exactly one thing: `release-version` fired,
or it did not.

```yaml
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?release-version"'
min: 1
```

A skill stealing a sibling's prompt is invisible to that shape. A case that
asserts only "context-handover fired" passes just as happily when
`session-handoff` fired alongside it, and a case that asserts only
"evaluate-session did not fire" says nothing about which skill did.

**A routing case has to assert three things: the intended skill fired, and each
sibling did not.** That is the structural change; the prompts are the easy half.

## Proposed description edits

Minimal and surgical. Each adds one clause naming the sibling it loses prompts
to, because a near-miss is settled by saying which side of the line the case
falls on, not by adding more adjectives to your own side.

**`context-handover`** — after "…hand it off, or brief the next session.":

> Works in any project and needs nothing connected; when the risk is that files
> disappear with the container or the account rather than that the thread is
> lost, that is `session-handoff`.

**`session-handoff`** — the description already ends "Needs a connected folder.",
which is a real fence. Sharpen it:

> Needs a connected folder — without one, clearing a long conversation without
> losing the thread is `context-handover`.

**`evaluate-session`** — rewrite the hook clause so it stops carrying an
end-of-session phrase:

> Also covers installing the hook that produces a scorecard automatically on
> every exit.

And append one fence:

> This is feedback about how the person worked, never a record of the work
> itself — saving, archiving or carrying the thread over is `context-handover`
> or `session-handoff`.

These are proposals. Per `CLAUDE.md`, a description is tested rather than argued,
so none of them should land without the cases below measuring whether they helped.

## The case matrix

Nine cases. Each asserts the intended skill fired and both siblings stayed quiet.

| # | Prompt | Must fire | Tests |
| --- | --- | --- | --- |
| 1 | "wrap this up for tomorrow" | context-handover | the phrase both handover skills claim |
| 2 | "let's call it a day — note where we got to" | context-handover | "note" is not "grade" |
| 3 | "this conversation is getting long and the answers are drifting" | context-handover | the canonical case, should be unambiguous |
| 4 | "save this before we lose it" *(connected folder present)* | session-handoff | the folder is the discriminator |
| 5 | "I'm moving to my other machine" *(no connected folder)* | context-handover | same words as 4, opposite answer |
| 6 | "how did I do on this one?" | evaluate-session | "how did I do" against "how did it go" |
| 7 | "was my prompting any good?" | evaluate-session | unambiguous positive |
| 8 | "what should I do differently next time?" | evaluate-session | no scoring vocabulary at all |
| 9 | "am I burning context?" | evaluate-session | overlaps context-handover's subject matter |

Cases 4 and 5 are the pair that carries the most weight: near-identical intent,
and the only thing separating them is whether a folder is connected.

## Mechanics

- **Tag them `routing`, not `trigger`.** `scripts/eval.sh trigger` filters by tag
  and `plugin/evals/README.md` records a baseline of "8/8 at 1.00" for that
  selection. Adding cases to it silently invalidates a documented number. Add a
  `routing` selector to `eval.sh` alongside the existing two.
- **Set both `min` and `max` on every negative.** The README records that `max: 0`
  alone becomes `expected 1..0` and fails forever.
- **`arm: both` is not needed here.** `eval.sh` runs `--ablation none`, so there
  is one arm. The README's warning applies to the default ablation.
- **Use `tool_used`, never `regex` on the trace.** The README records a run where
  a trace regex marked the right answer wrong because the model *mentioned* the
  thing it correctly declined to do.
- Case 4 needs a scaffold that presents a connected folder, and case 5 one that
  does not. If a connected folder cannot be simulated in the sandbox, drop the
  pair and record why — a case that cannot distinguish its two arms measures
  nothing, which is the failure mode the README is entirely about.

## Recommendation

Not part of 1.10.0. The routing risk is real but it is old — `context-handover`
and `session-handoff` have shipped alongside each other since 1.9.0 with this
overlap, and `evaluate-session` adds very little to it. Shipping the skill does
not make it worse.

Do the cases first and the description edits second, so there is a measurement to
move. Doing it the other way round produces a description that reads better and
no evidence it routes better.
