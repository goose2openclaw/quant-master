#!/bin/bash
set -e

# Agent Council - List category ownership
# Usage: ./list-categories.sh

SKILL_DIR="$(dirname "$0")/.."
DATA_FILE="$SKILL_DIR/data/category-owners.json"

echo "═══════════════════════════════════════════════════════════"
echo "  Category Ownership"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [[ ! -f "$DATA_FILE" ]]; then
  echo "  No categories claimed yet."
  echo ""
  echo "  Use: ./claim-category.sh --agent <id> --category <id>"
  exit 0
fi

CATEGORIES=$(jq -r '.categories | to_entries[] | "\(.key) \(.value)"' "$DATA_FILE" 2>/dev/null)

if [[ -z "$CATEGORIES" ]]; then
  echo "  No categories claimed yet."
  echo ""
  echo "  Use: ./claim-category.sh --agent <id> --category <id>"
  exit 0
fi

# Get agent config for display names
CONFIG=$(openclaw gateway call config.get --json)

echo "$CATEGORIES" | while read -r cat_id agent_id; do
  AGENT_INFO=$(echo "$CONFIG" | jq -r --arg id "$agent_id" '.parsed.agents.list[] | select(.id == $id) | "\(.identity.emoji // "🤖") \(.identity.name // .name)"')
  echo "  $cat_id → $AGENT_INFO ($agent_id)"
done

echo ""
