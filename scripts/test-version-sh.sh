#!/usr/bin/env bash
# Unit tests for the release-version skill's version.sh.
#
# version.sh edits other people's manifests and opens pull requests, so the
# parts that can go wrong quietly — version-source detection, semver
# arithmetic, in-place JSON editing, the test gate, the dirty-tree refusal —
# are worth pinning down. Every case builds a throwaway git repo in a temp
# directory, runs version.sh against it with --repo, and asserts. Nothing
# touches the network: a stub `gh` on PATH stands in for the GitHub CLI.
#
# Run it directly. It is not wired into scripts/test.sh, so it gates nothing.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION_SH="$ROOT/plugin/skills/release-version/scripts/version.sh"

fails=0
pass() { printf '  ok    %s\n' "$*"; }
fail() { printf '  FAIL  %s\n' "$*"; fails=$((fails+1)); }

[ -x "$VERSION_SH" ] || { printf 'cannot run: %s is missing or not executable\n' "$VERSION_SH"; exit 1; }

HAVE_JQ=1
command -v jq >/dev/null 2>&1 || HAVE_JQ=0

TMPROOT="$(mktemp -d)"
trap 'rm -rf "$TMPROOT"' EXIT

# ------------------------------------------------------------ the stub gh --
# preflight_tools insists on a `gh` that exists and reports itself
# authenticated. This one does that, records every invocation so a test can
# assert on what was asked of GitHub, and never leaves the machine.
STUBBIN="$TMPROOT/bin"
mkdir -p "$STUBBIN"
cat > "$STUBBIN/gh" <<'STUBEOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "${GH_LOG:-/dev/null}"
case "${1:-}" in
  --version) printf 'gh version 0.0.0 (stub)\n' ;;
  auth)      exit 0 ;;
  repo)      printf 'main\n' ;;
  pr)        printf 'https://example.invalid/pull/1\n' ;;
esac
exit 0
STUBEOF
chmod +x "$STUBBIN/gh"

# ------------------------------------------------------------- the harness --
repo_n=0
REPO_DIR=""

newrepo() {
  repo_n=$((repo_n+1))
  REPO_DIR="$TMPROOT/r$repo_n"
  mkdir -p "$REPO_DIR"
  git -C "$REPO_DIR" init -q -b main
  git -C "$REPO_DIR" config user.email test@example.invalid
  git -C "$REPO_DIR" config user.name  Test
  git -C "$REPO_DIR" config commit.gpgsign false
}

# Gives the repo an origin it can actually push to, plus an origin/main ref.
with_origin() {
  git -C "$REPO_DIR" init -q --bare "$TMPROOT/origin$repo_n.git"
  git -C "$REPO_DIR" remote add origin "$TMPROOT/origin$repo_n.git"
  git -C "$REPO_DIR" push -q -u origin main
}

commit_all() { git -C "$REPO_DIR" add -A && git -C "$REPO_DIR" commit -qm "${1:-commit}"; }

# Runs version.sh against the current fixture, merging stderr into stdout so a
# die() message can be asserted on. Sets VS_OUT and RC as globals rather than
# printing: a command substitution runs in a subshell, so an exit code captured
# there never reaches the caller.
RC=0
VS_OUT=""
vs() {
  # --repo has to follow the subcommand: version.sh takes $1 as the command.
  VS_OUT="$(cd "$REPO_DIR" && PATH="$STUBBIN:$PATH" "$VERSION_SH" "$@" --repo "$REPO_DIR" 2>&1)"
  RC=$?
}
# For inline use where only the output matters and RC is not asserted.
vso() { vs "$@"; printf '%s' "$VS_OUT"; }

check_eq() {
  if [ "$2" = "$3" ]; then pass "$1"; else fail "$1 — expected '$2', got '$3'"; fi
}
check_has() {
  case "$3" in
    *"$2"*) pass "$1" ;;
    *) fail "$1 — no '$2' in: $(printf '%s' "$3" | tr '\n' ' ' | cut -c1-180)" ;;
  esac
}
check_ok()   { if [ "$2" -eq 0 ]; then pass "$1"; else fail "$1 — exited $2"; fi; }
check_fail() { if [ "$2" -ne 0 ]; then pass "$1"; else fail "$1 — expected a non-zero exit"; fi; }
check_clean() {
  local d; d="$(git -C "$REPO_DIR" status --porcelain)"
  if [ -z "$d" ]; then pass "$1"; else fail "$1 — tree is dirty: $(printf '%s' "$d" | tr '\n' ' ')"; fi
}

