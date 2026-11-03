# Eval suite

Run by `claude plugin eval`. Every case is tagged with the skill it tests and
with `trigger` (does the skill fire when it should, and stay quiet when it
should not) or `behaviour` (once it fires, does it do the job right).

| Skill | Trigger | Behaviour |
| --- | --- | --- |
| `release-version` | 8 | 4 |
| `evaluate-session` | 8 | 4 |
| `drawio-conventions` | 7 | 5 |

```sh
scripts/eval.sh                     # everything
scripts/eval.sh trigger             # every trigger case, ~$1 per skill at one run
scripts/eval.sh behaviour           # every behavioural case
scripts/eval.sh evaluate-session    # one skill's cases — any skill directory name
scripts/eval.sh out-the-door --runs 1 --keep-temp
```

Anything after the selector is passed through to `claude plugin eval`.

## release-version

### What to expect

A healthy run is **every case at 1.00 except `cut-a-release`, which lands at
0.80–0.87**. That case carries release-version's one judge-scored grader, and it
disagrees with itself across runs on output a careful reader would accept. The
deterministic graders on that case have never produced a false result;
treat a judge failure as something to read, not something to fix. `eval.sh`
gates at 0.8 for this reason — do not raise it to 1.0.

Pinned baseline, `claude-sonnet-5` with a `claude-haiku-4-5` judge:

| Selection | Result | Cost |
| --- | --- | --- |
| `trigger`, 1 run | 8/8 at 1.00 | $0.89, 62s |
| `behaviour`, 3 runs | 4/4 at 1.00 | $2.20, ~4 min |

Re-recorded on 2026-09-23 when the docs check landed. The first pass of that run
caught two real faults — a README typo written up as a changelog line, and doc
edits made while a missing-tests question was still open — and a progress
grader on `target: trace` that passed on the skill's own text. The table is the
run after those fixes.

The models are pinned in `scripts/eval.sh`. Unpinned, a model release moves the
scores and a regression looks exactly like a model change.

## evaluate-session

The trigger negatives are near misses against the skill's neighbours: a code
review (`review-the-branch`), a handover (`wrap-up-for-today`), grading
something that is not a session (`grade-the-essays`), and "wasting context" said
about a project file (`trim-claude-md`).

The behavioural cases cannot produce a real grade. The sandbox's `claude` is
missing or not logged in, so `evaluate.sh`'s grading call always fails there.
Whether the grader bands a session correctly is what
`session-calibration/calibrate.sh` measures, outside the sandbox. These cases
check the skill around the grader instead: that it drives the scripts, that a
skip or a failure reaches the user as one, that a rubric change gets a dry run,
and that automatic grading is switched on through `enable-hook.sh` with the cost
stated. `grading-call-fails` found the skill grading a session itself when the
script failed; see its README.

Pinned baseline, `claude-sonnet-5` with a `claude-haiku-4-5` judge, recorded
2026-09-23:

| Selection | Result | Cost |
| --- | --- | --- |
| `evaluate-session`, 3 runs | 12/12 at 1.00, 36/36 runs | $4.82, ~5 min |

Some trigger runs end on the eight-turn cap after the skill has fired and
started running scripts. That is expected and does not affect the score: the
grader only asks whether the skill was called.

## drawio-conventions

The trigger positives cover a new diagram, a small edit to an existing
`.drawio` file, the name diagrams.net instead of draw.io, and the symptom rule A
exists for ("the arrow stays glued to the same spot") said without any draw.io
words. The near misses are a Mermaid flowchart of the same flow
(`mermaid-login-flow`), a question about a `.drawio` file that changes nothing
(`drawio-read-only-question`), and rendering it to PNG (`drawio-export-png`).

The behavioural cases check the written `.drawio` file, not what the reply
claims about it. Each house-style rule is a `regex` grader on the file. A
pattern such as `<mxCell\b(?=[^>]*\bedge="1")(?![^>]*jumpStyle=arc)[^>]*>`
matches an edge tag that breaks the rule, whatever the attribute order, so
`not_contains` means "no edge breaks it". Only the two "did the report say so"
checks use an `llm` grader.

First run, `claude-sonnet-5` with a `claude-haiku-4-5` judge, recorded
2026-11-02:

| Selection | Result | Cost |
| --- | --- | --- |
| `drawio-conventions`, 1 run | 10/11 at 1.00 | $1.79, ~4 min |
| `edit-reports-old-edge` after the fix, 3 runs | 3/3 at 1.00 | $0.49 |
| `drawio-conventions` after the fix and the spacing rules, 1 run | 11/11 at 1.00 | $1.92, ~3 min |

The one failure was real. The checklist said "no edge has `exitX`" without
exempting untouched edges, so the run silently fixed the fixture's old
User -> API edge instead of reporting it. The checklist now covers only the
cells the run added or changed.

