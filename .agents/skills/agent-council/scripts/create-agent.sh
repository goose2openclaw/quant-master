#!/bin/bash
set -e

# Agent Council - Create agent with full Discord integration
# Updated for OpenClaw 2026.3.x CLI (agents add/bind/set-identity)
#
# Usage: ./create-agent.sh [options]
#
# Options:
#   --id           Agent ID (required)
#   --name         Display name (required)
#   --emoji        Agent emoji (required)
#   --specialty    What the agent does (required)
#   --model        Model to use (default: anthropic/claude-sonnet-4-6)
#   --channel      Existing Discord channel ID to bind
#   --create       Create new Discord channel with this name
#   --category     Discord category ID for new channel
#   --topic        Channel topic (auto-generated if not specified)
#   --cron         Set up daily memory cron at this time (e.g., "23:00")
#   --no-cron      Skip daily memory cron setup
#   --tz           Timezone for cron (default: America/New_York)

# Defaults
MODEL="anthropic/claude-sonnet-4-6"
TZ="America/New_York"
GUILD_ID="${DISCORD_GUILD_ID:-}"
CRON_TIME="23:00"
SKIP_CRON=false
SKILL_DIR="$(dirname "$0")/.."
WORKSPACE_ROOT="${AGENT_WORKSPACE_ROOT:-$HOME/workspace/agents}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --id) ID="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --emoji) EMOJI="$2"; shift 2 ;;
    --specialty) SPECIALTY="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --channel) CHANNEL_ID="$2"; shift 2 ;;
    --create) CREATE_CHANNEL="$2"; shift 2 ;;
    --category) CATEGORY_ID="$2"; shift 2 ;;
    --topic) TOPIC="$2"; shift 2 ;;
    --cron) CRON_TIME="$2"; shift 2 ;;
    --no-cron) SKIP_CRON=true; shift ;;
    --tz) TZ="$2"; shift 2 ;;
    --own-category) OWN_CATEGORY="$2"; shift 2 ;;
    --guild-id) GUILD_ID="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Validate required args
if [[ -z "$ID" ]] || [[ -z "$NAME" ]] || [[ -z "$EMOJI" ]] || [[ -z "$SPECIALTY" ]]; then
  echo "Usage: $0 --id <id> --name <name> --emoji <emoji> --specialty <description>"
  echo ""
  echo "Required:"
  echo "  --id           Agent ID (lowercase, no spaces)"
  echo "  --name         Display name"
  echo "  --emoji        Agent emoji"
  echo "  --specialty    What the agent does"
  echo ""
  echo "Discord (pick one):"
  echo "  --channel      Bind to existing channel ID"
  echo "  --create       Create new channel with this name"
  echo "  --category     Category ID for new channel (optional)"
  echo "  --topic        Channel topic (auto-generated if not set)"
  echo ""
  echo "Optional:"
  echo "  --model        Model (default: claude-sonnet-4-6)"
  echo "  --cron         Daily memory cron time (default: 23:00)"
  echo "  --no-cron      Skip daily memory cron setup"
  echo "  --tz           Timezone (default: America/New_York)"
  echo "  --own-category Claim a category (auto-bind all channels in it)"
  echo "  --guild-id     Discord server ID (or set DISCORD_GUILD_ID env var)"
  echo ""
  echo "Environment:"
  echo "  DISCORD_GUILD_ID      Discord server ID (required for --create)"
  echo "  AGENT_WORKSPACE_ROOT  Agent workspace root (default: ~/workspace/agents)"
  echo ""
  echo "Examples:"
  echo "  $0 --id watson --name Watson --emoji 🔬 --specialty 'Deep research' --create research"
  echo "  $0 --id sage --name Sage --emoji 💰 --specialty 'Finance' --channel 1234567890"
  exit 1
fi

WORKSPACE="$WORKSPACE_ROOT/$ID"

echo "═══════════════════════════════════════════════════════════"
echo "  Agent Council - Creating $NAME $EMOJI"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────
# 1. Create workspace
# ─────────────────────────────────────────────────────────────
echo "📁 Creating workspace..."
mkdir -p "$WORKSPACE/memory"

