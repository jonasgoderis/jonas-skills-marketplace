#!/usr/bin/env bash
# evaluate-session SessionEnd launcher.
#
# Exists so settings.json holds one stable path. Pointing settings straight at
# the skill bakes in a location that moves: a plugin copy lives under a
# version-numbered directory and is replaced on every update, and a working
# checkout can be renamed or sit somewhere else on another machine. A hook whose
# path has gone stale fails silently, which is the worst way for this to break.
#
# This file is identical on every machine, so it can be tracked in a dotfiles
# repo alongside the other hooks rather than generated per machine. Anything
# machine-specific lives in the optional path file read below.
#
# Resolution order: an environment override, then the newest installed plugin
# copy, then a checkout named in ~/.claude/hooks/evaluate-session.path.
set -uo pipefail

candidates=()

[ -n "${EVALUATE_SESSION_SKILL:-}" ] && candidates+=("$EVALUATE_SESSION_SKILL")

# Newest version first. Paths share a prefix, so a version sort orders them.
while IFS= read -r d; do
  [ -n "$d" ] && candidates+=("$d")
done < <(find "$HOME/.claude/plugins/cache" -maxdepth 4 -type d \
           -path '*/skills/evaluate-session' 2>/dev/null | sort -V -r)

# A working checkout, for developing the skill before it is released. One line,
# a path. Machine-specific by nature, so keep it out of version control.
PATH_FILE="${XDG_CONFIG_HOME:-$HOME/.claude}/hooks/evaluate-session.path"
[ -f "$HOME/.claude/hooks/evaluate-session.path" ] && PATH_FILE="$HOME/.claude/hooks/evaluate-session.path"
if [ -f "$PATH_FILE" ]; then
  while IFS= read -r line; do
    case "$line" in ''|'#'*) continue ;; esac
    candidates+=("$line")
  done < "$PATH_FILE"
fi

for c in "${candidates[@]}"; do
  if [ -x "$c/scripts/hook.sh" ]; then
    exec "$c/scripts/hook.sh"
  fi
done

# Nothing resolved. Exit cleanly: a session ending is not the moment to complain.
exit 0