# ------------------------------------------------------------- 1. detection --
echo "Detection"

detects() { # label, filename, contents
  newrepo
  mkdir -p "$(dirname "$REPO_DIR/$2")"
  printf '%s' "$3" > "$REPO_DIR/$2"
  check_eq "$1" "0.3.0" "$(vso current)"
}

detects "VERSION"                      VERSION        '0.3.0
'
detects "package.json"                 package.json   '{ "name": "x", "version": "0.3.0" }
'
detects "composer.json"                composer.json  '{ "name": "v/x", "version": "0.3.0" }
'
detects "pyproject.toml [project]"     pyproject.toml '[project]
name = "x"
version = "0.3.0"
'
detects "pyproject.toml [tool.poetry]" pyproject.toml '[tool.poetry]
name = "x"
version = "0.3.0"
'
detects "Cargo.toml"                   Cargo.toml     '[package]
name = "x"
version = "0.3.0"
'
if [ "$HAVE_JQ" -eq 1 ]; then
  detects "marketplace.json" .claude-plugin/marketplace.json '{ "name": "m", "plugins": [ { "name": "p", "version": "0.3.0" } ] }
'
  detects "nested plugin.json" plugin/.claude-plugin/plugin.json '{ "name": "p", "version": "0.3.0" }
'
else
  pass "JSON manifests skipped (jq not installed)"
fi

# --------------------------------------------------------- 2. multi-source --
echo "Multiple sources"

newrepo
printf '0.3.0\n' > "$REPO_DIR/VERSION"
printf '{ "name": "x", "version": "0.3.0" }\n' > "$REPO_DIR/package.json"
if [ "$HAVE_JQ" -eq 1 ]; then
  check_eq "two agreeing sources read as one version" "0.3.0" "$(vso current)"
  vs bump minor >/dev/null
  check_eq "both sources bump together" "0.4.0" "$(vso current)"

  newrepo
  printf '0.3.0\n' > "$REPO_DIR/VERSION"
  printf '{ "name": "x", "version": "0.4.0" }\n' > "$REPO_DIR/package.json"
  vs current
  out="$VS_OUT"
  check_fail "disagreeing sources abort"            "$RC"
  check_has  "the abort says they disagree"         "disagree"     "$out"
  check_has  "the abort names VERSION"              "VERSION"      "$out"
  check_has  "the abort names package.json"         "package.json" "$out"
else
  pass "multi-source checks skipped (jq not installed)"
fi

# ---------------------------------------------------------- 3. arithmetic --
echo "Semver arithmetic"

bumps() { # label, start, level, expected
  newrepo
  printf '%s\n' "$2" > "$REPO_DIR/VERSION"
  vs bump "$3" >/dev/null
  check_eq "$1" "$4" "$(vso current)"
}

bumps "patch"                  1.9.0 patch 1.9.1
bumps "minor"                  1.9.0 minor 1.10.0
bumps "major"                  1.9.0 major 2.0.0
bumps "an explicit version"    1.9.0 2.5.3 2.5.3
bumps "minor resets the patch" 1.9.4 minor 1.10.0
bumps "major resets both"      1.9.4 major 2.0.0
bumps "no string ordering"     9.9.9 patch 9.9.10

# ------------------------------------------------------------ 4. refusals --
echo "Refusals"

newrepo
printf '1.0.0-rc1\n' > "$REPO_DIR/VERSION"
vs current
out="$VS_OUT"
check_fail "a prerelease is an error, not something to bump past" "$RC"
check_has  "the message says why" "not a plain MAJOR.MINOR.PATCH" "$out"

newrepo
printf 'banana\n' > "$REPO_DIR/VERSION"
vs current
out="$VS_OUT"
check_fail "a non-version string is an error" "$RC"

newrepo
vs current
out="$VS_OUT"
check_fail "no version source at all is an error" "$RC"
check_has  "it points at init" "init" "$out"

