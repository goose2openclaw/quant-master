#!/bin/bash
set -e

# Remove an agent
# Updated for OpenClaw 2026.3.x — uses `openclaw agents delete` and `openclaw agents unbind`
#
# Usage: ./remove-agent.sh --id <agent-id> [--delete-workspace] [--delete-channel]

while [[ $# -gt 0 ]]; do
  case $1 in
    --id) ID="$2"; shift 2 ;;
    --delete-workspace) DELETE_WORKSPACE=true; shift ;;
    --delete-channel) DELETE_CHANNEL=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$ID" ]]; then
  echo "Usage: $0 --id <agent-id> [--delete-workspace] [--delete-channel]"
  exit 1
fi

echo "Removing agent: $ID"

# Get channel IDs before removing (for optional channel deletion)
CONFIG=$(openclaw gateway call config.get --json 2>/dev/null)
CHANNEL_IDS=$(echo "$CONFIG" | jq -r --arg id "$ID" \
  '.parsed.bindings[] | select(.agentId == $id and .match.channel == "discord") | .match.peer.id')

# Remove all bindings for this agent
openclaw agents unbind --agent "$ID" --all >/dev/null 2>&1 && \
  echo "✓ Removed all bindings" || \
  echo "⚠ No bindings to remove (or agent not found)"

# Remove cron jobs for this agent
CRON_IDS=$(openclaw cron list --json 2>/dev/null | jq -r --arg id "$ID" '.jobs[] | select(.agentId == $id) | .id')
for cron_id in $CRON_IDS; do
  openclaw cron remove --id "$cron_id" >/dev/null 2>&1
  echo "✓ Removed cron job: $cron_id"
done

# Delete agent from config
openclaw agents delete "$ID" >/dev/null 2>&1 && \
  echo "✓ Removed from agent config" || \
  echo "⚠ Agent not found in config (may already be removed)"

# Delete Discord channels
if [[ "$DELETE_CHANNEL" == "true" ]]; then
  for ch_id in $CHANNEL_IDS; do
    openclaw message channel-delete --channelId "$ch_id" >/dev/null 2>&1 && \
      echo "✓ Deleted Discord channel: $ch_id" || \
      echo "✗ Failed to delete channel $ch_id (may need manual deletion)"
  done
fi

# Delete workspace
WORKSPACE="$HOME/workspace/agents/$ID"
if [[ "$DELETE_WORKSPACE" == "true" ]] && [[ -d "$WORKSPACE" ]]; then
  trash "$WORKSPACE" 2>/dev/null || rm -rf "$WORKSPACE"
  echo "✓ Deleted workspace: $WORKSPACE"
else
  [[ -d "$WORKSPACE" ]] && echo "  Workspace preserved: $WORKSPACE"
fi

# Delete agent state dir
AGENT_STATE="$HOME/.openclaw/agents/$ID"
if [[ "$DELETE_WORKSPACE" == "true" ]] && [[ -d "$AGENT_STATE" ]]; then
  trash "$AGENT_STATE" 2>/dev/null || rm -rf "$AGENT_STATE"
  echo "✓ Deleted agent state: $AGENT_STATE"
fi

# Update qmd index
if command -v qmd &> /dev/null; then
  qmd update >/dev/null 2>&1 && echo "✓ Updated qmd index"
fi

echo ""
echo "Done. Agent $ID removed."
