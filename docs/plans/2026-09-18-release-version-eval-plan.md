# Plan: evaluating release-version

Decided 2026-09-18. Implements **Option D** from
`2026-09-18-release-version-eval.md`. Read that document first for why the work
splits the way it does.

Settled decisions:

- **The suite lives at `plugin/evals/`**, the tool's default. No `--eval-dir`
  anywhere, `claude plugin eval init` writes to the right place, and commands
  stay short. The cost is that the cases ship to anyone who installs the
  plugin — accepted.
- **Nothing gates a release for now.** Neither the eval suite nor the
  `version.sh` unit tests are wired into `scripts/test.sh`; both are run
  deliberately. Phase 1 records the exact line to add whenever that changes.

Four phases, cheapest and most protective first. Each is independently useful
and can be stopped after without leaving anything half-built.

---

## Phase 0 — Measure before committing to a suite size — DONE 2026-09-22

Run on CLI **2.1.278** (the proposal was written against 2.1.276). Five
calibration runs, total spend well under a euro. Config errors cost $0, so
iterating on case files is free — only runs that reach the model are billed.

### Cost per run

| Shape | Turns | Cost |
| --- | --- | --- |
| Trigger case, no `Bash`, no scaffold | 3 | **$0.053** |
| Trigger case, `Bash` + scaffolded repo | 5 | **$0.095** |

Judge cost was $0 — no `llm` grader in either. Under the default `with-without`
ablation both arms run, so roughly double. **Budget for Phase 2: eight cases ×
three runs × two arms at ~$0.10 ≈ $5 per full suite run**, less in practice
because the negative cases stop earlier. That is cheap enough that the suite
size in Phase 2 stands as planned — no need to cut to six.

### Finding 1 — the sandbox workspace is empty, so every case needs a scaffold

The first calibration run failed its grader, and the trace showed why: the
working directory contains no repo and no files. Given "I think we're ready to
ship this", the agent globbed, found nothing, and asked what to ship. The
plugin *was* loaded — `claude-skills:release-version` appeared in the run's
slash commands and `Skill` was available — so the skill was offered and
correctly declined. There was nothing to release.

That invalidates the scaffold-free trigger suite this plan assumed. A release
prompt has no referent in an empty directory, so a positive trigger case there
tests whether the model hallucinates a release, which we want it *not* to do.

**Consequence:** `--scaffold` and `--allow-tools Bash` move from Phase 3 into
Phase 2. Trigger cases and behavioural cases share one fixture, and Phase 3
stops being "the phase that needs a scaffold" — it becomes "the phase with the
harder graders". Re-run with a fixture repo, the same prompt scored **1.0**:
the skill fired as the very first tool call, then went straight to
`version.sh check`.

### Finding 2 — `scaffold_script` is a path inside the case directory

Not inline bash (an inline script is read as a filename), and not a shared
path: `../fixtures/repo.sh` is rejected with *"escapes the case directory (`..`
or an absolute path) — it must name something inside it"*. Each case directory
needs its own copy of the scaffold.

**Consequence:** the shared fixture cannot be shared by reference. Generate it
instead — one source of truth plus a script that writes it into every case
directory that needs it, so the duplication is mechanical rather than
hand-maintained. That is the repo's own `scripts/` principle applied to the
eval suite. This is the first Phase 2 todo.

A directory under `evals/` with no `case.yaml` and no `prompt.md` is correctly
ignored by case discovery, so a `fixtures/` directory alongside the cases is
safe if a later layout wants one.

### Finding 3 — `max_turns: 4` is too low once a scaffold exists

The scaffolded run ended with *"Reached maximum number of turns (4)"*. The
grader still passed, because the skill fires on turn one, but an errored run is
noise in the report and the error would mask a real failure. Trigger cases want
`max_turns: 8`.

### Reference: the case and grader schema, confirmed from the binary

Worth recording so it is not re-derived. `prompt.md` frontmatter rejects unknown
keys outright, and the accepted sets are:

