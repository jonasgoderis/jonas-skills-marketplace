#!/usr/bin/env bash
# version.sh — deterministic version bumping and release PRs.
#
# All state-changing mechanics live here so they are reproducible and reviewable.
# The calling model supplies only prose: the PR title and the changelog body.
#
#   version.sh check                       preflight: tools, auth, repo, version sources
#   version.sh current                     print the current version
#   version.sh test                        run the project's test command
#   version.sh init [X.Y.Z]                create a VERSION file if no source exists
#   version.sh bump <level> [--dry-run]    write the new version to every source
#   version.sh release <level> --notes-file F --title T [flags]
#       runs the project's tests first; --test-cmd overrides, --no-test skips
#   version.sh tag [X.Y.Z]                 tag the current commit after a merge
#
# <level> is major | minor | patch | an explicit X.Y.Z
set -euo pipefail

PROG="${0##*/}"
REPO="$(pwd)"
DRY_RUN=0
MODE="combined"
NOTES_FILE=""
PR_TITLE=""
BRANCH=""
BASE=""
WRITE_CHANGELOG=1
DRAFT=0
RUN_TESTS=1
TEST_CMD=""
TEST_REPORT=""

die()  { printf '%s: error: %s\n' "$PROG" "$*" >&2; exit 1; }
warn() { printf '%s: %s\n' "$PROG" "$*" >&2; }
say()  { printf '%s\n' "$*"; }
run()  { if [ "$DRY_RUN" -eq 1 ]; then printf '  would run: %s\n' "$*"; else "$@"; fi; }

# ---------------------------------------------------------------- preflight --

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is not installed. $2"
}

preflight_tools() {
  need_cmd git "Install it with: xcode-select --install"
  need_cmd gh  "Install the GitHub CLI: brew install gh — then run: gh auth login"
  gh auth status >/dev/null 2>&1 \
    || die "gh is installed but not authenticated. Run: gh auth login"
}

preflight_repo() {
  git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 \
    || die "$REPO is not a git repository."
  git -C "$REPO" remote get-url origin >/dev/null 2>&1 \
    || die "no 'origin' remote. Add one before releasing."
}

need_jq_for() {
  command -v jq >/dev/null 2>&1 \
    || die "jq is required to read/write $1. Install it: brew install jq"
}

# ------------------------------------------------------------------ sources --

# Emits "kind<TAB>relative-path", sorted, for every version source in the repo.
detect_sources() {
  (
    cd "$REPO"
    [ -f VERSION ]        && printf 'plain\tVERSION\n'
    [ -f package.json ]   && printf 'json:.version\tpackage.json\n'
    [ -f composer.json ]  && printf 'json:.version\tcomposer.json\n'
    [ -f pyproject.toml ] && printf 'toml:project\tpyproject.toml\n'
    [ -f Cargo.toml ]     && printf 'toml:package\tCargo.toml\n'
    [ -f .claude-plugin/marketplace.json ] \
      && printf 'json:.plugins[].version\t.claude-plugin/marketplace.json\n'
    find . -maxdepth 4 -type f -name plugin.json -path '*/.claude-plugin/*' \
      -not -path './.git/*' -not -path '*/node_modules/*' 2>/dev/null \
      | sed 's|^\./||' | sort \
      | while read -r p; do printf 'json:.version\t%s\n' "$p"; done
    true
  )
}

# read_version <kind> <path> -> one version per line (may be several for a glob kind)
read_version() {
  local kind="$1" path="$2" f="$REPO/$2"
  case "$kind" in
    plain)
      printf '%s\n' "$(head -n1 "$f" | tr -d '[:space:]')"
      ;;
    json:.version)
      need_jq_for "$path"
      jq -r '.version // empty' "$f"
      ;;
    'json:.plugins[].version')
      need_jq_for "$path"
      jq -r '.plugins[]?.version // empty' "$f"
      ;;
    toml:*)
      local sect="${kind#toml:}"
      toml_read "$f" "$sect"
      ;;
    *) die "unknown source kind: $kind" ;;
  esac
}

