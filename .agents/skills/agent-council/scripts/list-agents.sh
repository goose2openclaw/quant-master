#!/bin/bash

# List all agents and their Discord bindings
# Updated for OpenClaw 2026.3.x — uses `openclaw agents list` and `openclaw agents bindings`

echo "═══════════════════════════════════════════════════════════"
echo "  Agent Council - Current Roster"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Use native CLI for agent list
openclaw agents list 2>/dev/null | grep -v "^Config warnings" | grep -v "^$" | grep -v "^🦞"

echo ""
echo "───────────────────────────────────────────────────────────"
echo "  Discord Bindings"
echo "───────────────────────────────────────────────────────────"
echo ""

# Use native CLI for bindings
openclaw agents bindings 2>/dev/null | grep -v "^Config warnings" | grep -v "^🦞"

echo ""
