# `side_questions` — verified, and it does not work

**2026-09-23.** The counter carried into 1.10.0 as "unverified" is now verified.
It reads zero on every session, and it always will.

## What was believed

`digest.py` counts events with `isSidechain: true` and `type: "user"` into
`user_activity.side_questions`. The intent, stated in the code comment and in
BP-12, is to count questions the user deliberately asked *off* the main thread —
evidence of context hygiene. No transcript on this machine had ever contained
one, so the counter was shipped untested.

Two outcomes seemed possible: the field never fires, or it fires on the wrong
thing. The second would have been the serious one — a subagent launch
incrementing it would mean BP-12 crediting the user for context hygiene the
*assistant* performed, which is the exact error the rubric was rewritten to
prevent.

## What is actually true

Measured across every transcript on the machine:

| | files | `isSidechain: true` events |
| --- | --- | --- |
| main session transcripts | 55 | **0** |
| `<session-id>/subagents/agent-*.jsonl` | 16 | 2042 |

All 2042 carry an `agentId`. No main-transcript event does.

This version of Claude Code writes subagent traffic to a **separate file**. A
main transcript contains no sidechain events at all, so `side_questions` is
structurally incapable of being non-zero on the only input the skill documents
feeding it.

**The feared bug does not occur.** The rubric's separation between what the user
did and what the assistant did survives — but by accident of file layout, not
because anything in the parser enforces it.

## The defect that is real

The field is **unfalsifiable**. The grader is handed `side_questions: 0` on every
session and cannot distinguish "the user never asked anything off-thread" from
"this field does not work". Any weight it carries in a BP-12 judgement is weight
on noise, and BP-12's observability note presents it as a signal.

That is precisely what the observability tiers exist to prevent. A practice the
evidence cannot show is meant to be reported as *unobserved*. A permanent zero
reports it as *measured and absent*, which is a different and worse claim.

## Two latent hazards

Both are only reachable by pointing the parser at a subagent file, which nothing
prevents:

- **No guard on the input.** `digest.py --transcript <a subagent file>` returns
  `side_questions: 23, user_prompts: 0, assistant_turns: 0` — measured, not
  predicted. Neither `digest.py` nor `evaluate.sh` checks that the file is a main
  transcript. A future glob over `~/.claude/projects/**/*.jsonl` would hit them.
- **Ordering in `parse()`.** The `isSidechain` branch (line 140) precedes the
  `isMeta` branch (line 147), and the increment (line 145) runs before
  `text_of()`. So injected `<system-reminder>` events — machinery by the skill's
  own definition in `NOT_A_PROMPT` — and tool results both count, although every
  other path discards them.

## The fix, if it is worth fixing

Keying on `isSidechain and not e.get("agentId")`, plus `not isMeta` and
`text_of(...) is not None`, is a zero-risk change: it produces the same 0 today
but stops producing it for the wrong reason, and it makes the subagent-file case
count nothing rather than 23.

That is cosmetic on its own. The question it does not answer is whether a genuine
off-thread question lands in the main transcript at all. There is no sample —
`/btw` has never been used on this machine — and given that this version
segregates *all* sidechain traffic into per-agent files, the likelihood is that
an off-thread question goes to its own file too. If so the field is not merely
untriggered but **unimplementable from the main transcript alone**, and the right
move is to drop it and mark BP-12's transcript signal unavailable rather than
keep a zero nobody can interpret.

The input guard is worth doing regardless of that question. It is a correctness
bug with a wrong answer rather than an absent one.

## Method note

Verified by delegating to a subagent, which was itself the instrument: launching
it generated the sidechain events under test. Every load-bearing claim in its
report was re-checked directly before being recorded here — the counts above, the
`agentId` universality, the subagent-file digest output and the line ordering.