newrepo
printf '1.9.0\n' > "$REPO_DIR/VERSION"
vs bump 1.2
out="$VS_OUT"
check_fail "a two-part level is rejected"    "$RC"
check_has  "it lists the valid levels"       "major | minor | patch" "$out"
vs bump 1.9.0
out="$VS_OUT"
check_fail "bumping to the current version is rejected" "$RC"
vs bump nonsense
out="$VS_OUT"
check_fail "an unknown level is rejected" "$RC"

# ------------------------------------------------------------- 5. dry run --
echo "Dry run"

newrepo
printf '1.9.0\n' > "$REPO_DIR/VERSION"
printf '{ "name": "x", "version": "1.9.0" }\n' > "$REPO_DIR/package.json"
commit_all "initial"
before="$(cksum "$REPO_DIR/VERSION" "$REPO_DIR/package.json")"
vs bump minor --dry-run
out="$VS_OUT"
check_ok  "bump --dry-run succeeds"            "$RC"
check_has "it says what it would do"  "would write" "$out"
check_eq  "it changes no file"        "$before" "$(cksum "$REPO_DIR/VERSION" "$REPO_DIR/package.json")"
check_clean "it leaves the tree clean"

# -------------------------------------------------------- 6. JSON editing --
echo "JSON editing"

if [ "$HAVE_JQ" -eq 1 ]; then
  newrepo
  mkdir -p "$REPO_DIR/.claude-plugin" "$REPO_DIR/plugin/.claude-plugin"
  # Deliberately not jq's formatting: four-space indent, and a long description
  # that a reformat would rewrap. Both must survive the bump untouched.
  cat > "$REPO_DIR/.claude-plugin/marketplace.json" <<'JSONEOF'
{
    "name": "a-marketplace",
    "description": "A description long enough that any reformat would show up in the diff as more than one changed line.",
    "plugins": [
        {
            "name": "a-plugin",
            "version": "1.9.0",
            "source": "./plugin"
        }
    ]
}
JSONEOF
  cat > "$REPO_DIR/plugin/.claude-plugin/plugin.json" <<'JSONEOF'
{
    "name": "a-plugin",
    "version": "1.9.0",
    "keywords": ["one", "two"]
}
JSONEOF
  commit_all "initial"
  vs bump minor >/dev/null
  check_eq "both manifests bump together" "1.10.0" "$(vso current)"

  numstat="$(git -C "$REPO_DIR" diff --numstat)"
  check_has "marketplace.json changes exactly one line" \
            "1	1	.claude-plugin/marketplace.json" "$numstat"
  check_has "plugin.json changes exactly one line" \
            "1	1	plugin/.claude-plugin/plugin.json" "$numstat"

  if jq -e . "$REPO_DIR/.claude-plugin/marketplace.json" >/dev/null 2>&1; then
    pass "the manifest still parses"
  else
    fail "the manifest no longer parses"
  fi
  check_has "the four-space indent survives" \
            '    "name": "a-marketplace",' "$(cat "$REPO_DIR/.claude-plugin/marketplace.json")"
else
  pass "JSON editing skipped (jq not installed)"
fi

# --------------------------------------------------------- 7. the test gate --
echo "The test gate"

# A repo that is ready to release apart from the thing under test.
releasable() { # test-script-body, or "" for no test script
  newrepo
  printf '0.3.0\n' > "$REPO_DIR/VERSION"
  if [ -n "$1" ]; then
    mkdir -p "$REPO_DIR/scripts"
    printf '%s\n' "$1" > "$REPO_DIR/scripts/test.sh"
    chmod +x "$REPO_DIR/scripts/test.sh"
  fi
  commit_all "initial"
  with_origin
  git -C "$REPO_DIR" checkout -q -b feature
  printf 'work\n' > "$REPO_DIR/feature.txt"
  commit_all "Add the feature"
  NOTES="$TMPROOT/notes$repo_n.md"
  printf '### Added\n\n- A feature.\n' > "$NOTES"
}

releasable '#!/bin/sh
exit 1'
vs release patch --notes-file "$NOTES" --title "Release"
out="$VS_OUT"
check_fail  "a failing test command aborts the release" "$RC"
check_has   "it says the tests failed"    "tests failed" "$out"
check_has   "it says nothing was changed" "Nothing has been changed" "$out"
check_clean "the tree is untouched afterwards"
check_eq    "the version is unchanged" "0.3.0" "$(vso current)"

