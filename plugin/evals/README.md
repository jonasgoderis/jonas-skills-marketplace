# Eval suite for the release-version skill

Twelve cases run by `claude plugin eval`. Eight ask whether the skill fires when
it should and stays quiet when it should not; four drive it through an actual
release and check what it does on the way. Two of those four are about the docs
check: `stale-docs` must document a flag the README misses and leave a dated plan
alone, and `internal-fix-no-docs` must not invent doc work for an internal change.

```sh
scripts/eval.sh              # everything
scripts/eval.sh trigger      # the eight trigger cases, ~$1 at one run each
scripts/eval.sh behaviour    # the four behavioural cases
scripts/eval.sh out-the-door --runs 1 --keep-temp
```

Anything after the selector is passed through to `claude plugin eval`.

## What to expect

A healthy run is **every case at 1.00 except `cut-a-release`, which lands at
0.80–0.87**. That case carries the one judge-scored grader in the suite, and it
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

## The fixtures

The sandbox starts each case in an empty directory, so every case builds its
own world first. `fixtures/repo.sh` is a small project with a finished feature
branch; `fixtures/release-repo.sh` adds a second version source, a passing test
script and a bare `origin`, and its history mixes two features, a fix for a bug
introduced on the same branch, and a README typo — so a run that turns four
commits into four changelog bullets has not understood the job.

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
