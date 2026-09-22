#!/usr/bin/env bash
# Install, inspect or remove the SessionEnd hook that grades each session.
#
# Opt-in by design. A hook that fires on every exit spends the user's tokens
# without them asking, so installing it is a decision they make once, out loud,
# rather than something a plugin turns on by being installed.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$HERE/.." && pwd)"
# settings.json gets one stable, machine-independent path; the launcher behind it
# resolves the skill at run time. See assets/hook-launcher.sh for why.
LAUNCHER_DIR="$HOME/.claude/hooks"
LAUNCHER="$LAUNCHER_DIR/evaluate-session.sh"
HOOK_CMD="~/.claude/hooks/evaluate-session.sh"
SCOPE="user"
ACTION=""
ASSUME_YES=0

usage() {
  cat <<'USAGE'
install-hook.sh --install | --status | --uninstall | --test [--scope user|project] [--yes]

  --install     add the SessionEnd hook
  --status      report whether it is installed, and where
  --uninstall   remove it again
  --test        fire the installed hook against this project's most recent
                session, exactly as Claude Code would on exit
  --scope       user (~/.claude/settings.json, the default) or
                project (.claude/settings.json in the current directory)
  --yes         skip the confirmation prompt
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --install|--status|--uninstall|--test) ACTION="${1#--}"; shift ;;
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
  jq -e '(.hooks.SessionEnd // []) | map(.hooks // []) | flatten
     | map(select((.command // "") | test("evaluate-session"))) | length > 0' \
    "$SETTINGS" >/dev/null 2>&1
}

current_cmds() {
  jq -r '(.hooks.SessionEnd // []) | map(.hooks // []) | flatten
     | map(select((.command // "") | test("evaluate-session"))) | .[].command' \
    "$SETTINGS" 2>/dev/null
}

write_settings() {
  # settings.json is commonly a symlink into a dotfiles repo, so resolve it and
  # replace the file it points at — a plain mv onto the link would destroy it.
  # Write a temp file first and rename: a truncating write that dies partway
  # leaves the user with no settings at all.
  local content="$1" target tmp
  target="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$SETTINGS")" || return 1
  tmp="$(mktemp "${target}.XXXXXX")" || return 1
  printf '%s\n' "$content" > "$tmp" || { rm -f "$tmp"; return 1; }
  jq -e . "$tmp" >/dev/null 2>&1 || { rm -f "$tmp"; return 1; }
  chmod --reference="$target" "$tmp" 2>/dev/null || chmod 644 "$tmp"
  mv -f "$tmp" "$target"
}

write_launcher() {
  mkdir -p "$LAUNCHER_DIR" || return 1
  # A symlink here means the user keeps the launcher under version control, so
  # it is theirs and not ours to overwrite. The launcher is identical everywhere
  # anyway; only the path file below differs per machine.
  if [ -L "$LAUNCHER" ]; then
    echo "launcher: $LAUNCHER is a symlink — left alone"
  else
    cp "$SKILL_DIR/assets/hook-launcher.sh" "$LAUNCHER" || return 1
    chmod +x "$LAUNCHER"
  fi
  # Record this checkout only when it is not already reachable as an installed
  # plugin, so a normal install writes no machine-specific state at all.
  case "$SKILL_DIR" in
    "$HOME"/.claude/plugins/cache/*) rm -f "$LAUNCHER_DIR/evaluate-session.path" ;;
    *) printf '%s\n' "$SKILL_DIR" > "$LAUNCHER_DIR/evaluate-session.path" ;;
  esac
}

# ~/.claude/projects holds one directory per project, named for its path with
# every character that is not a letter or digit replaced by a dash.
transcript_dir() {
  printf '%s/.claude/projects/%s\n' "$HOME" \
    "$(printf '%s' "$1" | sed 's/[^A-Za-z0-9]/-/g')"
}

case "$ACTION" in
  test)
    installed_cmd || { echo "install-hook: not installed in $SETTINGS" >&2; exit 1; }
    # Read the command out of settings rather than assuming it, so this tests
    # the wiring that actually exists instead of the wiring we intended.
    CMD="$(current_cmds | head -1)"
    CMD="${CMD/#\~/$HOME}"
    [ -x "$CMD" ] || { echo "install-hook: $CMD is not executable — the hook would fail silently" >&2; exit 1; }

    DIR="$(transcript_dir "$PWD")"
    [ -d "$DIR" ] || { echo "install-hook: no transcripts for this project at $DIR" >&2; exit 1; }
    LATEST="$(find "$DIR" -maxdepth 1 -name '*.jsonl' -type f -exec stat -f '%m %N' {} + 2>/dev/null \
              || find "$DIR" -maxdepth 1 -name '*.jsonl' -type f -printf '%T@ %p\n' 2>/dev/null)"
    LATEST="$(printf '%s\n' "$LATEST" | sort -rn | head -1 | cut -d' ' -f2-)"
    [ -n "$LATEST" ] && [ -f "$LATEST" ] || { echo "install-hook: no session transcript found in $DIR" >&2; exit 1; }

    echo "hook:       $CMD"
    echo "transcript: $(basename "$LATEST")"
    BEFORE="$(find "$HOME/.claude/scorecards" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    printf '{"session_id":"test","transcript_path":"%s","cwd":"%s","reason":"prompt_input_exit"}' \
      "$LATEST" "$PWD" | "$CMD"
    rc=$?
    echo "hook returned $rc immediately (it grades detached, so an exit here is not the result)"
    echo -n "waiting for a scorecard"
    for _ in $(seq 1 30); do
      sleep 5
      AFTER="$(find "$HOME/.claude/scorecards" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
      if [ "$AFTER" -gt "$BEFORE" ]; then
        echo
        echo "wrote: $(find "$HOME/.claude/scorecards" -maxdepth 1 -name '*.md' -newermt '-3 minutes' 2>/dev/null | head -1)"
        exit 0
      fi
      echo -n "."
    done
    echo
    echo "no scorecard after 150s. A session under the minimum turn count is" >&2
    echo "skipped on purpose; otherwise run evaluate.sh directly to see the error." >&2
    exit 1
    ;;

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
    [ -x "$SKILL_DIR/scripts/hook.sh" ] || { echo "install-hook: $SKILL_DIR/scripts/hook.sh is missing or not executable" >&2; exit 2; }
    MIGRATING=0
    if installed_cmd; then
      # An entry already naming this skill is either identical, in which case
      # there is nothing to do, or an older one pointing straight at a copy of
      # the skill, which is what the launcher exists to replace.
      if current_cmds | grep -qx "$HOOK_CMD"; then
        # The settings entry is right, but the launcher behind it may be from an
        # older version of the skill. Refreshing it is the point of re-running.
        write_launcher || { echo "install-hook: could not write $LAUNCHER" >&2; exit 2; }
        echo "already installed in $SETTINGS; launcher refreshed"
        exit 0
      fi
      echo "Replacing an older entry that points directly at a copy of the skill:"
      current_cmds | sed 's/^/  /'
      echo
      MIGRATING=1
    fi
    mkdir -p "$(dirname "$SETTINGS")" || exit 2
    [ -f "$SETTINGS" ] || printf '{}\n' > "$SETTINGS"
    jq -e . "$SETTINGS" >/dev/null 2>&1 || {
      echo "install-hook: $SETTINGS is not valid JSON; refusing to edit it" >&2; exit 2; }

    # Merged into whatever SessionEnd hooks already exist rather than replacing
    # them — other hooks in this file are not ours to remove.
    NEW="$(jq --arg c "$HOOK_CMD" \
      '.hooks //= {} | .hooks.SessionEnd //= []
       | .hooks.SessionEnd = ((.hooks.SessionEnd)
           | map(.hooks = ((.hooks // []) | map(select((.command // "") | test("evaluate-session") | not))))
           | map(select((.hooks | length) > 0)))
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

    write_launcher || { echo "install-hook: could not write $LAUNCHER" >&2; exit 2; }
    write_settings "$NEW" || { echo "install-hook: could not write $SETTINGS" >&2; exit 2; }
    echo "launcher: $LAUNCHER"
    if [ "$MIGRATING" -eq 1 ]; then
      echo "installed, replacing the older direct path"
    else
      echo "installed"
    fi
    ;;

  uninstall)
    if ! installed_cmd; then
      echo "not installed in $SETTINGS"
      exit 1
    fi
    # Drop only entries naming this command, then drop groups left empty.
    NEW="$(jq '.hooks.SessionEnd = ((.hooks.SessionEnd // [])
         | map(.hooks = ((.hooks // []) | map(select((.command // "") | test("evaluate-session") | not))))
         | map(select((.hooks | length) > 0)))
       | if (.hooks.SessionEnd | length) == 0 then del(.hooks.SessionEnd) else . end' "$SETTINGS")" || exit 2
    write_settings "$NEW" || { echo "install-hook: could not write $SETTINGS" >&2; exit 2; }
    [ -L "$LAUNCHER" ] || rm -f "$LAUNCHER"
    rm -f "$LAUNCHER_DIR/evaluate-session.path"
    echo "removed from $SETTINGS"
    ;;
esac