releasable ""
vs release patch --notes-file "$NOTES" --title "Release"
out="$VS_OUT"
check_fail "no discoverable test command stops the release" "$RC"
check_has  "it offers --test-cmd" "--test-cmd" "$out"
check_has  "it offers --no-test"  "--no-test"  "$out"
check_clean "the tree is untouched afterwards"

releasable '#!/bin/sh
exit 0'
vs release patch --notes-file "$NOTES" --title "Release" --dry-run
out="$VS_OUT"
check_ok   "a passing test command lets the dry run through" "$RC"
check_has  "the tests actually ran" "Tests passed" "$out"

# ------------------------------------------------------------ 8. repo state --
echo "Repo state"

releasable '#!/bin/sh
exit 0'
printf 'scratch\n' > "$REPO_DIR/junk.txt"
vs release patch --notes-file "$NOTES" --title "Release" --dry-run
out="$VS_OUT"
check_fail "uncommitted work is not swept into the release" "$RC"
check_has  "it names the offending path" "junk.txt" "$out"
rm -f "$REPO_DIR/junk.txt"

releasable '#!/bin/sh
exit 0'
git -C "$REPO_DIR" checkout -q main
vs release patch --notes-file "$NOTES" --title "Release" --dry-run
out="$VS_OUT"
check_fail "combined mode refuses to release from the base branch" "$RC"
check_has  "it suggests the alternative" "--mode release" "$out"

releasable '#!/bin/sh
exit 0'
GH_LOG="$TMPROOT/gh$repo_n.log"; export GH_LOG
vs release patch --notes-file "$NOTES" --title "Release v0.3.1"
out="$VS_OUT"
unset GH_LOG
check_ok  "a full release run succeeds"            "$RC"
check_eq  "the version was written"      "0.3.1"   "$(vso current)"
check_eq  "the bump is its own commit"   "Release v0.3.1" \
          "$(git -C "$REPO_DIR" log -1 --format=%s)"
check_eq  "it touches only the version sources and the changelog" \
          "CHANGELOG.md VERSION" \
          "$(git -C "$REPO_DIR" show --name-only --format= HEAD | sort | tr '\n' ' ' | sed 's/ $//')"
check_has "the changelog entry was prepended" "## [0.3.1]" "$(cat "$REPO_DIR/CHANGELOG.md")"
check_has "a PR was opened through gh" "pr create" "$(cat "$TMPROOT/gh$repo_n.log")"

# --------------------------------------------------------------- 9. PR body --
echo "The PR body"

releasable '#!/bin/sh
exit 0'
vs release patch --notes-file "$NOTES" --title "Release" --dry-run
out="$VS_OUT"
check_has "it records the test command that ran" 'Tests: `scripts/test.sh` passed' "$out"
check_has "it records the version transition"    'Version: `0.3.0` → `0.3.1`'      "$out"
check_has "it carries the notes"                 "A feature."                      "$out"
check_has "nothing was pushed"                   "would run: git"                  "$out"

releasable '#!/bin/sh
exit 0'
vs release patch --notes-file "$NOTES" --title "Release" --dry-run --no-test
out="$VS_OUT"
check_has "skipping tests is recorded in the PR body" 'Tests: **skipped**' "$out"

# ----------------------------------------------------- 10. temporary files --
echo "Temporary files"

# Found by the behavioural eval, not by these tests: BSD mktemp ignores TMPDIR
# for a bare invocation and writes to /var/folders, which sandboxes and locked
# down CI runners do not allow. The release then dies on a scratch file. This
# is a structural check because the failure only shows up somewhere TMPDIR is
# the only writable temp directory, which is not here.
if grep -qE '\$\(mktemp\)' "$VERSION_SH"; then
  fail "a bare mktemp ignores TMPDIR on macOS and fails inside a sandbox"
else
  pass "every temporary file honours TMPDIR"
fi

# ------------------------------------------------------------------- done --
echo
if [ "$fails" -eq 0 ]; then
  echo "All checks passed."
  exit 0
fi
echo "$fails check(s) failed."
exit 1
