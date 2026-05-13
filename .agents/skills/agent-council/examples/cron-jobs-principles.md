# Cron Job Creation Rules

**MANDATORY for all agents creating cron jobs or reminders.**

## The One Pattern That Works

```
sessionTarget: "isolated"
payload.kind: "agentTurn"
delivery.mode: "none"
```

The payload message MUST include explicit instructions to send to Discord using the message tool.

## Example: Discord Reminder

```json
{
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "Remind the user about X. Send to Discord channel <CHANNEL_ID> using the message tool (action=send, channel=discord, target=channel:<CHANNEL_ID>). Prepend <@USER_ID>."
  },
  "delivery": { "mode": "none" }
}
```

## What NOT To Do

❌ **NEVER** use `sessionTarget: "main"` + `payload.kind: "systemEvent"` for reminders — these inject into the main session silently and don't post to Discord.

❌ **NEVER** use `delivery.mode: "announce"` — the `delivery.channel` field expects a platform name (e.g., "discord"), not a channel ID. Misuse causes unpredictable routing.

❌ **NEVER** put a channel ID in `delivery.channel` — it's for platform names only.

## Channel Reference

When creating a job, you MUST know which Discord channel to target. Add your own channels here:

- `CHANNEL_ID` — #general
- `CHANNEL_ID` — #alerts
- `CHANNEL_ID` — #reports

## Key Rules

1. Always use `isolated` + `agentTurn` — this spawns a real agent session that can use tools
2. The payload message should tell the agent WHAT to do AND WHERE to send it
3. `delivery.mode: "none"` — the agent handles delivery itself via the message tool
4. For one-time reminders, add `"deleteAfterRun": true`
5. For scheduled reminders, use `schedule.kind: "cron"` with a cron expression and timezone
