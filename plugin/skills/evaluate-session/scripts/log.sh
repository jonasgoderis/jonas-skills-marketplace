#!/usr/bin/env bash
# Sourced by hook.sh, evaluate.sh and enable-hook.sh. One line per thing that
# happened to a session at exit — graded, skipped and why, or failed and where —
# because a detached hook that exits quietly is indistinguishable from one that
# never ran.

LOG_NAME="evaluate-session.log"
# A long-running install should not grow a file forever. Trim to the newest half
# once it passes this many lines.
LOG_MAX_LINES=1000

# eval_log FILE SESSION REASON MESSAGE
# An empty FILE means "nowhere to write", which is not an error.
eval_log() {
  local file="$1" session="${2:-?}" reason="${3:-?}" msg="$4"
  [ -n "$file" ] || return 0
  mkdir -p "$(dirname "$file")" 2>/dev/null || return 0
  printf '%s  %-8s  %-17s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" \
    "${session:0:8}" "$reason" "$msg" >> "$file" 2>/dev/null || return 0
  if [ "$(wc -l < "$file" 2>/dev/null || echo 0)" -gt "$LOG_MAX_LINES" ]; then
    tail -n $(( LOG_MAX_LINES / 2 )) "$file" > "$file.tmp" 2>/dev/null \
      && mv "$file.tmp" "$file" 2>/dev/null
  fi
  return 0
}
