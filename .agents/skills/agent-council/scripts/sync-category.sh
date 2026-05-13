#!/bin/bash
set -e

# Agent Council - Sync all channels in a category to the owning agent
# Usage: ./sync-category.sh --category <id>
#
# Discovers all channels in the category and binds them to the owner agent.
# 
# Note: This script reads from a cached channel list. Run with --refresh to update.

SKILL_DIR="$(dirname "$0")/.."
DATA_FILE="$SKILL_DIR/data/category-owners.json"
CACHE_FILE="$SKILL_DIR/data/channels-cache.json"
GUILD_ID="${DISCORD_GUILD_ID:-}"
DRY_RUN=false
REFRESH=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --category) CATEGORY_ID="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --refresh) REFRESH=true; shift ;;
    --help|-h)
      echo "Usage: $0 --category <id> [--dry-run] [--refresh]"
      echo ""
      echo "Options:"
      echo "  --category   Discord category ID (required)"
      echo "  --dry-run    Show what would be done without making changes"
      echo "  --refresh    Refresh channel cache before syncing"
      echo ""
      echo "Environment:"
      echo "  DISCORD_GUILD_ID   Discord server ID (for cache refresh)"
      echo ""
      echo "Example:"
      echo "  $0 --category 123456789012345678"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Validate
if [[ -z "$CATEGORY_ID" ]]; then
  echo "Error: --category is required"
  exit 1
fi

# Get owner from data file
if [[ ! -f "$DATA_FILE" ]]; then
  echo "Error: No category owners configured. Run claim-category.sh first."
  exit 1
fi

OWNER=$(jq -r --arg cat "$CATEGORY_ID" '.categories[$cat] // empty' "$DATA_FILE")
if [[ -z "$OWNER" ]]; then
  echo "Error: Category $CATEGORY_ID has no owner. Run claim-category.sh first."
  exit 1
fi

# Get agent info
CONFIG=$(openclaw gateway call config.get --json)
AGENT_INFO=$(echo "$CONFIG" | jq -r --arg id "$OWNER" '.parsed.agents.list[] | select(.id == $id) | "\(.identity.emoji // "🤖") \(.identity.name // .name)"')

echo "═══════════════════════════════════════════════════════════"
echo "  Syncing Category to $AGENT_INFO"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Channel list - we need to use a pre-cached list or ask user to provide
# Since we can't call the message tool from bash, we use a cache file
if [[ ! -f "$CACHE_FILE" ]] || [[ "$REFRESH" == "true" ]]; then
  echo "  ⚠ Channel cache not found or refresh requested."
  echo ""
  echo "  To update the cache, run this in an OpenClaw session:"
  echo "    message channel-list --guildId $GUILD_ID --limit 100"
  echo ""
  echo "  Then save the result to: $CACHE_FILE"
  echo ""
  echo "  Or provide channels manually with bind-channel.sh"
  exit 1
fi

# Filter to channels in this category
CHANNELS=$(jq -c --arg parent "$CATEGORY_ID" '[.channels[] | select(.parent_id == $parent and .type != 4)]' "$CACHE_FILE")
CHANNEL_COUNT=$(echo "$CHANNELS" | jq 'length')

if [[ "$CHANNEL_COUNT" -eq 0 ]]; then
  echo "  No channels found in category $CATEGORY_ID"
  exit 0
fi

echo "  Found $CHANNEL_COUNT channels:"
echo ""

# Get current bindings
CURRENT_BINDINGS=$(echo "$CONFIG" | jq -c '.parsed.bindings // []')

# Process each channel
BOUND_COUNT=0
echo "$CHANNELS" | jq -c '.[]' | while read -r channel; do
  CH_ID=$(echo "$channel" | jq -r '.id')
  CH_NAME=$(echo "$channel" | jq -r '.name')
  
  # Check if already bound to this agent
  EXISTING=$(echo "$CURRENT_BINDINGS" | jq -r --arg id "$CH_ID" '.[] | select(.match.peer.id == $id) | .agentId')
  
  if [[ "$EXISTING" == "$OWNER" ]]; then
    echo "  ✓ #$CH_NAME ($CH_ID) — already bound"
  elif [[ -n "$EXISTING" ]]; then
    echo "  ⚠ #$CH_NAME ($CH_ID) — bound to $EXISTING (skipping)"
  else
    echo "  → #$CH_NAME ($CH_ID) — binding to $OWNER"
    
    if [[ "$DRY_RUN" != "true" ]]; then
      "$SKILL_DIR/scripts/bind-channel.sh" --agent "$OWNER" --channel "$CH_ID" --quiet
    fi
    
    BOUND_COUNT=$((BOUND_COUNT + 1))
  fi
done

echo ""
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  Dry run complete. No changes made."
else
  echo "  ✓ Sync complete"
fi