# pyproject has two conventional homes for the version; try both.
toml_read() {
  local f="$1" sect="$2" v
  v="$(awk -v s="[$sect]" '
    /^\[/ { inside = ($0 == s) }
    inside && /^[[:space:]]*version[[:space:]]*=/ {
      match($0, /"[^"]*"/); if (RSTART) { print substr($0, RSTART+1, RLENGTH-2); exit }
    }' "$f")"
  if [ -z "$v" ] && [ "$sect" = "project" ]; then
    v="$(awk -v s="[tool.poetry]" '
      /^\[/ { inside = ($0 == s) }
      inside && /^[[:space:]]*version[[:space:]]*=/ {
        match($0, /"[^"]*"/); if (RSTART) { print substr($0, RSTART+1, RLENGTH-2); exit }
      }' "$f")"
  fi
  printf '%s\n' "$v"
}

write_version() {
  local kind="$1" path="$2" new="$3" f="$REPO/$2" tmp
  tmp="$(mktemp)"
  case "$kind" in
    plain)
      printf '%s\n' "$new" > "$tmp"
      ;;
    json:*)
      json_write "$kind" "$path" "$new"
      rm -f "$tmp"
      return 0
      ;;
    toml:*)
      local sect="${kind#toml:}"
      toml_write "$f" "$sect" "$new" > "$tmp"
      ;;
  esac
  [ -s "$tmp" ] || { rm -f "$tmp"; die "refusing to write an empty $path"; }
  mv "$tmp" "$f"
}

# JSON manifests are edited in place with sed so the diff shows one changed line
# and nothing else; hand-formatted files survive a release untouched. jq is the
# fallback, and the result is always read back to confirm it actually landed.
json_write() {
  local kind="$1" path="$2" new="$3" f="$REPO/$2" cur esc backup tmp
  need_jq_for "$path"
  cur="$(read_version "$kind" "$path" | head -n1)"
  backup="$(mktemp)"; tmp="$(mktemp)"
  cp "$f" "$backup"
  esc="$(printf '%s' "$cur" | sed 's/[.[\*^$()+?{|]/\\&/g')"
  sed -E "s/(\"version\"[[:space:]]*:[[:space:]]*)\"$esc\"/\\1\"$new\"/g" "$f" > "$tmp"
  if [ -s "$tmp" ]; then
    mv "$tmp" "$f"
    if [ "$(read_version "$kind" "$path" | sort -u)" = "$new" ] && jq -e . "$f" >/dev/null 2>&1; then
      rm -f "$backup"; return 0
    fi
  fi
  cp "$backup" "$f"; rm -f "$backup" "$tmp"
  tmp="$(mktemp)"
  case "$kind" in
    json:.version)             jq --indent 2 --arg v "$new" '.version = $v' "$f" > "$tmp" ;;
    'json:.plugins[].version') jq --indent 2 --arg v "$new" '.plugins |= map(.version = $v)' "$f" > "$tmp" ;;
  esac
  [ -s "$tmp" ] || { rm -f "$tmp"; die "refusing to write an empty $path"; }
  mv "$tmp" "$f"
}

