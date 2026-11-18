---
type: regex
target:
  source: file
  path: docs/azure.drawio
pattern: '<mxCell\b(?=[^>]*container=1)(?=[^>]*\bid="([^"]+)")[^>]*>[\s\S]*<mxCell\b(?=[^>]*\bstyle="(?:[^"]*;)?text;)(?=[^>]*\bvalue="[^"])(?=[^>]*\bparent="\1")'
match: contains
---
