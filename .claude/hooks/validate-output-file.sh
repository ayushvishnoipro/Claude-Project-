#!/bin/bash
# PostToolUse / Write: warn if a file written to docs/ or output/ is empty. Never blocks.
INPUT=$(cat 2>/dev/null)
[ -z "$INPUT" ] && INPUT="$CLAUDE_TOOL_INPUT"

FILE_PATH=$(printf '%s' "$INPUT" | python -c "import sys,json; d=json.load(sys.stdin); d=d.get('tool_input',d); print(d.get('file_path',''))" 2>/dev/null || echo "")

# Normalize: backslashes -> slashes, strip project dir prefix so globs match
FILE_PATH="${FILE_PATH//\\//}"
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
ROOT="${ROOT//\\//}"
FILE_PATH="${FILE_PATH#"$ROOT"/}"

# Only validate files in docs/ or output/
if [[ "$FILE_PATH" == docs/* ]] || [[ "$FILE_PATH" == output/* ]]; then
  if [ ! -s "$FILE_PATH" ]; then
    echo "WARNING: $FILE_PATH was written but is empty. The agent may have failed to produce output." >&2
  else
    LINES=$(wc -l < "$FILE_PATH")
    echo "OK: $FILE_PATH written ($LINES lines)" >&2
  fi
fi
exit 0