cat > "$WORKSPACE/SOUL.md" << EOF
# SOUL.md - $NAME $EMOJI

## Identity
- **Name:** $NAME
- **Emoji:** $EMOJI
- **Role:** $SPECIALTY

## Personality
Be helpful, concise, and proactive. You're a specialist — own your domain.

## Guidelines
- Read your memory at session start (\`memory/YYYY-MM-DD.md\` — today + yesterday)
- Write to memory as you work (see below)
- Stay in your lane unless asked to cross domains
- When nothing needs attention, reply \`HEARTBEAT_OK\`

## Memory - Write As You Go!

**Don't wait for end-of-day.** Write to \`memory/YYYY-MM-DD.md\` DURING the session when:
- A significant decision is made
- You learn something new or important
- A task is completed (especially complex ones)
- Context that future-you would need
- You receive information worth remembering

**Pattern:**
\`\`\`markdown
## [HH:MM] Topic
Brief note about what happened, what was decided, or what was learned.
\`\`\`

---
*Customize this as your role evolves.*
EOF

cat > "$WORKSPACE/HEARTBEAT.md" << EOF
# HEARTBEAT.md - $NAME $EMOJI

Handle scheduled cron jobs and system events only.

If there are system events (cron jobs), handle them.
Otherwise, reply \`HEARTBEAT_OK\`.
EOF

cat > "$WORKSPACE/AGENTS.md" << 'AGENTSEOF'
# AGENTS.md - Your Workspace

This folder is home. Treat it that way.

## Every Session

Before doing anything else:
1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION:** Also read `MEMORY.md`

## Memory

Write to `memory/YYYY-MM-DD.md` AS YOU WORK — don't wait for end of day.
- One file per date, always. No suffixes.
- `MEMORY.md` = long-term curated memory (main session only)

## Safety

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking. `trash` > `rm`.
- **Ask first:** Emails, tweets, public posts, anything that leaves the machine.
AGENTSEOF

# Create IDENTITY.md for set-identity
cat > "$WORKSPACE/IDENTITY.md" << EOF
# IDENTITY.md

- **Name:** $NAME
- **Emoji:** $EMOJI
- **Role:** $SPECIALTY
EOF

echo "   ✓ Created SOUL.md, HEARTBEAT.md, AGENTS.md, IDENTITY.md, memory/"

# ─────────────────────────────────────────────────────────────
# 2. Discord channel (create or use existing)
# ─────────────────────────────────────────────────────────────
if [[ -n "$CREATE_CHANNEL" ]]; then
  if [[ -z "$GUILD_ID" ]]; then
    echo "   ✗ DISCORD_GUILD_ID not set. Use --guild-id or set the environment variable."
    exit 1
  fi
  echo ""
  echo "📺 Creating Discord channel #$CREATE_CHANNEL..."

  TOPIC="${TOPIC:-$NAME $EMOJI — $SPECIALTY}"

  # Use openclaw message tool to create channel
  CREATE_CMD="openclaw message channel-create --name \"$CREATE_CHANNEL\" --guildId \"$GUILD_ID\""
  [[ -n "$CATEGORY_ID" ]] && CREATE_CMD="$CREATE_CMD --parentId \"$CATEGORY_ID\""
  RESULT=$(eval "$CREATE_CMD --json" 2>/dev/null)

  CHANNEL_ID=$(echo "$RESULT" | jq -r '.channel.id // .id // empty')

  if [[ -z "$CHANNEL_ID" ]]; then
    echo "   ✗ Failed to create channel"
    echo "$RESULT" | jq . 2>/dev/null || echo "$RESULT"
    exit 1
  fi

  # Set topic
  openclaw message channel-edit --channelId "$CHANNEL_ID" --topic "$TOPIC" >/dev/null 2>&1 || true

  echo "   ✓ Created channel: $CHANNEL_ID"
fi

# ─────────────────────────────────────────────────────────────
# 3. Register agent via CLI
# ─────────────────────────────────────────────────────────────
echo ""
echo "⚙️  Registering agent..."

# Use `openclaw agents add` to register the agent
ADD_CMD="openclaw agents add $ID --workspace \"$WORKSPACE\" --model \"$MODEL\" --non-interactive --json"
ADD_RESULT=$(eval "$ADD_CMD" 2>/dev/null) || true

if echo "$ADD_RESULT" | jq -e '.ok // .id' >/dev/null 2>&1; then
  echo "   ✓ Agent registered via CLI"
else
  # May already exist — that's fine, we'll update identity below
  echo "   ⚠ Agent may already exist (will update identity)"
fi

# Set identity (name + emoji)
openclaw agents set-identity --agent "$ID" --name "$NAME" --emoji "$EMOJI" >/dev/null 2>&1 || true
echo "   ✓ Identity set: $NAME $EMOJI"

# ─────────────────────────────────────────────────────────────
# 3b. Copy auth profiles from default agent (with SecretRefs)
# ─────────────────────────────────────────────────────────────
OPENCLAW_DIR="$HOME/.openclaw"
AGENT_AUTH_DIR="$OPENCLAW_DIR/agents/$ID/agent"
mkdir -p "$AGENT_AUTH_DIR"

DEFAULT_AGENT_ID=$(cat "$OPENCLAW_DIR/openclaw.json" 2>/dev/null | jq -r '.agents.list[] | select(.default == true) | .id' | head -1)
DEFAULT_AUTH="$OPENCLAW_DIR/agents/${DEFAULT_AGENT_ID:-main}/agent/auth-profiles.json"

if [[ -f "$DEFAULT_AUTH" ]] && [[ ! -f "$AGENT_AUTH_DIR/auth-profiles.json" ]]; then
  cp "$DEFAULT_AUTH" "$AGENT_AUTH_DIR/auth-profiles.json"
  echo "   ✓ Auth profiles copied from $DEFAULT_AGENT_ID (SecretRef-backed)"
elif [[ -f "$AGENT_AUTH_DIR/auth-profiles.json" ]]; then
  echo "   ✓ Auth profiles already exist"
else
  echo "   ⚠ No auth-profiles.json found to copy — agent may fail to authenticate"
fi

# ─────────────────────────────────────────────────────────────
# 4. Bind to Discord channel (config patch for channel-specific routing)
# ─────────────────────────────────────────────────────────────
if [[ -n "$CHANNEL_ID" ]]; then
  echo ""
  echo "🔗 Binding agent to Discord channel..."

  # Channel-specific Discord bindings require config patch
  # (openclaw agents bind only supports channel-level routing, not per-channel-ID)
  CONFIG=$(openclaw gateway call config.get --json 2>/dev/null)

  if ! echo "$CONFIG" | jq -e '.parsed' >/dev/null 2>&1; then
    echo "   ✗ Failed to get current config. Aborting binding."
    exit 1
  fi

  CURRENT_BINDINGS=$(echo "$CONFIG" | jq -c '.parsed.bindings // []')

  # Build new binding
  NEW_BINDING=$(jq -n \
    --arg agentId "$ID" \
    --arg channelId "$CHANNEL_ID" \
    '{
      agentId: $agentId,
      match: { channel: "discord", peer: { kind: "channel", id: $channelId } }
    }')

  # Prepend binding (first match wins), dedupe by channel ID
  BINDINGS=$(echo "$CURRENT_BINDINGS" | jq --argjson new "$NEW_BINDING" \
    '[($new)] + [.[] | select(.match.peer.id != $new.match.peer.id or .agentId != $new.agentId)]')

  # Add channel to guild allowlist
  CURRENT_CHANNELS=$(echo "$CONFIG" | jq -c --arg gid "$GUILD_ID" '.parsed.channels.discord.guilds[$gid].channels // {}')
  CHANNELS=$(echo "$CURRENT_CHANNELS" | jq --arg id "$CHANNEL_ID" '. + { ($id): { allow: true } }')

  PATCH=$(jq -n --argjson b "$BINDINGS" --argjson c "$CHANNELS" --arg gid "$GUILD_ID" \
    '{ bindings: $b, channels: { discord: { guilds: { ($gid): { channels: $c } } } } }')

  BASE_HASH=$(openclaw gateway call config.get --json 2>/dev/null | jq -r '.hash // empty')
  PATCH_PARAMS=$(jq -n --arg raw "$(echo "$PATCH" | jq -c .)" --arg hash "$BASE_HASH" '{raw: $raw, baseHash: $hash}')
  openclaw gateway call config.patch --params "$PATCH_PARAMS" --json --timeout 30000 >/dev/null 2>&1

  echo "   ✓ Bound $ID → #$CHANNEL_ID"
  echo "   ✓ Added to guild allowlist"
fi

# ─────────────────────────────────────────────────────────────
# 5. Daily memory cron (default: enabled)
# ─────────────────────────────────────────────────────────────
if [[ "$SKIP_CRON" != "true" ]]; then
  echo ""
  echo "⏰ Setting up daily memory cron at $CRON_TIME $TZ..."

  HOUR=$(echo "$CRON_TIME" | cut -d: -f1)
  MINUTE=$(echo "$CRON_TIME" | cut -d: -f2)

  # Remove existing memory cron for this agent
  EXISTING=$(openclaw cron list --json 2>/dev/null | jq -r --arg agent "$ID" \
    '.jobs[] | select(.agentId == $agent and (.name | test("memory|Memory"))) | .id' | head -1)
  [[ -n "$EXISTING" ]] && openclaw cron remove --id "$EXISTING" >/dev/null 2>&1

  DELIVER_CHANNEL_ID="${CHANNEL_ID:-}"

  CRON_CMD=(openclaw cron add \
    --name "$NAME Daily Memory Update" \
    --cron "$MINUTE $HOUR * * *" \
    --tz "$TZ" \
    --agent "$ID" \
    --model sonnet \
    --session isolated \
    --message "End of day memory update: Review today's conversations and activity. Create/update memory/\$(date +%Y-%m-%d).md with a summary of: what was worked on, decisions made, progress, and context for tomorrow. If nothing new, reply HEARTBEAT_OK.")

  if [[ -n "$DELIVER_CHANNEL_ID" ]]; then
    CRON_CMD+=(--announce --channel discord --to "channel:$DELIVER_CHANNEL_ID")
  fi

  "${CRON_CMD[@]}" >/dev/null 2>&1

  if [[ $? -eq 0 ]]; then
    echo "   ✓ Cron job created"
  else
    echo "   ✗ Cron job creation failed (create manually)"
  fi
fi

# ─────────────────────────────────────────────────────────────
# 6. Category ownership (optional)
# ─────────────────────────────────────────────────────────────
if [[ -n "$OWN_CATEGORY" ]]; then
  echo ""
  echo "📂 Claiming category ownership..."
  "$SKILL_DIR/scripts/claim-category.sh" --agent "$ID" --category "$OWN_CATEGORY" --sync
fi

# ─────────────────────────────────────────────────────────────
# 7. Update qmd index
# ─────────────────────────────────────────────────────────────
if command -v qmd &> /dev/null; then
  echo ""
  echo "🔍 Updating qmd index..."
  qmd update >/dev/null 2>&1 && echo "   ✓ Agent memory now searchable via qmd"
fi

# ─────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✓ Agent $NAME $EMOJI created successfully!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Workspace:  $WORKSPACE"
echo "  Model:      $MODEL"
[[ -n "$CHANNEL_ID" ]] && echo "  Discord:    #$CHANNEL_ID"
[[ "$SKIP_CRON" != "true" ]] && echo "  Cron:       Daily at $CRON_TIME $TZ"
echo ""
echo "  Next steps:"
echo "    1. Customize $WORKSPACE/SOUL.md"
echo "    2. Test: send a message in the bound channel"
echo ""