- **case-level:** `schema_version`, `name`, `description`, `tags`, `plugins`,
  `runs` (default 3, max 50), `expected_outcome`
- **execution-level:** `model`, `max_turns` (default 10), `timeout_seconds`
  (default 300), `allowed_tools`, `artifact_publish`, `growthbook_overrides`,
  `append_system_prompt`, `env`
- **`case.yaml` only:** `context.scaffold_script`, `context.history_file`,
  `context.add_dirs`; requires `schema_version` (current is `"1.1"`)

Grader frontmatter, all types also taking `name`, `weight` (default 1) and
`arm`:

| Type | Fields |
| --- | --- |
| `regex` | `target` (`trace`\|`last_message`\|`files`\|`mock_calls`\| `{source: file, path: …}`), `pattern`, `flags`, `match` (`contains`\|`not_contains`\|`count:N`) |
| `tool_used` | `tool`, `input_match`, `min`, `max` |
| `tool_order` | `before`, `after` (each a tool name or `{tool, input_match}`) |
| `file_exists` | `path`, `exists` (default true) |
| `llm` | `criteria`, `focus` |
| `baseline` | `baseline_file`, `criteria` |

`arm` is `with-only` \| `both` with **no default**, which confirms the trap:
negative trigger cases need `arm: both` written out. And `regex` accepting
`target: {source: file, path: …}` is what makes Phase 3's "assert `gh.log` is
empty" implementable.

### Reference: result JSON shape

Per-run results live at `cases[].arms.with[]` (and `.without[]`), **not**
`cases[].runs[]` as the 2026-09-16 document's gating sketch assumed. Each entry
carries `score`, `passed`, `turns`, `costUsd`, `judgeCostUsd`, `error`,
`tracePath` and a `graders[]` array with `explanation`. Top level has `costUsd`,
`durationSeconds`, `partial` and `aggregates`.

`--keep-temp` is how you read a trace, but it seals the kept workspace at mode
000; inspecting it needs a `chmod 700` on the directory and its `sealed` child.

### Landed in this phase

- `plugin/evals/ready-to-ship/` — the first real Phase 2 positive case, scoring
  1.0: `case.yaml`, `prompt.md`, `scaffold.sh`, `graders/skill-fired.md`.
- `plugin/evals/results/` added to `.gitignore`.

---

## Phase 1 — `version.sh` unit tests (free, no model) — DONE 2026-09-22

The dangerous half. A wrong `write_version` silently corrupts a manifest in
someone else's repo; no amount of trigger accuracy compensates for that.

**New file:** `scripts/test-version-sh.sh` — plain bash, no `bats` dependency,
matching the `pass`/`fail`/`fails` idiom already in `scripts/test.sh` so the
output reads the same and it can be folded in later without a rewrite. Each case
builds a throwaway repo under the session scratchpad, runs
`version.sh --repo <that>`, asserts, and tears down.

Helpers the file needs:

- `mkrepo` — `git init`, an initial commit, a configurable set of version
  sources, a local bare `origin` in the temp dir.
- `stub_gh` — a `gh` on `PATH` that logs argv to a file and exits 0, so
  `preflight_tools` passes and `release` can be exercised without GitHub.

Cases, grouped:

**Detection** — one repo per source kind, asserting `current` finds it:
`VERSION`, `package.json`, `composer.json`, `pyproject.toml` under `[project]`,
`pyproject.toml` under `[tool.poetry]` only, `Cargo.toml`,
`.claude-plugin/marketplace.json`, a nested `*/.claude-plugin/plugin.json`.

**Multi-source** — two sources agreeing bump together to the same value; two
disagreeing abort non-zero and name both files in the message.

**Arithmetic** — `1.9.0` + `minor` → `1.10.0`; + `major` → `2.0.0`; + `patch` →
`1.9.1`; explicit `2.5.3` is taken verbatim; `9.9.9` + `patch` → `9.9.10` (no
string sorting).

