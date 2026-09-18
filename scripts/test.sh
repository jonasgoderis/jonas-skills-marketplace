#!/usr/bin/env bash
# Validates the marketplace before a release: manifests parse and agree, every
# skill is well-formed, every shell script is syntactically sound.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fails=0
pass() { printf '  ok    %s\n' "$*"; }
fail() { printf '  FAIL  %s\n' "$*"; fails=$((fails+1)); }

echo "Manifests"
for f in .claude-plugin/marketplace.json plugin/.claude-plugin/plugin.json; do
  if [ ! -f "$f" ]; then fail "$f is missing"; continue; fi
  if jq -e . "$f" >/dev/null 2>&1; then pass "$f parses"; else fail "$f is not valid JSON"; fi
done

mv_version="$(jq -r '.plugins[0].version // empty' .claude-plugin/marketplace.json 2>/dev/null)"
pl_version="$(jq -r '.version // empty' plugin/.claude-plugin/plugin.json 2>/dev/null)"
if [ -z "$mv_version" ] || [ -z "$pl_version" ]; then
  fail "a manifest is missing its version"
elif [ "$mv_version" != "$pl_version" ]; then
  fail "versions disagree: marketplace $mv_version vs plugin $pl_version"
else
  pass "versions agree at $mv_version"
fi

mv_name="$(jq -r '.plugins[0].name // empty' .claude-plugin/marketplace.json 2>/dev/null)"
pl_name="$(jq -r '.name // empty' plugin/.claude-plugin/plugin.json 2>/dev/null)"
[ "$mv_name" = "$pl_name" ] && pass "plugin name matches in both manifests" \
                            || fail "plugin name differs: '$mv_name' vs '$pl_name'"

echo "Skills"
shopt -s nullglob
found=0
for dir in plugin/skills/*/; do
  name="$(basename "$dir")"
  found=$((found+1))
  skill="$dir/SKILL.md"
  if [ ! -f "$skill" ]; then fail "$name has no SKILL.md"; continue; fi

  if [ "$(head -n1 "$skill")" != "---" ]; then
    fail "$name: SKILL.md does not open with YAML frontmatter"
    continue
  fi
  fm="$(awk 'NR>1 { if ($0 == "---") exit; print }' "$skill")"
  fm_name="$(printf '%s\n' "$fm" | sed -n 's/^name:[[:space:]]*//p' | head -n1)"
  fm_desc="$(printf '%s\n' "$fm" | sed -n 's/^description:[[:space:]]*//p' | head -n1)"

  [ -n "$fm_desc" ] && pass "$name: has a description" \
                    || fail "$name: frontmatter has no description"
  [ "$fm_name" = "$name" ] && pass "$name: frontmatter name matches its directory" \
                           || fail "$name: frontmatter name '$fm_name' != directory '$name'"

  body_lines="$(awk 'f>1; /^---$/ { f++ }' "$skill" | grep -cv '^[[:space:]]*$')"
  [ "$body_lines" -ge 5 ] && pass "$name: has a body" \
                          || fail "$name: SKILL.md body is effectively empty"
done
[ "$found" -gt 0 ] && pass "$found skill(s) found" || fail "no skills found under plugin/skills/"

echo "Scripts"
scripts=0
while IFS= read -r sh; do
  scripts=$((scripts+1))
  bash -n "$sh" 2>/dev/null && pass "$sh parses" || fail "$sh has a syntax error"
  [ -x "$sh" ] && pass "$sh is executable" || fail "$sh is not executable"
done < <(find plugin/skills scripts -name '*.sh' -type f 2>/dev/null | sort)
[ "$scripts" -gt 0 ] || pass "no shell scripts to check"

echo
if [ "$fails" -eq 0 ]; then
  echo "All checks passed."
  exit 0
fi
echo "$fails check(s) failed."
exit 1