toml_write() {
  local f="$1" sect="$2" new="$3" out
  out="$(awk -v s="[$sect]" -v v="$new" '
    /^\[/ { inside = ($0 == s) }
    inside && !done && /^[[:space:]]*version[[:space:]]*=/ {
      sub(/=.*/, "= \"" v "\""); done = 1
    }
    { print }
    END { exit done ? 0 : 3 }' "$f")" && { printf '%s\n' "$out"; return 0; }
  if [ "$sect" = "project" ]; then
    awk -v s="[tool.poetry]" -v v="$new" '
      /^\[/ { inside = ($0 == s) }
      inside && !done && /^[[:space:]]*version[[:space:]]*=/ {
        sub(/=.*/, "= \"" v "\""); done = 1
      }
      { print }
      END { exit done ? 0 : 3 }' "$f"
    return $?
  fi
  return 3
}

# Plain MAJOR.MINOR.PATCH only. Prereleases are deliberately not supported: they
# need their own ordering rules, and a project that does not cut them should not
# pay for the ambiguity.
valid_semver() {
  printf '%s' "$1" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'
}

# The single current version, or a hard failure if the sources disagree.
current_version() {
  local sources found="" v
  sources="$(detect_sources)"
  [ -n "$sources" ] || die "no version source found in $REPO. Run: $PROG init"
  while IFS="$(printf '\t')" read -r kind path || [ -n "$kind" ]; do
    [ -n "${kind:-}" ] || continue
    while read -r v || [ -n "$v" ]; do
      [ -n "$v" ] || continue
      valid_semver "$v" || die "$path holds '$v', which is not a plain MAJOR.MINOR.PATCH version."
      found="$found$v
"
    done < <(read_version "$kind" "$path")
  done <<< "$sources"
  found="$(printf '%s' "$found" | sort -u)"
  [ -n "$found" ] || die "version sources exist but none of them carries a version."
  if [ "$(printf '%s\n' "$found" | wc -l | tr -d ' ')" -gt 1 ]; then
    printf '%s: error: version sources disagree:\n' "$PROG" >&2
    list_sources >&2
    printf 'Reconcile them by hand, then run this again.\n' >&2
    exit 1
  fi
  printf '%s\n' "$found"
}

list_sources() {
  local kind path v
  while IFS="$(printf '\t')" read -r kind path || [ -n "$kind" ]; do
    [ -n "${kind:-}" ] || continue
    while read -r v || [ -n "$v" ]; do
      [ -n "$v" ] || continue
      printf '  %-44s %s\n' "$path" "$v"
    done < <(read_version "$kind" "$path")
  done <<< "$(detect_sources)"
}

next_version() {
  local cur="$1" level="$2" core major minor patch
  if valid_semver "$level"; then printf '%s\n' "$level"; return 0; fi
  IFS=. read -r major minor patch <<< "$cur"
  case "$level" in
    major) major=$((major+1)); minor=0; patch=0 ;;
    minor) minor=$((minor+1)); patch=0 ;;
    patch) patch=$((patch+1)) ;;
    *) die "unknown bump level '$level'. Use: major | minor | patch | X.Y.Z" ;;
  esac
  printf '%s.%s.%s\n' "$major" "$minor" "$patch"
}

# Finds the project's own test command. Nothing clever: the first convention that
# matches wins, and the order is fixed so two runs never disagree.
detect_test_cmd() {
  local d="$REPO"
  if [ -f "$d/scripts/test.sh" ]; then printf 'scripts/test.sh\n'; return 0; fi
  if [ -f "$d/test.sh" ];         then printf './test.sh\n';       return 0; fi
  if [ -f "$d/package.json" ] && command -v jq >/dev/null 2>&1 \
     && [ -n "$(jq -r '.scripts.test // empty' "$d/package.json")" ]; then
    if   [ -f "$d/pnpm-lock.yaml" ];     then printf 'pnpm test\n'
    elif [ -f "$d/yarn.lock" ];          then printf 'yarn test\n'
    elif [ -f "$d/bun.lockb" ];          then printf 'bun test\n'
    else printf 'npm test\n'; fi
    return 0
  fi
  if [ -f "$d/Makefile" ] && grep -Eq '^test:' "$d/Makefile"; then printf 'make test\n'; return 0; fi
  if [ -f "$d/Cargo.toml" ];                      then printf 'cargo test\n';  return 0; fi
  if [ -f "$d/go.mod" ];                          then printf 'go test ./...\n'; return 0; fi
  if [ -f "$d/pytest.ini" ] || [ -f "$d/tox.ini" ] \
     || { [ -f "$d/pyproject.toml" ] && [ -d "$d/tests" ]; }; then
    printf 'pytest\n'; return 0
  fi
  return 1
}

# Runs the tests and stops the release if they fail. Sets TEST_REPORT to the line
# that goes into the PR body, so the PR never implies a green run that never
# happened.
run_tests() {
  local cmd=""
  if [ "$RUN_TESTS" -eq 0 ]; then
    TEST_REPORT='Tests: **skipped** (`--no-test`)'
    warn "tests skipped — the PR will say so."
    return 0
  fi
  cmd="${TEST_CMD:-$(detect_test_cmd || true)}"
  if [ -z "$cmd" ]; then
    die "no test command detected. Pass --test-cmd '<command>', or --no-test to release without one."
  fi
  say "Running tests: $cmd"
  if [ "$DRY_RUN" -eq 1 ]; then
    say "  would run them for real; running now to prove the release would be green"
  fi
  if ( cd "$REPO" && eval "$cmd" ); then
    TEST_REPORT="Tests: \`$cmd\` passed"
    say "Tests passed."
  else
    die "tests failed ($cmd). Nothing has been changed."
  fi
}

