
# This project has no test command for version.sh to discover. Appended to the
# base fixture rather than kept as a second copy of it, so the two cases cannot
# drift apart.
rm -f scripts/test.sh
rmdir scripts 2>/dev/null || true
git add -A
GIT_AUTHOR_DATE='2026-09-18T11:06:00' GIT_COMMITTER_DATE='2026-09-18T11:06:00' \
  git commit -qm 'Drop the test script'
