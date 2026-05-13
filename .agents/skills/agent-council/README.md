# Agent Council

**Discord-integrated agent management for OpenClaw.**

Updated for **OpenClaw 2026.3.x** — uses native CLI commands where possible, with config patching only for Discord channel-specific routing.

## What OpenClaw Provides (Native CLI)

```bash
openclaw agents list              # List all agents
openclaw agents bindings          # Show channel bindings
openclaw agents add <id>          # Register a new agent
openclaw agents delete <id>       # Remove an agent
openclaw agents bind --agent <id> --bind discord    # Channel-level routing
openclaw agents unbind --agent <id> --bind discord
openclaw agents set-identity --agent <id> --name "Name" --emoji "🔬"
```

## What Agent Council Adds

The CLI handles agent registration, but spinning up a fully Discord-connected agent still requires: creating the channel, setting topics, adding to allowlists, per-channel-ID binding (which `agents bind` doesn't support), workspace scaffolding, and daily memory cron. Agent Council does all of that in one command.

- **Discord channel creation** with auto-generated topic
- **Per-channel-ID routing** (specific Discord channels → specific agents)
- **Safe config merging** (arrays replace in OpenClaw — Agent Council handles the merge)
- **Workspace scaffolding** (SOUL.md, HEARTBEAT.md, IDENTITY.md, memory/)
- **Daily memory cron** by default
- **Category ownership** (claim categories, auto-bind new channels)

## Quick Start

```bash
# Install
git clone https://github.com/itsahedge/agent-council.git ~/.openclaw/skills/agent-council
openclaw gateway config.patch --raw '{"skills":{"entries":{"agent-council":{"enabled":true}}}}'

# Set your Discord server ID
export DISCORD_GUILD_ID="123456789012345678"

# Create agent with Discord channel + daily memory
~/.openclaw/skills/agent-council/scripts/create-agent.sh \
  --id watson \
  --name "Watson" \
  --emoji "🔬" \
  --specialty "Deep research" \
  --create "research" \
  --category "987654321098765432"
```

This creates:
- Agent registered via `openclaw agents add` + `set-identity`
- Agent workspace with SOUL.md, HEARTBEAT.md, IDENTITY.md, memory/
- Discord #research channel with topic
- Per-channel binding: watson → #research
- Allowlist entry for #research
- Daily memory cron at 23:00 ET

## Scripts

| Script | Purpose |
|--------|---------|
| `create-agent.sh` | Full agent setup (workspace, Discord, binding, cron) |
| `bind-channel.sh` | Bind agent to additional channels |
| `list-agents.sh` | Show all agents and bindings (wraps native CLI) |
| `remove-agent.sh` | Clean removal (unbind, delete, workspace, channel) |
| `claim-category.sh` | Claim a Discord category for an agent |
| `sync-category.sh` | Bind all channels in a category to its owner |
| `list-categories.sh` | Show category ownership |

## Why Config Patch Is Still Needed

`openclaw agents bind` works at the **channel level** (discord, telegram) — not per-Discord-channel-ID. For routing specific Discord channels to specific agents (e.g., #research → watson, #finance → sage), the `bindings` array config patch is still required. Agent Council handles this safely.

## Key Features

### Safe Config Patching
OpenClaw's `config.patch` replaces arrays, it doesn't merge them. Agent Council:
- Fetches current config first
- Merges new entries with existing
- Validates before patching
- Aborts if config fetch fails (prevents accidental wipes)

### Binding Priority
New bindings are **prepended** (not appended), so specific channel bindings take priority over catch-all rules.

### Daily Memory by Default
Every agent gets a nightly cron that triggers memory consolidation. Use `--no-cron` to opt out.

### Auth Profiles
Agent creation copies SecretRef-backed auth profiles from the default agent — no plaintext tokens in config.

### Category Ownership
Agents can own Discord categories:

```bash
# Claim a category for an agent
./claim-category.sh --agent chief --category 123456789012345678 --sync

# After adding channels in Discord:
./sync-category.sh --category 123456789012345678

# See all owned categories
./list-categories.sh
```

### Cron Job Patterns
Agents can create their own cron jobs. The key rule: Always use `sessionTarget: "isolated"` + `agentTurn` + `delivery.mode: "none"`, and have the payload explicitly send to Discord via the message tool. See [examples/cron-jobs-principles.md](./examples/cron-jobs-principles.md).

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_GUILD_ID` | For `--create` | Your Discord server ID |
| `AGENT_WORKSPACE_ROOT` | No | Agent workspace root (default: `~/clawd/agents`) |

## Documentation

See [SKILL.md](./SKILL.md) for full options reference, cron patterns, and manual setup instructions.

## License

MIT
