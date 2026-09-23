
# A branch that leaves the docs half done, next to a doc that must not be
# "fixed". The README gains a Usage section for bin/greet in the first commit
# and misses the --shout flag added in the second, so it is touched and still
# stale — a run that treats "touched" as "up to date" misses it. The dated plan
# on main says a command-line interface is out of scope; the branch ships one,
# and the plan is still an accurate record of what was decided at the time.
git checkout -q main
mkdir -p docs/plans
cat > docs/plans/2026-09-10-greeter-plan.md <<'PLAN'
# Greeter plan

Out of scope for now: a parting message, and any command-line interface.
PLAN
commit '2026-09-15T09:00:00' 'Record the greeter plan'
git push -q origin main
git checkout -q add-greeting
git rebase -q main

mkdir -p bin
cat > bin/greet <<'GREET'
#!/bin/sh
name=world
[ "${1:-}" = "--name" ] && name="$2"
echo "hello $name"
GREET
chmod +x bin/greet
cat >> README.md <<'README'

## Usage

    bin/greet [--name NAME]

`--name` sets who is greeted.
README
commit '2026-09-19T10:00:00' 'Add bin/greet'

cat > bin/greet <<'GREET'
#!/bin/sh
name=world; shout=0
while [ $# -gt 0 ]; do
  case "$1" in
    --name)  name="$2"; shift ;;
    --shout) shout=1 ;;
  esac
  shift
done
msg="hello $name"
[ "$shout" -eq 1 ] && msg="$(printf '%s' "$msg" | tr '[:lower:]' '[:upper:]')"
echo "$msg"
GREET
commit '2026-09-19T15:00:00' 'Add a --shout flag to bin/greet'
