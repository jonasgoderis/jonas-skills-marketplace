#!/usr/bin/env bash
# Switch automatic grading on or off, and check that it works.
#
# The hook itself is registered by the plugin's hooks/hooks.json and is always
# present once the plugin is enabled. All this does is create or remove the
# marker file that hook.sh looks for, so nothing is ever written to settings.json
# and there is no path anywhere that can go stale.
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
# Written to the plugin's data directory when it is known, and always to the
# fixed path as well, so the hook finds it whichever way it is invoked. Both
# survive plugin updates.
MARKER_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/evaluate-session}"
MARKER="$MARKER_DIR/enabled"
FALLBACK="$HOME/.claude/evaluate-session/enabled"
ACTION=""

usage() {
  cat <<'USAGE'
enable-hook.sh --on | --off | --status | --test

  --on       grade every session from now on
  --off      stop grading automatically; /evaluate-session still works
  --status   report whether automatic grading is on
  --test     grade this project's most recent session now, through the same
             entry point the hook uses
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --on|--off|--status|--test) ACTION="${1#--}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "enable-hook: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[ -n "$ACTION" ] || { usage >&2; exit 2; }

# ~/.claude/projects holds one directory per project, named for its path with
# every character that is not a letter or digit replaced by a dash.
latest_transcript() {
  local dir
  dir="$HOME/.claude/projects/$(printf '%s' "$1" | sed 's/[^A-Za-z0-9]/-/g')"
  [ -d "$dir" ] || return 1
  find "$dir" -maxdepth 1 -name '*.jsonl' -type f -exec stat -f '%m %N' {} + 2>/dev/null \
    | sort -rn | head -1 | cut -d' ' -f2-
}

case "$ACTION" in
  status)
    if [ -f "$MARKER" ] || [ -f "$FALLBACK" ]; then
      echo "on — every session that ends is graded"
      [ -f "$MARKER" ]   && echo "marker: $MARKER"
      [ -f "$FALLBACK" ] && [ "$MARKER" != "$FALLBACK" ] && echo "marker: $FALLBACK"
      exit 0
    fi
    echo "off — nothing is graded automatically; /evaluate-session still works"
    exit 1
    ;;

  on)
    if [ -f "$MARKER" ] || [ -f "$FALLBACK" ]; then echo "already on"; exit 0; fi
    stamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    mkdir -p "$MARKER_DIR" && printf '%s\n' "$stamp" > "$MARKER" || exit 2
    mkdir -p "$(dirname "$FALLBACK")" && printf '%s\n' "$stamp" > "$FALLBACK" || exit 2
    echo "on — every session that ends is now graded."
    echo "That is one model call per session, roughly 6,000 input tokens on"
    echo "Haiku, a fraction of a cent. Switch it off with --off."
    ;;

  off)
    if [ ! -f "$MARKER" ] && [ ! -f "$FALLBACK" ]; then echo "already off"; exit 0; fi
    rm -f "$MARKER" "$FALLBACK" || exit 2
    echo "off — nothing is graded automatically. Scorecards already written are kept."
    ;;

  test)
    LATEST="$(latest_transcript "$PWD")" || {
      echo "enable-hook: no transcripts for this project" >&2; exit 1; }
    [ -n "$LATEST" ] && [ -f "$LATEST" ] || {
      echo "enable-hook: no session transcript found" >&2; exit 1; }

    echo "transcript: $(basename "$LATEST")"
    [ -f "$MARKER" ] || echo "note: automatic grading is off, so the real hook would stop here"

    scorecards() { find "$HOME/.claude/scorecards" -maxdepth 1 -name '*.md' \
                     ! -name 'index.md' 2>/dev/null; }
    newest_scorecard() {
      # -newermt returns matches in directory order, not by time, so sort.
      scorecards -exec stat -f '%m %N' {} + 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-
    }
    BEFORE="$(scorecards | wc -l | tr -d ' ')"
    # Run through hook.sh with the marker forced on, so this exercises the same
    # payload parsing and detached hand-off the real SessionEnd hook uses.
    printf '{"session_id":"test","transcript_path":"%s","cwd":"%s","reason":"prompt_input_exit"}' \
      "$LATEST" "$PWD" | CLAUDE_PLUGIN_DATA="$MARKER_DIR" EVALUATE_SESSION_FORCE=1 \
      bash "$SKILL_DIR/scripts/hook.sh"
    echo "hook returned $? immediately (grading runs detached)"

    echo -n "waiting for a scorecard"
    for _ in $(seq 1 30); do
      sleep 5
      AFTER="$(scorecards | wc -l | tr -d ' ')"
      if [ "$AFTER" -gt "$BEFORE" ]; then
        echo
        echo "wrote: $(newest_scorecard)"
        exit 0
      fi
      echo -n "."
    done
    echo
    echo "no scorecard after 150s. A session under the minimum turn count is" >&2
    echo "skipped on purpose; otherwise run evaluate.sh directly to see the error." >&2
    exit 1
    ;;
esac
