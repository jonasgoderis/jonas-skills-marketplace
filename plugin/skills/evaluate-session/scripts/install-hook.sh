#!/usr/bin/env bash
# Install, inspect or remove the SessionEnd hook that grades each session.
#
# Opt-in by design. A hook that fires on every exit spends the user's tokens
# without them asking, so installing it is a decision they make once, out loud,
# rather than something a plugin turns on by being installed.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
HOOK_CMD="$HERE/hook.sh"
SCOPE="user"
ACTION=""
ASSUME_YES=0

usage() {
  cat <<'USAGE'
install-hook.sh --install | --status | --uninstall [--scope user|project] [--yes]

  --install     add the SessionEnd hook
  --status      report whether it is installed, and where
  --uninstall   remove it again
  --scope       user (~/.claude/settings.json, the default) or
                project (.claude/settings.json in the current directory)
  --yes         skip the confirmation prompt
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --install|--status|--uninstall) ACTION="${1#--}"; shift ;;
    --scope) SCOPE="${2:-}"; shift 2 ;;
    --yes|-y) ASSUME_YES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "install-hook: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$ACTION" ] || { usage >&2; exit 2; }
command -v jq >/dev/null 2>&1 || { echo "install-hook: jq is required" >&2; exit 2; }

case "$SCOPE" in
  user)    SETTINGS="$HOME/.claude/settings.json" ;;
  project) SETTINGS="$PWD/.claude/settings.json" ;;
  *) echo "install-hook: --scope must be user or project" >&2; exit 2 ;;
esac

installed_cmd() {
  [ -f "$SETTINGS" ] || return 1
  jq -e --arg c "$HOOK_CMD" \
    '(.hooks.SessionEnd // []) | map(.hooks // []) | flatten
     | map(select(.command == $c)) | length > 0' "$SETTINGS" >/dev/null 2>&1
}

case "$ACTION" in
  status)
    if installed_cmd; then
      echo "installed in $SETTINGS"
      exit 0
    fi
    # An entry pointing at another copy of this skill still grades every session.
    if [ -f "$SETTINGS" ] && jq -e '(.hooks.SessionEnd // []) | length > 0' "$SETTINGS" >/dev/null 2>&1; then
      echo "not installed in $SETTINGS, but other SessionEnd hooks are present:"
      jq -r '(.hooks.SessionEnd // []) | map(.hooks // []) | flatten | .[].command // empty' "$SETTINGS" | sed 's/^/  /'
      exit 1
    fi
    echo "not installed in $SETTINGS"
    exit 1
    ;;

  install)
    [ -x "$HOOK_CMD" ] || { echo "install-hook: $HOOK_CMD is missing or not executable" >&2; exit 2; }
    if installed_cmd; then
      echo "already installed in $SETTINGS"
      exit 0
    fi
    mkdir -p "$(dirname "$SETTINGS")" || exit 2
    [ -f "$SETTINGS" ] || printf '{}\n' > "$SETTINGS"
    jq -e . "$SETTINGS" >/dev/null 2>&1 || {
      echo "install-hook: $SETTINGS is not valid JSON; refusing to edit it" >&2; exit 2; }

    # Merged into whatever SessionEnd hooks already exist rather than replacing
    # them — other hooks in this file are not ours to remove.
    NEW="$(jq --arg c "$HOOK_CMD" \
      '.hooks //= {} | .hooks.SessionEnd //= []
       | .hooks.SessionEnd += [{"hooks":[{"type":"command","command":$c}]}]' "$SETTINGS")" || exit 2

    echo "About to add to $SETTINGS:"
    echo "  SessionEnd -> $HOOK_CMD"
    echo
    echo "Every session that ends will be graded. That is one model call per"
    echo "session, roughly 6,000 input tokens on Haiku — a fraction of a cent."
    if [ "$ASSUME_YES" -eq 0 ]; then
      printf 'Add it? [y/N] '
      read -r reply < /dev/tty || reply=""
      case "$reply" in y|Y|yes|YES) ;; *) echo "nothing changed"; exit 1 ;; esac
    fi

    cp "$SETTINGS" "$SETTINGS.bak" || exit 2
    printf '%s\n' "$NEW" > "$SETTINGS" || exit 2
    echo "installed; previous settings saved to $SETTINGS.bak"
    ;;

  uninstall)
    if ! installed_cmd; then
      echo "not installed in $SETTINGS"
      exit 1
    fi
    # Drop only entries naming this command, then drop groups left empty.
    NEW="$(jq --arg c "$HOOK_CMD" \
      '.hooks.SessionEnd = ((.hooks.SessionEnd // [])
         | map(.hooks = ((.hooks // []) | map(select(.command != $c))))
         | map(select((.hooks | length) > 0)))
       | if (.hooks.SessionEnd | length) == 0 then del(.hooks.SessionEnd) else . end' "$SETTINGS")" || exit 2
    cp "$SETTINGS" "$SETTINGS.bak" || exit 2
    printf '%s\n' "$NEW" > "$SETTINGS" || exit 2
    echo "removed from $SETTINGS; previous settings saved to $SETTINGS.bak"
    ;;
esac