default_branch() {
  local b
  b="$(git -C "$REPO" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null || true)"
  b="${b##*/}"
  [ -n "$b" ] || b="$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || true)"
  [ -n "$b" ] || b="main"
  printf '%s\n' "$b"
}

# Paths this script itself is allowed to touch, so it can tell a dirty tree apart
# from its own edits.
owned_paths() {
  detect_sources | cut -f2
  printf 'CHANGELOG.md\n'
}

# ------------------------------------------------------------------ changelog --

write_changelog() {
  local new="$1" notes="$2" f="$REPO/CHANGELOG.md" entry tmp line
  entry="$(mktemp)"; tmp="$(mktemp)"
  {
    printf '## [%s] - %s\n\n' "$new" "$(date +%Y-%m-%d)"
    cat "$notes"
    printf '\n'
  } > "$entry"

  if [ ! -f "$f" ]; then
    { printf '# Changelog\n\n'; cat "$entry"; } > "$tmp"
  else
    line="$(grep -n '^## ' "$f" | head -n1 | cut -d: -f1 || true)"
    if [ -n "$line" ]; then
      head -n "$((line-1))" "$f" > "$tmp"
      cat "$entry" >> "$tmp"
      tail -n "+$line" "$f" >> "$tmp"
    else
      cat "$f" > "$tmp"; printf '\n' >> "$tmp"; cat "$entry" >> "$tmp"
    fi
  fi
  mv "$tmp" "$f"
  rm -f "$entry"
}

# ------------------------------------------------------------------ commands --

# check reports every problem it finds rather than stopping at the first one,
# then exits non-zero if anything would block a release.
cmd_check() {
  local problems=0
  if command -v gh >/dev/null 2>&1; then
    say "gh:             $(gh --version | head -n1)"
    if gh auth status >/dev/null 2>&1; then
      say "gh auth:        ok"
    else
      say "gh auth:        NOT AUTHENTICATED — run: gh auth login"; problems=1
    fi
  else
    say "gh:             NOT INSTALLED — run: brew install gh && gh auth login"; problems=1
  fi
  command -v jq >/dev/null 2>&1 \
    && say "jq:             $(jq --version)" \
    || { say "jq:             not installed (only needed for JSON manifests)"; }

  say "repo:           $REPO"
  if git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1; then
    say "branch:         $(git -C "$REPO" rev-parse --abbrev-ref HEAD)"
    if git -C "$REPO" remote get-url origin >/dev/null 2>&1; then
      say "origin:         $(git -C "$REPO" remote get-url origin)"
      say "default branch: $(default_branch)"
    else
      say "origin:         MISSING — add a remote before releasing"; problems=1
    fi
    local dirty
    dirty="$(git -C "$REPO" status --porcelain | wc -l | tr -d ' ')"
    say "working tree:   $([ "$dirty" = 0 ] && echo clean || echo "$dirty uncommitted path(s)")"
  else
    say "git:            NOT A REPOSITORY"; problems=1
  fi

  local tcmd
  tcmd="$(detect_test_cmd || true)"
  if [ -n "$tcmd" ]; then
    say "tests:          $tcmd"
  else
    say "tests:          none detected — release needs --test-cmd or --no-test"
  fi

  if [ -z "$(detect_sources)" ]; then
    say "version source: none — run '''$PROG init''' to create a VERSION file"
  else
    say "version sources:"
    list_sources
  fi
  return $problems
}

cmd_test() {
  run_tests
}

cmd_current() {
  current_version
}

cmd_init() {
  local start="${1:-0.1.0}"
  valid_semver "$start" || die "'$start' is not a MAJOR.MINOR.PATCH version."
  local sources
  sources="$(detect_sources)"
  if [ -n "$sources" ]; then
    say "A version source already exists; nothing to create:"
    list_sources
    return 0
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    say "would create $REPO/VERSION at $start"
    return 0
  fi
  printf '%s\n' "$start" > "$REPO/VERSION"
  say "Created VERSION at $start"
}

