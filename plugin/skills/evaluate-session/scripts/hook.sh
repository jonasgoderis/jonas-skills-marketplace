#!/usr/bin/env bash
# SessionEnd hook entry point, registered by the plugin's hooks/hooks.json.
# Claude Code pipes the hook payload in as JSON on stdin; this pulls out what
# evaluate.sh needs and hands off, detached.
#
# Plugin hooks are live as soon as the plugin is enabled, and grading every
# session spends the user's tokens. So this is off until someone asks for it:
# without the marker file it exits immediately, which costs an installer who
# never wanted it a few milliseconds per exit and nothing else.
set -uo pipefail

# Two locations, because only a real plugin invocation has CLAUDE_PLUGIN_DATA
# set. Enabling from a working checkout writes the other one, and a toggle that
# silently fails to toggle is worse than either path being wrong.
enabled=0
[ -n "${CLAUDE_PLUGIN_DATA:-}" ] && [ -f "$CLAUDE_PLUGIN_DATA/enabled" ] && enabled=1
[ -f "$HOME/.claude/evaluate-session/enabled" ] && enabled=1
[ "$enabled" = 1 ] || [ -n "${EVALUATE_SESSION_FORCE:-}" ] || exit 0

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
