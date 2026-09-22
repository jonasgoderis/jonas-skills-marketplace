#!/usr/bin/env bash
# SessionEnd hook entry point. Claude Code pipes the hook payload in as JSON on
# stdin; this pulls out what evaluate.sh needs and hands off, detached.
#
# Kept separate from the settings entry so the command stored in settings.json
# stays one readable path instead of an unreadable inline pipeline.
set -uo pipefail

# The grading run is a Claude session too. Stop here rather than recursing.
[ -n "${CLAUDE_EVALUATE_SESSION:-}" ] && exit 0

command -v jq >/dev/null 2>&1 || exit 0

PAYLOAD="$(cat)"
TRANSCRIPT="$(printf '%s' "$PAYLOAD" | jq -r '.transcript_path // empty')"
CWD="$(printf '%s' "$PAYLOAD" | jq -r '.cwd // empty')"
REASON="$(printf '%s' "$PAYLOAD" | jq -r '.reason // empty')"

[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] || exit 0

# Grading a session the user abandoned mid-prompt is as useful as grading one
# they finished, so every reason is accepted. A hook that fires on exit must
# never delay it, so the work is detached and its output discarded.
HERE="$(cd "$(dirname "$0")" && pwd)"
nohup "$HERE/evaluate.sh" \
  --transcript "$TRANSCRIPT" \
  --project-dir "${CWD:-$PWD}" \
  --reason "${REASON:-unknown}" \
  >/dev/null 2>&1 &

exit 0
