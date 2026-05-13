#!/bin/bash
set -e

# Bind an agent to a Discord channel
# Updated for OpenClaw 2026.3.x
#
# Note: `openclaw agents bind` works at channel level (discord, telegram),
# not per-Discord-channel-ID. For channel-specific routing we still need
# config patching for the bindings array.
#
# Usage: ./bind-channel.sh --agent <id> --channel <id> [--topic "..."]

GUILD_ID="${DISCORD_GUILD_ID:-}"
QUIET=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --agent) AGENT_ID="$2"; shift 2 ;;
    --channel) CHANNEL_ID="$2"; shift 2 ;;
    --create) CREATE_CHANNEL="$2"; shift 2 ;;
    --category) CATEGORY_ID="$2"; shift 2 ;;
    --topic) TOPIC="$2"; shift 2 ;;
    --quiet|-q) QUIET=true; shift ;;
    --guild-id) GUILD_ID="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$AGENT_ID" ]] || [[ -z "$CHANNEL_ID" && -z "$CREATE_CHANNEL" ]]; then
  echo "Usage: $0 --agent <agent-id> --channel <channel-id>"
  echo "   or: $0 --agent <agent-id> --create <channel-name> [--category <id>]"
  exit 1
fi

# Create channel if needed
if [[ -n "$CREATE_CHANNEL" ]]; then
  if [[ -z "$GUILD_ID" ]]; then
    echo "✗ DISCORD_GUILD_ID not set. Use --guild-id or set the environment variable."
    exit 1
  fi
  [[ "$QUIET" != "true" ]] && echo "Creating channel #$CREATE_CHANNEL..."

  CREATE_CMD="openclaw message channel-create --name \"$CREATE_CHANNEL\" --guildId \"$GUILD_ID\""
  [[ -n "$CATEGORY_ID" ]] && CREATE_CMD="$CREATE_CMD --parentId \"$CATEGORY_ID\""
  RESULT=$(eval "$CREATE_CMD --json" 2>/dev/null)
  CHANNEL_ID=$(echo "$RESULT" | jq -r '.channel.id // .id // empty')

  if [[ -z "$CHANNEL_ID" ]]; then
    echo "✗ Failed to create channel"
    exit 1
  fi

  [[ "$QUIET" != "true" ]] && echo "Created: $CHANNEL_ID"

  if [[ -n "$TOPIC" ]]; then
    openclaw message channel-edit --channelId "$CHANNEL_ID" --topic "$TOPIC" >/dev/null 2>&1 || true
  fi
fi

# Channel-specific Discord bindings require config patch
CONFIG=$(openclaw gateway call config.get --json 2>/dev/null)

if ! echo "$CONFIG" | jq -e '.parsed' >/dev/null 2>&1; then
  echo "✗ Failed to get config. Aborting."
  exit 1
fi

CURRENT_BINDINGS=$(echo "$CONFIG" | jq -c '.parsed.bindings // []')

# Build and prepend binding (first match wins)
NEW_BINDING=$(jq -n \
  --arg agentId "$AGENT_ID" \
  --arg channelId "$CHANNEL_ID" \
  '{
    agentId: $agentId,
    match: { channel: "discord", peer: { kind: "channel", id: $channelId } }
  }')

BINDINGS=$(echo "$CURRENT_BINDINGS" | jq --argjson new "$NEW_BINDING" \
  '[($new)] + [.[] | select(.match.peer.id != $new.match.peer.id or .agentId != $new.agentId)]')

# Add to guild allowlist
if [[ -n "$GUILD_ID" ]]; then
  CURRENT_CHANNELS=$(echo "$CONFIG" | jq -c --arg gid "$GUILD_ID" '.parsed.channels.discord.guilds[$gid].channels // {}')
  CHANNELS=$(echo "$CURRENT_CHANNELS" | jq --arg id "$CHANNEL_ID" '. + { ($id): { allow: true } }')

  PATCH=$(jq -n --argjson b "$BINDINGS" --argjson c "$CHANNELS" --arg gid "$GUILD_ID" \
    '{ bindings: $b, channels: { discord: { guilds: { ($gid): { channels: $c } } } } }')
else
  PATCH=$(jq -n --argjson b "$BINDINGS" '{ bindings: $b }')
fi

BASE_HASH=$(openclaw gateway call config.get --json 2>/dev/null | jq -r '.hash // empty')
PATCH_PARAMS=$(jq -n --arg raw "$(echo "$PATCH" | jq -c .)" --arg hash "$BASE_HASH" '{raw: $raw, baseHash: $hash}')
openclaw gateway call config.patch --params "$PATCH_PARAMS" --json --timeout 30000 >/dev/null 2>&1

[[ "$QUIET" != "true" ]] && echo "✓ Bound $AGENT_ID → #$CHANNEL_ID"
