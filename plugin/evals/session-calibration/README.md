# Calibration for the evaluate-session skill

Two synthetic sessions with known ground truth, graded through the real pipeline.

```sh
plugin/evals/session-calibration/calibrate.sh            # 3 runs each, a few cents
plugin/evals/session-calibration/calibrate.sh --runs 1
plugin/evals/session-calibration/calibrate.sh --dry-run  # build and digest only
```

## Why this exists

`evaluate-session`'s rubric resolves ambiguity upward, because an unfairly harsh
grade gets ignored and a generous one does not. The cost of that choice is a
failure mode nothing else would catch: every session lands at A, the scorecards
stay cheerful, and the skill has silently stopped measuring anything.

Real transcripts cannot detect it. Every session on the machine this was built on
was driven by someone who already knows how, so a run of A grades is equally
consistent with a working rubric and a broken one. The negative control is the
only thing that separates them.

## What to expect

| Session | Band | Why |
| --- | --- | --- |
| `bad` | **C** | Five costs, each traceable to words the user typed |
| `ordinary` | **A+** or **A** | The same project driven properly |

`calibrate.sh` accepts C or D for `bad` and A+, A or B for `ordinary`, and exits
non-zero otherwise. A `bad` session grading B or above means the bands have
stopped discriminating, and the fix is a threshold rather than more prose.

Measured 2026-09-23 on `haiku`, six gradings of `bad` and five of `ordinary`:

- `bad` — C six times out of six. BP-06 led the focus items in all five reports
  that were kept.
- `ordinary` — A+, A, A+, A, A+.

The band is stable; the sections below it are not. See
`docs/plans/2026-09-23-evaluate-session-calibration.md` for what varied and what
that implies.

## The fixture

`make-sessions.py` builds both transcripts and the project they ran in. The
transcripts are generated rather than committed because the *shape* is the
point — reading the generator tells you what each session demonstrates, where
eight hundred lines of JSON would not.

The fixture project is deliberately healthy: `CLAUDE.md` present and split across
`docs/`, rules on disk. The structural practices read the filesystem, so if the
project were a mess both sessions would carry the same structural complaints and
a low grade on `bad` would no longer prove that the *driving* was what moved it.

Both sessions run in the same project for the same reason. The only variable is
how the work was asked for.

## Changing the rubric invalidates this

The bands are a property of `references/rubric.md`, `references/best-practices.md`
and `assets/grader-prompt.md` together. Edit any of them and the numbers above
are stale — rerun before trusting them. That is the whole point of the file: a
rubric edit that quietly stops the grader marking anything down is otherwise
indistinguishable from a rubric edit that worked.