cmd_bump() {
  local level="${1:-}" cur new kind path
  [ -n "$level" ] || die "usage: $PROG bump <major|minor|patch|X.Y.Z>"
  cur="$(current_version)"
  new="$(next_version "$cur" "$level")"
  [ "$new" != "$cur" ] || die "$new is already the current version."
  say "$cur -> $new"
  while IFS="$(printf '\t')" read -r kind path || [ -n "$kind" ]; do
    [ -n "${kind:-}" ] || continue
    if [ "$DRY_RUN" -eq 1 ]; then
      say "  would write $path"
    else
      write_version "$kind" "$path" "$new"
      say "  wrote $path"
    fi
  done <<< "$(detect_sources)"
}

cmd_release() {
  local level="${1:-}"
  [ -n "$level" ] || die "usage: $PROG release <level> --notes-file F --title T"
  [ -n "$NOTES_FILE" ] || die "--notes-file is required: the changelog body for this release."
  [ "$NOTES_FILE" = "-" ] || [ -f "$NOTES_FILE" ] || die "notes file not found: $NOTES_FILE"

  preflight_tools
  preflight_repo

  local notes
  notes="$(mktemp)"
  if [ "$NOTES_FILE" = "-" ]; then cat > "$notes"; else cat "$NOTES_FILE" > "$notes"; fi
  [ -s "$notes" ] || die "the notes file is empty; a release PR needs a description."

  local cur new base cur_branch dirty
  cur="$(current_version)"
  new="$(next_version "$cur" "$level")"
  [ "$new" != "$cur" ] || die "$new is already the current version."
  base="${BASE:-$(default_branch)}"
  cur_branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD)"

  # Uncommitted work is never swept into a release commit. Version and changelog
  # files are the exception: those are this script's own output.
  dirty="$(git -C "$REPO" status --porcelain -- . \
           | cut -c4- \
           | grep -vxF -f <(owned_paths) || true)"
  if [ -n "$dirty" ]; then
    printf '%s: error: uncommitted changes present:\n%s\n' "$PROG" "$dirty" >&2
    die "commit or stash them first — the version bump is committed on its own."
  fi

  run_tests

  if [ "$MODE" = "release" ]; then
    run git -C "$REPO" fetch origin "$base"
    BRANCH="${BRANCH:-release/v$new}"
    run git -C "$REPO" checkout -b "$BRANCH" "origin/$base"
  else
    if [ "$cur_branch" = "$base" ]; then
      die "you are on $base. In combined mode the PR carries your work, so switch to a feature branch first (or use --mode release)."
    fi
    BRANCH="$cur_branch"
    git -C "$REPO" rev-parse --verify --quiet "origin/$base" >/dev/null 2>&1 \
      || run git -C "$REPO" fetch origin "$base"
    if [ "$(git -C "$REPO" rev-list --count "origin/$base..HEAD" 2>/dev/null || echo 0)" = "0" ]; then
      warn "no commits on $BRANCH ahead of origin/$base — the PR will contain only the version bump."
    fi
  fi

  say "Releasing $cur -> $new on branch $BRANCH (base $base, mode $MODE)"

  local kind path
  while IFS="$(printf '\t')" read -r kind path || [ -n "$kind" ]; do
    [ -n "${kind:-}" ] || continue
    if [ "$DRY_RUN" -eq 1 ]; then say "  would write $path"
    else write_version "$kind" "$path" "$new"; say "  wrote $path"; fi
  done <<< "$(detect_sources)"

  if [ "$WRITE_CHANGELOG" -eq 1 ]; then
    if [ "$DRY_RUN" -eq 1 ]; then say "  would prepend the $new entry to CHANGELOG.md"
    else write_changelog "$new" "$notes"; say "  wrote CHANGELOG.md"; fi
  fi

  local -a files=()
  while IFS= read -r path || [ -n "$path" ]; do
    [ -n "$path" ] || continue
    [ -e "$REPO/$path" ] && files+=("$path")
  done <<< "$(owned_paths)"

  run git -C "$REPO" add -- "${files[@]}"
  run git -C "$REPO" commit -m "Release v$new" -m "$(head -n 20 "$notes")"
  run git -C "$REPO" push -u origin "$BRANCH"

  local body title
  body="$(mktemp)"
  { cat "$notes"
    printf '\n\n---\n\nVersion: `%s` → `%s`  \n%s\n' "$cur" "$new" "$TEST_REPORT"
  } > "$body"
  title="${PR_TITLE:-Release v$new}"

  if [ "$DRY_RUN" -eq 1 ]; then
    say "  would open a PR: $title"
    say "--- PR body ---"; cat "$body"; say "--- end ---"
    rm -f "$body" "$notes"
    return 0
  fi

  local -a pr_args=(pr create --base "$base" --head "$BRANCH" --title "$title" --body-file "$body")
  [ "$DRAFT" -eq 1 ] && pr_args+=(--draft)
  if ! ( cd "$REPO" && gh "${pr_args[@]}" ); then
    warn "the bump is committed and $BRANCH is pushed, but opening the PR failed."
    warn "the PR body is kept at $body — open it by hand with:"
    warn "  gh pr create --base $base --head $BRANCH --title '$title' --body-file $body"
    rm -f "$notes"
    exit 1
  fi
  rm -f "$body" "$notes"
  say "Released $new. Tag it after the merge: $PROG tag $new"
}

