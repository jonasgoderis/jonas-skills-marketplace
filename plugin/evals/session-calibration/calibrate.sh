#!/usr/bin/env bash
# Check that evaluate-session's bands can still go down.
#
# The rubric resolves ambiguity upward on purpose — an unfairly harsh grade gets
# ignored, which costs more than a generous one. The price of that choice is a
# failure mode nothing else in the repo detects: every session becomes an A, the
# scorecards stay cheerful, and the skill quietly stops measuring anything.
#
# So this grades two synthetic sessions whose ground truth is known, and fails
# when either lands outside the band it was built to earn. It is a calibration,
# not a unit test: it makes real grading calls and costs a few cents a run.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(cd "$HERE/../../skills/evaluate-session" && pwd)"

RUNS=3
MODEL="haiku"
KEEP=0
WORK=""

usage() {
  cat <<'USAGE'
calibrate.sh [options]

  --runs N      gradings per session (default: 3)
  --model NAME  model for the grading call (default: haiku)
  --work DIR    build the fixture here and keep it (default: a temp dir)
  --keep        keep the temp directory and print its path
  --dry-run     build the fixture and digest both sessions, grade nothing
USAGE
}

DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --runs)    RUNS="${2:-}"; shift 2 ;;
    --model)   MODEL="${2:-}"; shift 2 ;;
    --work)    WORK="${2:-}"; KEEP=1; shift 2 ;;
    --keep)    KEEP=1; shift ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "calibrate: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [ -z "$WORK" ]; then
  WORK="$(mktemp -d "${TMPDIR:-/tmp}/session-calibration.XXXXXX")" || exit 2
  [ "$KEEP" -eq 1 ] || trap 'rm -rf "$WORK"' EXIT
fi
mkdir -p "$WORK" || exit 2

PROJECT="$(python3 "$HERE/make-sessions.py" --out "$WORK")" || exit 2

if [ "$DRY" -eq 1 ]; then
  for name in bad ordinary; do
    echo "--- $name"
    python3 "$SKILL/scripts/digest.py" --transcript "$WORK/$name-session.jsonl" \
      --project-dir "$PROJECT" | head -40
  done
  echo "fixture: $WORK"
  exit 0
fi

# Bands the fixture was built to earn. `bad` costs itself five episodes, so
# anything above C means the bands are not discriminating and the fix is a
# threshold rather than more prose. `ordinary` is allowed to sit anywhere at or
# above B: the difference between A+ and A is a judgement call this cannot pin.
expected_bad="C D"
expected_ordinary="A+ A B"

fails=0
printf '%-10s  %-8s  %s\n' session expected grades
printf '%-10s  %-8s  %s\n' --------- -------- ------

for name in bad ordinary; do
  eval "want=\$expected_$name"
  grades=""
  for _ in $(seq 1 "$RUNS"); do
    out="$("$SKILL/scripts/evaluate.sh" \
            --transcript "$WORK/$name-session.jsonl" \
            --project-dir "$PROJECT" \
            --model "$MODEL" \
            --out "$WORK/scorecards-$name" 2>"$WORK/$name.err")"
    if [ -z "$out" ] || [ ! -f "$out" ]; then
      grades="$grades ?"
      echo "calibrate: the grading call for '$name' produced nothing" >&2
      head -3 "$WORK/$name.err" >&2
      fails=$((fails+1))
      continue
    fi
    g="$(grep -m1 -oE '^\*\*Grade: [^*]+\*\*' "$out" | sed 's/\*\*Grade: //; s/\*\*//')"
    grades="$grades ${g:-?}"
    case " $want " in
      *" $g "*) ;;
      *) fails=$((fails+1)); echo "calibrate: '$name' graded $g, wanted one of: $want" >&2 ;;
    esac
  done
  printf '%-10s  %-8s %s\n' "$name" "$(printf "%s" "$want" | tr " " "/")" "$grades"
done

echo
if [ "$fails" -eq 0 ]; then
  echo "Calibration holds: a session that went badly still grades down."
  [ "$KEEP" -eq 1 ] && echo "fixture: $WORK"
  exit 0
fi
echo "$fails grading(s) landed outside the expected band."
[ "$KEEP" -eq 1 ] && echo "fixture: $WORK"
exit 1