**Refusals** — a source holding `1.0.0-rc1` is an error, not something bumped
past; a non-semver string is an error; an explicit level of `1.2` is rejected.

**Dry run** — `bump --dry-run` changes no file (assert via `git status
--porcelain` empty and a checksum of each source before and after).

**JSON editing** — bump a hand-formatted `marketplace.json` with unusual
indentation; assert `git diff --numstat` shows exactly one changed line per file
and the rest is byte-identical. This is the claim the skill makes in prose and
the one most likely to regress.

**Test gate** — a repo whose `scripts/test.sh` exits 1: `release` aborts
non-zero and `git status --porcelain` is empty afterwards (tree untouched, no
branch created). A repo with no discoverable test command: `release` stops and
the message names `--test-cmd` and `--no-test`.

**Repo state** — a dirty tree is refused by `release`; after a successful
`release`, the version bump is its own commit (`git log -1 --stat` touches only
the sources and `CHANGELOG.md`).

**PR body** — with a passing test command, the body rendered by `--dry-run`
contains the command and that it passed; with `--no-test`, it says tests were
skipped. Assert on the dry-run output, not on a real PR.

### Outcome

`scripts/test-version-sh.sh`, 65 checks, all passing in about 20 seconds with no
API key and no network. Every case builds a throwaway repo under `mktemp -d`
and runs `version.sh --repo <it>`; a stub `gh` on `PATH` reports itself
authenticated, logs its argv so a test can assert on what was asked of GitHub,
and never leaves the machine.

**No `version.sh` bugs surfaced.** The three failures found along the way were
all in the test harness:

- `--repo` has to follow the subcommand — `version.sh` takes `$1` as the
  command, so `version.sh --repo X current` is an unknown-command error. Worth
  knowing; the SKILL.md usage block shows it correctly but it is easy to get
  backwards.
- A helper that captured the exit code inside a command substitution never saw
  it — the subshell's `RC` assignment does not reach the caller, so every
  negative assertion was reading a stale `0` and passing regardless. This is the
  bug that makes a test suite worthless while looking green; it is why the
  harness now sets `VS_OUT`/`RC` as globals and keeps a separate `vso` for the
  cases that only want output.
- The fixture committed its test script on the feature branch, so the
  base-branch test tripped the test gate first and asserted the wrong refusal.

A suite that passes on its first honest run deserves suspicion, so it was
mutation-tested. Three deliberate breaks in `version.sh`, all caught:

| Mutation | Caught by |
| --- | --- |
| `minor` stops resetting the patch | *minor resets the patch* — got `1.10.4` |
| JSON manifests always take the `jq` reformat path | *changes exactly one line* — got 9/9 and 6/3 — and *the four-space indent survives* |
| The dirty-tree refusal is dropped | *uncommitted work is not swept into the release* |

The JSON mutation is the one worth noting: it reproduces exactly the failure the
skill's prose promises against, and the diff-size assertion catches it cleanly.

`claude plugin validate plugin --strict` passes as well.

**Not wired into `scripts/test.sh`.** The script stands alone and is run on
purpose. The hook, for whenever that changes, is one section in `scripts/test.sh`
running `scripts/test-version-sh.sh` and adding its exit status to `fails`.
Worth knowing what that decision costs: an unwired test script is one nobody
runs, so Phase 4 puts it in the README and it is on us to run it before a
release by hand.

`claude plugin validate plugin --strict` is worth running for the same reason
and gates nothing either — Phase 4 documents it alongside.

---

## Phase 2 — Trigger suite — DONE 2026-09-22

Eight cases, three runs each: **6/8, $1.99, 65 seconds** at `--concurrency 4`.
Both failures are consistent (0/3), not stochastic.

