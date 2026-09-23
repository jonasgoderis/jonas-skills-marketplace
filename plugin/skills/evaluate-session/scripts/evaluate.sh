#!/usr/bin/env bash
# Grade one Claude Code session against the practice catalogue.
#
# Digest the transcript, send the digest to a model with the rubric, write the
# scorecard to disk and append a line to the index. Nothing here is interactive:
# it is built to be run detached from a SessionEnd hook, and also works on the
# command line for a session that has already ended.
set -uo pipefail

# The grading run is itself a Claude session, which ends, which fires SessionEnd
# again. Without this guard the first exit forks until something gives out.
if [ -n "${CLAUDE_EVALUATE_SESSION:-}" ]; then
  exit 0
fi
export CLAUDE_EVALUATE_SESSION=1

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${HOME}/.claude/scorecards"
MODEL="haiku"
TRANSCRIPT=""
PROJECT_DIR="$PWD"
MIN_TURNS=5
DRY_RUN=0
REASON=""

usage() {
  cat <<'USAGE'
evaluate.sh --transcript <path> [options]

  --transcript PATH   session .jsonl to grade (required)
  --project-dir DIR   project the session ran in (default: cwd)
  --model NAME        model for the grading call (default: haiku)
  --out DIR           where scorecards land (default: ~/.claude/scorecards)
  --min-turns N       skip sessions shorter than this (default: 5)
  --reason R          SessionEnd reason, recorded in the index
  --dry-run           print the digest and the prompt, call nothing, spend nothing
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --transcript)  TRANSCRIPT="${2:-}"; shift 2 ;;
    --project-dir) PROJECT_DIR="${2:-}"; shift 2 ;;
    --model)       MODEL="${2:-}"; shift 2 ;;
    --out)         OUT_DIR="${2:-}"; shift 2 ;;
    --min-turns)   MIN_TURNS="${2:-}"; shift 2 ;;
    --reason)      REASON="${2:-}"; shift 2 ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    *) echo "evaluate: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$TRANSCRIPT" ] || { echo "evaluate: --transcript is required" >&2; exit 2; }
[ -f "$TRANSCRIPT" ] || { echo "evaluate: no such transcript: $TRANSCRIPT" >&2; exit 2; }

command -v claude >/dev/null 2>&1 || { echo "evaluate: claude is not on PATH" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "evaluate: python3 is not on PATH" >&2; exit 2; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/evaluate-session.XXXXXX")" || exit 2
trap 'rm -rf "$TMP"' EXIT

# Digest first. A short session, or one whose messages match a secret pattern,
# stops here — before anything is sent anywhere.
DIGEST="$TMP/digest.json"
python3 "$SKILL_DIR/scripts/digest.py" \
  --transcript "$TRANSCRIPT" \
  --project-dir "$PROJECT_DIR" \
  --min-turns "$MIN_TURNS" \
  > "$DIGEST" 2> "$TMP/digest.err"
rc=$?
if [ "$rc" -eq 3 ]; then
  exit 0                                   # too short to say anything useful
elif [ "$rc" -eq 4 ]; then
  cat "$TMP/digest.err" >&2                # secret matched; nothing was written
  exit 4
elif [ "$rc" -ne 0 ]; then
  cat "$TMP/digest.err" >&2
  exit "$rc"
fi

PROMPT="$TMP/prompt.md"
{
  cat "$SKILL_DIR/assets/grader-prompt.md"
  printf '\n\n---\n\n# Practice catalogue\n\n'
  cat "$SKILL_DIR/references/best-practices.md"
  printf '\n\n---\n\n# Rubric\n\n'
  cat "$SKILL_DIR/references/rubric.md"
  printf '\n\n---\n\n# Session digest\n\n```json\n'
  cat "$DIGEST"
  printf '\n```\n'
} > "$PROMPT"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "--- digest ($(wc -c < "$DIGEST" | tr -d ' ') bytes) ---"
  cat "$DIGEST"
  echo "--- prompt ($(wc -c < "$PROMPT" | tr -d ' ') bytes, ~$(( $(wc -c < "$PROMPT") / 4 )) tokens) ---"
  echo "would call: claude -p --model $MODEL --restricted"
  exit 0
fi

# --restricted removes the tools that run commands: the grader reads and answers,
# it does not act. The transcript it is reading is untrusted text.
REPORT="$TMP/report.md"
if ! claude -p --model "$MODEL" --restricted --permission-mode dontAsk \
     < "$PROMPT" > "$REPORT" 2> "$TMP/claude.err"; then
  echo "evaluate: the grading call failed" >&2
  head -5 "$TMP/claude.err" >&2
  exit 1
fi
[ -s "$REPORT" ] || { echo "evaluate: the grading call returned nothing" >&2; exit 1; }

# Strip an enclosing code fence if the model added one anyway.
if [ "$(head -n1 "$REPORT")" = '```' ] || [ "$(head -n1 "$REPORT")" = '```markdown' ]; then
  sed '1d; ${/^```$/d;}' "$REPORT" > "$REPORT.clean" && mv "$REPORT.clean" "$REPORT"
fi

mkdir -p "$OUT_DIR" || exit 2
PROJECT="$(basename "$PROJECT_DIR" | tr ' ' '-')"
STAMP="$(date +%Y-%m-%d-%H%M)"
DEST="$OUT_DIR/${STAMP}-${PROJECT}.md"
cp "$REPORT" "$DEST"

# One scorecard is a mood; the index is whether the practice is improving.
GRADE="$(grep -m1 -oE '^\*\*Grade: [^*]+\*\*' "$REPORT" | sed 's/\*\*Grade: //; s/\*\*//' | tr -d '\n')"
FOCUS="$(awk '/^## Focus on/{f=1;next} /^## /{f=0} f' "$REPORT" \
         | grep -oE 'BP-[0-9]{2}' | head -2 | paste -sd, - | tr -d '\n')"
INDEX="$OUT_DIR/index.md"
[ -f "$INDEX" ] || printf '# Scorecards\n\n| Date | Project | Grade | Focus | Report |\n| --- | --- | --- | --- | --- |\n' > "$INDEX"
printf '| %s | %s | %s | %s | [%s](%s) |\n' \
  "$(date +%Y-%m-%d)" "$PROJECT" "${GRADE:-?}" "${FOCUS:-—}" "$(basename "$DEST")" "$(basename "$DEST")" \
  >> "$INDEX"

echo "$DEST"
