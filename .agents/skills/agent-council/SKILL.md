---
name: agent-council
description: Create autonomous AI agents with Discord bindings. Use when setting up new agents, managing agent cron jobs, or scheduling agent tasks. Covers agent creation, channel binding, cron job patterns, and delivery routing.
---

# Agent Council

Create and manage autonomous AI agents with full Discord integration.

Updated for **OpenClaw 2026.3.x** — uses native CLI commands (`openclaw agents add/delete/bind/unbind/bindings/set-identity`) where possible, with config patching only for Discord channel-specific routing (which the CLI doesn't support yet).

## What It Does

1. **Creates agent workspace** (SOUL.md, HEARTBEAT.md, IDENTITY.md, memory/)
2. **Registers agent** via `openclaw agents add`
3. **Creates Discord channel** (optional) with topic
4. **Binds agent to channel** (routing via config patch)
5. **Copies auth profiles** (SecretRef-backed, from default agent)
6. **Sets up cron jobs** (optional daily memory)

## CLI Quick Reference

These native commands are available without the skill:

```bash
# List agents and bindings
openclaw agents list
openclaw agents bindings

# Add/remove agents
openclaw agents add <id> --workspace <dir> --model <model> --non-interactive
openclaw agents delete <id>

# Channel-level routing (telegram, discord — not per-Discord-channel)
openclaw agents bind --agent <id> --bind discord
openclaw agents unbind --agent <id> --bind discord

# Identity
openclaw agents set-identity --agent <id> --name "Name" --emoji "🔬"
```

**Note:** `openclaw agents bind` works at the **channel level** (discord, telegram), not per-Discord-channel-ID. For routing specific Discord channels to specific agents, the skill's config patching is still needed.

## Scripts

| Script | Purpose |
|--------|---------|
| `create-agent.sh` | Full agent setup with Discord integration |
| `bind-channel.sh` | Bind existing agent to additional Discord channel |
| `list-agents.sh` | Show all agents and their Discord bindings |
| `remove-agent.sh` | Remove agent (config, crons, optionally workspace/channel) |
| `claim-category.sh` | Claim a Discord category for an agent |
| `sync-category.sh` | Sync all channels in a category to its owner |
| `list-categories.sh` | Show category ownership |

## Usage

### Create Agent with New Discord Channel

```bash
export DISCORD_GUILD_ID="123456789012345678"

~/.openclaw/skills/agent-council/scripts/create-agent.sh \
  --id watson \
  --name "Watson" \
  --emoji "🔬" \
  --specialty "Deep research and competitive analysis" \
  --create "research" \
  --category "987654321098765432"
```

This will:
- Create `<workspace>/agents/watson/` with SOUL.md, HEARTBEAT.md, IDENTITY.md
- Register agent via `openclaw agents add`
- Create Discord #research channel in the specified category
- Bind watson → #research (config patch for channel-specific routing)
- Add #research to guild allowlist
- Copy auth profiles from default agent (SecretRef-backed)
- Create daily memory cron at 11:00 PM (use `--no-cron` to skip)

### Create Agent with Existing Channel

```bash
./create-agent.sh \
  --id sage \
  --name "Sage" \
  --emoji "💰" \
  --specialty "Personal finance" \
  --channel "234567890123456789"
```

### Bind Agent to Additional Channel

```bash
./bind-channel.sh --agent forge --channel "345678901234567890"
./bind-channel.sh --agent forge --create "defi" --category "456789012345678901"
```

### List Current Setup

```bash
./list-agents.sh
```

### Remove Agent

```bash
# Remove from config only (keeps workspace)
./remove-agent.sh --id test-agent

# Full removal (workspace trashed, channels deleted)
./remove-agent.sh --id test-agent --delete-workspace --delete-channel
```

### Category Ownership

```bash
./claim-category.sh --agent chief --category 123456789012345678 --sync
./list-categories.sh
./sync-category.sh --category 123456789012345678
```

---

## Agent Cron Jobs

### Delivery Pattern

**Option A: `--announce` (preferred for simple jobs)**

```bash
openclaw cron add \
  --name "My Task" \
  --agent myagent \
  --cron "0 9 * * *" \
  --session isolated \
  --model sonnet \
  --announce --channel discord --to "channel:YOUR_CHANNEL_ID" \
  --message "Do the task."
```

**Option B: `delivery: none` + message tool (for custom formatting)**

```bash
openclaw cron add \
  --name "My Task" \
  --agent myagent \
  --cron "0 9 * * *" \
  --session isolated \
  --model sonnet \
  --message "Do the task. Then send the result to Discord using the message tool (action=send, channel=discord, target=channel:YOUR_CHANNEL_ID)."
```

**⚠️ Common mistake:** `--channel` expects the platform name (`discord`), `--to` expects the destination (`channel:ID`).

### Heartbeat vs Cron

- **Heartbeat:** Multiple checks batched, needs conversation context, timing can drift
- **Cron:** Exact timing, task isolation, different model, one-shot reminders

### Key Rules

- `delivery.mode` = `"none"` when the payload handles its own delivery via message tool
- Set `timeoutSeconds` to 90-120 for tool-using tasks (default 60 is often too tight)
- Always check for duplicate cron names before creating: `cron action=list`

---

## Options Reference

### create-agent.sh

| Option | Required | Description |
|--------|----------|-------------|
| `--id` | ✓ | Agent ID (lowercase, no spaces) |
| `--name` | ✓ | Display name |
| `--emoji` | ✓ | Agent emoji |
| `--specialty` | ✓ | What the agent does |
| `--model` | | Model (default: claude-sonnet-4-6) |
| `--channel` | | Existing Discord channel ID |
| `--create` | | Create new channel with this name |
| `--category` | | Category ID for new channel |
| `--topic` | | Channel topic (auto-generated if not set) |
| `--cron` | | Daily memory cron time (default: 23:00) |
| `--no-cron` | | Skip daily memory cron setup |
| `--tz` | | Timezone (default: America/New_York) |
| `--own-category` | | Claim a Discord category (auto-binds all channels) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_GUILD_ID` | For `--create` | Your Discord server ID |
| `AGENT_WORKSPACE_ROOT` | No | Agent workspace root (default: `~/workspace/agents`) |