| Case | Kind | 3 runs |
| --- | --- | --- |
| `ready-to-ship` | fires | pass, pass, pass |
| `next-version` | fires | pass, pass, pass |
| `out-the-door` | fires | **FAIL, FAIL, FAIL** |
| `write-the-changelog` | fires | **FAIL, FAIL, FAIL** |
| `bump-a-dependency` | silent | pass, pass, pass |
| `node-version-question` | silent | pass, pass, pass |
| `what-changed` | silent | pass, pass, pass |
| `open-a-pr` | silent | pass, pass, pass |

### The finding: the description promises two things it does not deliver

Both failures are phrasings the frontmatter explicitly claims:

- *"…say the work is done and ready to go out"* — but **"The work's done — get
  it out the door."** never fires the skill.
- *"prepare release notes or a changelog entry"* — but **"Write the changelog
  for this branch."** never fires it. The agent runs `git log`, reads the diff
  and writes the changelog itself, in two turns.

All four negatives hold, including the near miss (*"Create a PR for this
work."*), so the description is not simply too narrow — it is mis-aimed. It
over-indexes on the release *decision* and under-indexes on the release
*artifacts*.

### The fix, and what the failures actually were

Re-running the two failures with traces showed two different causes, and the
first one was mine:

- **`out-the-door`** was confounded by the fixture. With no `origin`, "get it
  out the door" has nowhere to go: the agent checked, found no remote and no
  `gh` auth, and reasonably offered a local merge instead. That tested the
  fixture, not the skill. The fixture now creates a bare `origin` in the
  sandbox's own `TMPDIR` and pushes `main` to it. **With a coherent fixture the
  case still failed** — and told us something better: the agent announced
  *"pushing the branch and opening a PR against `main`"* and ran `git push`
  itself, never consulting the skill. That is precisely the outcome the skill
  exists to prevent.
- **`write-the-changelog`** needed no fixture change. The agent ran `git log`,
  read the diff and wrote the changelog inline, in two turns.

So both failures share one root cause, and it is not vocabulary — the phrases
*"get a finished branch out the door"* and *"prepare release notes or a
changelog entry"* were already in the description, word for word. Both requests
**look like one-step jobs**, so the model simply does them. This is the
mechanism `skill-creator` documents: Claude declines to consult a skill for work
it believes it can handle directly, however well the description matches.

The fix was to stop listing topics and give the model the reason: those requests
read like one-step jobs, and doing them by hand skips the manifest sync, the
test gate and the approval step. One sentence protects the near miss —
*"A pull request for work still in progress is not a release; finishing
something and sending it out is."* — because the rest of the change pushes hard
towards pull requests and `open-a-pr` must stay silent.

### Result: 8/8

| Case | Kind | Before | After |
| --- | --- | --- | --- |
| `ready-to-ship` | fires | 3/3 | 3/3 |
| `next-version` | fires | 3/3 | 3/3 |
| `out-the-door` | fires | **0/3** | **3/3** |
| `write-the-changelog` | fires | **0/3** | **3/3** |
| `bump-a-dependency` | silent | 3/3 | 3/3 |
| `node-version-question` | silent | 3/3 | 3/3 |
| `what-changed` | silent | 3/3 | 3/3 |
| `open-a-pr` | silent | 3/3 | 3/3 |

24 of 24 runs, `overallScore` 1.0, $2.61, 128 seconds.

**Caveat worth keeping.** The description was tuned against these eight cases
and now scores full marks on them, so the suite is both the test and the target.
A perfect score here is evidence the two specific gaps closed without breaking
the negatives — not evidence the description is good in general. Held-out
phrasings the description was not written against would be the honest next
check, and are worth adding before trusting the number.

### Resolved: git inside the sandbox

The blocker recorded earlier is fixed, and the cause is worth keeping.

`/opt/homebrew/bin` **is** on the sandbox PATH, ahead of `/usr/bin` — the
sandbox inherits the operator's PATH rather than synthesising one. But
`/opt/homebrew/bin/git` is a symlink into `Cellar`, and the sandbox blocks
*reading* that target while permitting *exec* of it. So the shell's PATH lookup
skips the entry and falls through to `/usr/bin/git`, the Command Line Tools
shim that cannot write its xcrun cache. `/opt/homebrew/bin/git --version` works
when called directly; plain `git` does not.

The fix is a two-line wrapper at `~/.local/bin/git` (first on that PATH, owned
by the operator, no `sudo`) that `exec`s `/opt/homebrew/bin/git`. Outside the
sandbox it resolves to the same binary the shell already picks, so it changes
nothing on the host. Removing it: `rm ~/.local/bin/git`.

Effect on the suite: xcrun errors per run 14 → 0, the worst case 16 turns → 2,
and a full 8-case single-run pass 103s/$1.03 → 21s/$0.64.

Routes that do **not** work, so nobody retries them: `execution.env` in a case
(only `EVAL_*` keys are accepted); `DEVELOPER_DIR` or `PATH` exported from the
operator shell (stripped by the env allowlist); a shell profile written into the
sandbox home by the scaffold (the files land correctly but the sandbox does not
source them). This is macOS-only — on Linux `/usr/bin/git` is a real binary.

### Decision: `--ablation none` for the trigger suite

The no-plugin baseline arm is meaningless here. Without the plugin the skill
cannot fire, so every positive fails the baseline by construction — which is
exactly why a `tool_used: Skill` grader is treated as with-only under
`with-without`. Running one arm halves the cost and loses nothing. The
behavioural cases in Phase 3 may want the baseline back.

`plugin/evals/`, one directory per case: `case.yaml` (for the scaffold),
`prompt.md`, `scaffold.sh`, and `graders/skill-fired.md`.

Phase 0 moved the fixture here. Every case runs `--scaffold --allow-tools Bash`
against the same throwaway repo — a `VERSION` at `0.3.0`, a short history, and
a feature branch with a commit on it — because without one the prompts have no
referent and the skill is right not to fire. `max_turns: 8`.

The first todo is `scripts/sync-eval-fixtures.sh`, which writes the canonical
scaffold into each case directory, since `scaffold_script` cannot point outside
its own case. `ready-to-ship` already exists from Phase 0 and becomes the first
of the four positives once the sync script owns its `scaffold.sh`.

**Positive cases** (`tool_used` on `Skill`, `input_match` on
`"skill"\s*:\s*"(?:[\w-]+:)?release-version"`, default `min: 1`):

- "I think we're ready to ship this." — **done, scores 1.0** (`ready-to-ship`)
- "What should the next version be?"
- "Write the changelog for this branch."
- "The work's done — get it out the door."

**Negative cases** (`min: 0, max: 0`, **`arm: both`** — without that they are
excluded from scoring under the default ablation and pass while asserting
nothing):

- "Bump the lodash dependency to the latest."
- "What Node version does this project need?"
- "What changed since Friday?"
- "Create a PR for this work." — the near-miss that matters: opening a PR is
  something the skill does, but not something it should own.

Eight cases at `--runs 3` is 24 runs plus the baseline arm — about **$5** at
the rates Phase 0 measured. Cheap enough to keep all eight.

These prompts ship with the plugin, so keep them generic: no client names, no
internal paths, nothing that only makes sense on this machine. The four above
already satisfy that.

Run the suite, read the failures, and fold any description changes back into
`SKILL.md`. Per `CLAUDE.md`, load `anthropic-skills:skill-creator` before
editing the description — it is a non-trivial change to a skill, and description
tuning is what that skill is for.

---

## Phase 3 — Behavioural cases — DONE 2026-09-22

Two cases against a richer fixture (`fixtures/release-repo.sh`): four commits
mixing two features, a fix for a bug introduced on the same branch, and a README
typo; two version sources; a passing `scripts/test.sh`; and a bare `origin` in
the sandbox's `TMPDIR`. `no-test-command` reuses that fixture with a snippet
appended, so the two cannot drift apart.

Full suite, ten cases: **overallScore 0.98, 9/10 cases at 1.0**, $1.25 for a
single-run pass. Per-case at three runs: `no-test-command` 1.0,
`cut-a-release` 0.87.

| Grader | Case | 3 runs |
| --- | --- | --- |
| `ran-check` | cut-a-release | pass ×3 |
| `read-the-commits` | cut-a-release | pass ×3 |
| `no-pr-opened` | cut-a-release | pass ×3 |
| `version-not-hand-edited` | cut-a-release | pass ×3 |
| `changelog-reads-the-diff` (llm) | cut-a-release | 1–2 of 3 |
| `did-not-skip-the-tests` | no-test-command | pass ×3 |
| `raised-the-missing-tests` (llm) | no-test-command | pass ×3 |

### The gh stub

`version.sh`'s preflight needs `gh` present and authenticated or the run stops
before anything worth measuring. The sandbox has a throwaway home, so the real
`gh` is never authenticated there, and its PATH cannot be changed from a case.

The wrapper at `~/.local/bin/gh` (first on that PATH) `exec`s the real binary
unless `EVAL_GH_STUB` is set — and `execution.env` in a case may set `EVAL_*`
keys and nothing else, so only these case files can switch it on. Outside an
eval it is a pass-through; the host `gh` stays authenticated and unchanged.
It logs argv to `gh.log` in the workspace, which the fixture adds to
`.git/info/exclude` so it cannot dirty the tree and trip `version.sh`'s refusal
to sweep uncommitted work into a release.

### Two real defects found

**`version.sh` used bare `mktemp`.** BSD `mktemp` resolves a bare invocation
through `_CS_DARWIN_USER_TEMP_DIR` and ignores `TMPDIR`, so it writes to
`/var/folders` — outside the allowlist of any sandbox, and of locked-down CI.
The first behavioural run had to shim `mktemp` onto `PATH` to get the release to
run at all. Eight call sites now go through a `tmpfile()` helper that passes an
explicit template. Turns for that case dropped 17 → 8 and cost halved.
`scripts/test-version-sh.sh` pins it structurally, because the failure only
appears somewhere `TMPDIR` is the sole writable temp directory.

**The notes could understate a release.** Twice, a run collapsed two new
features into one line phrased as though the first already existed — "the app
now prints a parting message *after its greeting*", when the greeting was also
new on that branch. Collapsing commits is right; dropping one of them is not.
`SKILL.md` gained a line saying so.

### Grader footguns, all found the hard way

Three ways a grader here silently measures nothing or the wrong thing. Each
cost a run to find, so they are worth stating.

- **`min` defaults to 1.** A "must not happen" grader written with only
  `max: 0` becomes `expected 1..0` and fails every run, forever. Both `min: 0`
  and `max: 0` are needed. The mirror image of the `arm: both` trap: that one
  passes while asserting nothing, this one fails while asserting nothing.
- **`input_match` runs against the serialised JSON tool input.** The skill
  invokes its script by absolute path, so the command contains
  `version.sh\" check` — a pattern of `version\.sh\s+check` never matches.
  `\S*` between them does.
- **A `regex` grader on `target: trace` cannot tell use from mention.** An
  assertion that `--no-test` never appears failed a run whose actual words were
  *"I'd rather not just pass `--no-test` and quietly release"* — exemplary
  behaviour, marked wrong. The same mistake failed a run for explaining why it
  had excluded the README typo. Where the claim is "the skill did not *do* X",
  `tool_used` with `min: 0, max: 0` is the right instrument, because it only
  ever sees tool calls.

### The llm grader is advisory, not a gate

`changelog-reads-the-diff` is the one grader that will not settle. It has
earned its place — it twice caught the understated-notes defect above, which no
deterministic grader could see — but across six three-run sittings it scored
anywhere from 0/3 to 2/3 on output a careful reader would accept, and moving it
between `focus: last_message` and `focus: trace` changed the verdict more than
the skill's behaviour did.

That matches what this plan assumed at the outset: judge verdicts get noisier
the longer the text, and release notes sit right at the edge. Two consequences
worth honouring rather than tuning away:

- **Do not run the behavioural cases at `--threshold 1.0`.** With every
  deterministic grader green, `cut-a-release` still lands at 0.8–0.87. That is
  the healthy steady state, not a regression.
- **Read a failure before believing it.** The four deterministic graders on
  that case have not produced a false result once. The judge has produced
  several.

One case change was legitimate rather than tuning: the prompt now asks to see
the proposed notes, because the run does not always repeat them in its final
message and the judge was being asked to grade text that was not there.

## Phase 4 — Wiring and documentation

- **New file:** `scripts/eval.sh` — wraps `claude plugin eval plugin` with
  `--trust-plugin`, pinned `--model` and `--judge-model`, `--no-publish`,
  `--max-cost-usd` and `--json`. Pinning the models matters: unpinned, results
  drift under you and a regression looks like a model change. `--no-publish` is
  not optional here — the report would otherwise go to claude.ai carrying repo
  paths and commit text.
- `plugin/evals/README.md`: how to run the suite, what the stub `gh` is for, why
  the negatives need `arm: both`, and the cost figure from Phase 0.
- Repo `README.md` (or `CLAUDE.md`, whichever documents the test story): the
  three commands that exist and when to run each — `scripts/test.sh` before a
  release, `scripts/test-version-sh.sh` after touching `version.sh`,
  `scripts/eval.sh` after touching a skill description. Since none of them gate,
  this note is the only thing keeping them alive.
- Update `2026-09-16-skill-evaluation.md` with a pointer to this plan, so the
  older survey does not read as the current state.
- `.gitignore`: add `plugin/evals/results/` — timestamped run output does not
  belong in git, and it would otherwise ship with the plugin.

---

## Todo list

Phase 0 — done
1. ~~Measure the cost of one trivial eval run; record the figure in this file.~~

Phase 1 — done
2. ~~Write `scripts/test-version-sh.sh` with the `mkrepo` and `stub_gh` helpers.~~
3. ~~Add the detection, multi-source, arithmetic and refusal cases.~~
4. ~~Add the dry-run and JSON-editing cases.~~
5. ~~Add the test-gate, repo-state and PR-body cases.~~
6. ~~Run it; fix whatever `version.sh` bugs it surfaces.~~ None surfaced; mutation-tested instead.

Phase 2 — done
7. ~~Write `scripts/sync-eval-fixtures.sh` and let it own `ready-to-ship/scaffold.sh`.~~
8. ~~Add the three remaining positive trigger cases.~~
9. ~~Add the four negative cases with `arm: both`.~~
10. ~~Run the suite; record the results.~~
11. ~~If triggering is wrong, tune the description via `anthropic-skills:skill-creator` and re-run.~~ 6/8 → 8/8.

Phase 3 — done
12. ~~Grow the fixture: richer history, `marketplace.json`, passing `scripts/test.sh`, bare `origin`, stub `gh`.~~
13. ~~Author case 1 with its seven graders.~~ Five; two were unassertable.
14. ~~Author case 2 (no test command).~~
15. ~~Run both; debug the fixture until they run clean.~~

Phase 4
16. Write `scripts/eval.sh` with pinned models and `--no-publish`.
17. Write `plugin/evals/README.md`.
18. Document the three commands and when to run each.
19. ~~Add `plugin/evals/results/` to `.gitignore`~~ (done in Phase 0); cross-reference this plan from the 2026-09-16 doc.
20. Release the work with `/release-version` — a `minor` bump, and a live test of the skill being evaluated.

---

## Out of scope

- The other three skills. The 2026-09-16 document covers them and nothing here
  changes its conclusions, including that `session-handoff` is not evaluable
  with this tooling.
- Running evals in GitHub Actions. They need an API key in CI and a cost
  ceiling, and that is a separate decision from having a suite at all.
- Testing `version.sh tag`, which needs a merged PR to be meaningful.
