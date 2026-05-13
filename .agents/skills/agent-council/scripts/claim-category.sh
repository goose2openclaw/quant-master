#!/bin/bash
set -e

# Agent Council - Claim a Discord category for an agent
# Usage: ./claim-category.sh --agent <id> --category <id> [--sync]
#
# When an agent owns a category, new channels created in that category
# will automatically be bound to the agent.

SKILL_DIR="$(dirname "$0")/.."
DATA_FILE="$SKILL_DIR/data/category-owners.json"
SYNC=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --agent) AGENT_ID="$2"; shift 2 ;;
    --category) CATEGORY_ID="$2"; shift 2 ;;
    --sync) SYNC=true; shift ;;
    --help|-h)
      echo "Usage: $0 --agent <id> --category <id> [--sync]"
      echo ""
      echo "Options:"
      echo "  --agent      Agent ID (required)"
      echo "  --category   Discord category ID (required)"
      echo "  --sync       Immediately sync all channels in category to agent"
      echo ""
      echo "Example:"
      echo "  $0 --agent chief --category 123456789012345678 --sync"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Validate
if [[ -z "$AGENT_ID" ]] || [[ -z "$CATEGORY_ID" ]]; then
  echo "Error: --agent and --category are required"
  echo "Run with --help for usage"
  exit 1
fi

# Ensure data file exists
if [[ ! -f "$DATA_FILE" ]]; then
  echo '{"_comment": "Maps Discord category IDs to agent IDs", "categories": {}}' > "$DATA_FILE"
fi

# Check agent exists
AGENT_EXISTS=$(openclaw gateway call config.get --json | jq -r --arg id "$AGENT_ID" '.parsed.agents.list[] | select(.id == $id) | .id')
if [[ -z "$AGENT_EXISTS" ]]; then
  echo "Error: Agent '$AGENT_ID' not found in config"
  exit 1
fi

# Get agent info for display
AGENT_INFO=$(openclaw gateway call config.get --json | jq -r --arg id "$AGENT_ID" '.parsed.agents.list[] | select(.id == $id) | "\(.identity.emoji // "🤖") \(.identity.name // .name)"')

# Update ownership
jq --arg cat "$CATEGORY_ID" --arg agent "$AGENT_ID" '.categories[$cat] = $agent' "$DATA_FILE" > "${DATA_FILE}.tmp"
mv "${DATA_FILE}.tmp" "$DATA_FILE"

echo "═══════════════════════════════════════════════════════════"
echo "  Category Claimed"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Agent:    $AGENT_INFO ($AGENT_ID)"
echo "  Category: $CATEGORY_ID"
echo ""

# Sync if requested
if [[ "$SYNC" == "true" ]]; then
  echo "  Syncing channels..."
  "$SKILL_DIR/scripts/sync-category.sh" --category "$CATEGORY_ID"
else
  echo "  Run with --sync to bind existing channels, or use:"
  echo "  $SKILL_DIR/scripts/sync-category.sh --category $CATEGORY_ID"
fi
