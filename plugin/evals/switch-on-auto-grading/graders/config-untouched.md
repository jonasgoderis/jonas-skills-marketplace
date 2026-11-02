---
type: regex
target: trace
pattern: '"file_path"\s*:\s*"[^"]*(settings(\.local)?\.json|hooks\.json)"'
match: not_contains
---

The plugin already registers the hook. Switching it on is a marker file; editing
either of these is the path that breaks on the next plugin update.
