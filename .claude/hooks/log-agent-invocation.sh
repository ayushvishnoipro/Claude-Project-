#!/bin/bash
# PreToolUse / Agent: append a timestamped entry to docs/changelog.md. Never blocks.
INPUT=$(cat 2>/dev/null)
[ -z "$INPUT" ] && INPUT="$CLAUDE_TOOL_INPUT"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
AGENT_NAME=$(printf '%s' "$INPUT" | python -c "import sys,json; d=json.load(sys.stdin); d=d.get('tool_input',d); print(d.get('description') or d.get('subagent_type') or 'unknown')" 2>/dev/null || echo "unknown")
[ -z "$AGENT_NAME" ] && AGENT_NAME="unknown"

echo "" >> docs/changelog.md
echo "### $TIMESTAMP — Spawning agent: $AGENT_NAME" >> docs/changelog.md
exit 0