cmd_tag() {
  preflight_tools
  preflight_repo
  local v="${1:-}"
  [ -n "$v" ] || v="$(current_version)"
  valid_semver "$v" || die "'$v' is not a MAJOR.MINOR.PATCH version."
  git -C "$REPO" rev-parse --verify --quiet "refs/tags/v$v" >/dev/null 2>&1 \
    && die "tag v$v already exists."
  run git -C "$REPO" tag -a "v$v" -m "v$v"
  run git -C "$REPO" push origin "v$v"
  say "Tagged v$v"
}

# ---------------------------------------------------------------------- main --

[ $# -gt 0 ] || { sed -n '3,15p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
CMD="$1"; shift

ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)       DRY_RUN=1 ;;
    --mode)          MODE="${2:-}"; shift ;;
    --mode=*)        MODE="${1#*=}" ;;
    --notes-file)    NOTES_FILE="${2:-}"; shift ;;
    --notes-file=*)  NOTES_FILE="${1#*=}" ;;
    --title)         PR_TITLE="${2:-}"; shift ;;
    --title=*)       PR_TITLE="${1#*=}" ;;
    --branch)        BRANCH="${2:-}"; shift ;;
    --branch=*)      BRANCH="${1#*=}" ;;
    --base)          BASE="${2:-}"; shift ;;
    --base=*)        BASE="${1#*=}" ;;
    --repo)          REPO="${2:-}"; shift ;;
    --repo=*)        REPO="${1#*=}" ;;
    --no-changelog)  WRITE_CHANGELOG=0 ;;
    --no-test)       RUN_TESTS=0 ;;
    --test-cmd)      TEST_CMD="${2:-}"; shift ;;
    --test-cmd=*)    TEST_CMD="${1#*=}" ;;
    --draft)         DRAFT=1 ;;
    -h|--help)       sed -n '3,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --*)             die "unknown flag: $1" ;;
    *)               ARGS+=("$1") ;;
  esac
  shift
done

case "$MODE" in combined|release) ;; *) die "--mode must be 'combined' or 'release'" ;; esac
[ -d "$REPO" ] || die "no such directory: $REPO"
REPO="$(cd "$REPO" && pwd)"

case "$CMD" in
  check)   cmd_check ;;
  test)    cmd_test ;;
  current) cmd_current ;;
  init)    cmd_init ${ARGS[@]+"${ARGS[@]}"} ;;
  bump)    cmd_bump ${ARGS[@]+"${ARGS[@]}"} ;;
  release) cmd_release ${ARGS[@]+"${ARGS[@]}"} ;;
  tag)     cmd_tag ${ARGS[@]+"${ARGS[@]}"} ;;
  *)       die "unknown command '$CMD'. Use: check | current | test | init | bump | release | tag" ;;
esac
