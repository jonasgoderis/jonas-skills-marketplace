#!/usr/bin/env bash
# SessionEnd hook entry point, registered by the plugin's hooks/hooks.json.
# Claude Code pipes the hook payload in as JSON on stdin; this pulls out what
# evaluate.sh needs and hands off, detached.
#
# Plugin hooks are live as soon as the plugin is enabled, and grading every
# session spends the user's tokens. So this is off until someone asks for it:
# without the marker file it logs one line and exits, which costs an installer
# who never wanted it a few milliseconds per exit and nothing else.
set -uo pipefail

# The grading run is a Claude session too. Stop here rather than recursing, and
# say nothing: every graded session would otherwise log a second, useless line.
[ -n "${CLAUDE_EVALUATE_SESSION:-}" ] && exit 0

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=log.sh
. "$HERE/log.sh"

# Two locations, because only a real plugin invocation has CLAUDE_PLUGIN_DATA
# set. Enabling from a working checkout writes the other one, and a toggle that
# silently fails to toggle is worse than either path being wrong.
enabled=0
[ -n "${CLAUDE_PLUGIN_DATA:-}" ] && [ -f "$CLAUDE_PLUGIN_DATA/enabled" ] && enabled=1
[ -f "$HOME/.claude/evaluate-session/enabled" ] && enabled=1

PAYLOAD="$(cat)"
TRANSCRIPT="" CWD="" REASON="" SESSION=""
if command -v jq >/dev/null 2>&1; then
  TRANSCRIPT="$(printf '%s' "$PAYLOAD" | jq -r '.transcript_path // empty' 2>/dev/null)"
  CWD="$(printf '%s' "$PAYLOAD" | jq -r '.cwd // empty' 2>/dev/null)"
  REASON="$(printf '%s' "$PAYLOAD" | jq -r '.reason // empty' 2>/dev/null)"
  SESSION="$(printf '%s' "$PAYLOAD" | jq -r '.session_id // empty' 2>/dev/null)"
fi

if [ "$enabled" = 0 ] && [ -z "${EVALUATE_SESSION_FORCE:-}" ]; then
  # Logged only into the plugin's own data directory, which Claude Code creates
  # and removes with the plugin. Someone who never switched this on gets no new
  # folder in their home directory for it.
  [ -n "${CLAUDE_PLUGIN_DATA:-}" ] && eval_log "$CLAUDE_PLUGIN_DATA/$LOG_NAME" \
    "$SESSION" "$REASON" "skipped: automatic grading is off (enable-hook.sh --on)"
  exit 0
fi

LOG="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/evaluate-session}/$LOG_NAME"

command -v jq >/dev/null 2>&1 || {
  eval_log "$LOG" "$SESSION" "$REASON" "skipped: jq is not installed"; exit 0; }
[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] || {
  eval_log "$LOG" "$SESSION" "$REASON" "skipped: no transcript at '${TRANSCRIPT:-<none>}'"; exit 0; }

# Grading a session the user abandoned mid-prompt is as useful as grading one
# they finished, so every reason is accepted. A hook that fires on exit must
# never delay it, so the work is detached. evaluate.sh logs how it ended; a
# "started" line with nothing after it means the run was killed before finishing.
eval_log "$LOG" "$SESSION" "$REASON" "started: grading detached"
nohup "$HERE/evaluate.sh" \
  --transcript "$TRANSCRIPT" \
  --project-dir "${CWD:-$PWD}" \
  --reason "${REASON:-unknown}" \
  --log "$LOG" \
  >/dev/null 2>&1 &

exit 0
