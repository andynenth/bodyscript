#!/bin/bash
# Script to start Claude Code with proper TMPDIR settings for Playwright MCP

echo "Setting up environment for Claude Code with Playwright MCP support..."

# Create a user-specific temp directory
export TMPDIR="$HOME/tmp"
mkdir -p "$TMPDIR"

echo "TMPDIR set to: $TMPDIR"
echo "Starting Claude Code..."

# Start Claude Code with the correct environment
claude

echo "Claude Code session ended."