No case checks the spacing rules. A regex cannot measure the distance between
shapes. The skill now ships `scripts/check_drawio.py`, which does measure it, but
no grader runs that script on a case's output yet.

Field-feedback update (v1.15.0), 3 runs each, same models, recorded 2026-11-02:

| Run | Result | Cost |
| --- | --- | --- |
| First full run | 9/11 at 1.00 | $7.03 |
| After the `--find` icon lookup | 10/11 at 1.00 | $7.07 |
| After the grader fix and the style strings in `--find` | 11/11 at 1.00 | $6.82 |

Both failures were in `icon-labels-above-lines`. First, runs spent all 20
turns searching the draw.io app files by hand for AWS stencil names. The
script's `--find` option now does that lookup in one call. Second,
`04-icons-after-edges` ignored the parent of each cell, so an icon inside a
group container failed it even though the skill allows that order. The
pattern now uses a backreference to compare parents. The full history is in
`docs/plans/2026-11-02-drawio-conventions-feedback.md`.

Layout update (v1.16.0), 3 runs each, same models, recorded 2026-11-03:

| Selection | Result | Cost |
| --- | --- | --- |
| `gateway-fan-out-notes` (new) | 3/3 at 1.00 | $1.03 |
| `icon-labels-above-lines`, with the new label-position grader | 3/3 at 1.00 | $1.33 |

`gateway-fan-out-notes` gives one shape four outgoing edges and two notes of
very different length. Its graders check that the edges carry waypoints with
`followTerminals=1` instead of fixed points, and that a note has `autosize=1`.
The other cases were not rerun for this update. The decisions are in
`docs/plans/2026-11-03-drawio-conventions-layout-round-2.md`.

`drawio-export-png` ends on the eight-turn cap after trying to render. That is
expected and does not affect the score: the grader only asks whether the skill
was called.

## The fixtures

The sandbox starts each case in an empty directory, so every case builds its
own world first. `fixtures/repo.sh` is a small project with a finished feature
branch; `fixtures/release-repo.sh` adds a second version source, a passing test
script and a bare `origin`, and its history mixes two features, a fix for a bug
introduced on the same branch, and a README typo — so a run that turns four
commits into four changelog bullets has not understood the job.

`fixtures/sessions.sh`, for evaluate-session, carries three synthetic
transcripts and the project they ran in. They are generated by
`session-calibration/make-sessions.py`, which the sync script embeds through an
`@EMBED` line, so the calibration and the evals grade the same sessions.

`fixtures/drawio-repo.sh`, for drawio-conventions, is a small shop project with
a services list, a login flow in prose and a `docs/flow.drawio`. In that diagram
the User -> API edge has hand-drawn fixed connection points, so the edit cases
can check that an untouched old edge is reported rather than silently changed.

A case's `scaffold_script` has to name a file inside its own case directory, so
these cannot be shared by reference. `scripts/sync-eval-fixtures.sh` writes the
copies and `--check` fails when one has drifted. Edit the fixture, never a
generated `scaffold.sh`.

## The gh stub

`version.sh` refuses to start without an authenticated `gh`, and the sandbox's
throwaway home means the real one never is. The behavioural cases set
`EVAL_GH_STUB`, which a wrapper at `~/.local/bin/gh` looks for; without it the
wrapper execs the real binary untouched. `EVAL_*` is the only variable class a
case file may set, so nothing else can switch the stub on by accident.

**That wrapper lives outside this repo**, so the behavioural cases will not
work on another machine until it exists there. The trigger cases need nothing.

## Writing a grader without fooling yourself

Four ways a grader here silently measures nothing. Each one cost a run.

- **`arm: both` on a negative.** Under the default `with-without` ablation a
  `tool_used` grader on `Skill` is treated as a plugin-fired indicator and
  dropped from the score. A "must not fire" case without `arm: both` passes
  while asserting nothing.
- **`min` defaults to 1.** A "must not happen" grader written with only
  `max: 0` becomes `expected 1..0` and fails every run forever. Set both.
- **`input_match` sees serialised JSON.** The skill calls its script by
  absolute path, so the command reads `version.sh\" check` and a pattern of
  `version\.sh\s+check` never matches. Put `\S*` between them.
- **`regex` on `target: trace` cannot tell use from mention.** An assertion
  that `--no-test` never appears failed a run that said *"I'd rather not just
  pass `--no-test`"* — the right answer, marked wrong. When the claim is "the
  skill did not *do* X", use `tool_used`, which only sees tool calls.

## macOS

`/usr/bin/git` is a Command Line Tools shim that writes an `xcrun` cache to a
path the sandbox blocks, so git fails inside every run. Homebrew's git works
but its `bin` entry is skipped, because the sandbox permits executing the
symlink while blocking a read of its Cellar target. A wrapper at
`~/.local/bin/git` that execs `/opt/homebrew/bin/git` fixes it. None of this
applies on Linux, where `/usr/bin/git` is a real binary.
