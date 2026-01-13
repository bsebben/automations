# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository contains personal automation tools and utilities for macOS. Tools are typically standalone Python scripts or shell scripts.

## Structure

Each tool lives in its own directory with:
- Main executable script(s)
- `lib/` subdirectory for shared modules (if needed)
- Tool-specific README.md with usage instructions

## Current Tools

- **screenshot-tool**: macOS screenshot utility with ShareX-style window highlighting and annotation support
  - Main script: `screenshot-sharex.py` (Python with pyobjc)
  - Shell wrapper: `screenshot-annotate.sh`
  - Dependencies: `pyobjc`, `pyobjc-framework-Quartz`, `pyobjc-framework-Cocoa`

## Conventions

- Python scripts should be executable (`chmod +x`) with proper shebang
- Use `lib/` for reusable modules within a tool
- Each tool should have its own README.md documenting usage

## User Info (for MCP integrations)

- **Slack User ID:** U06RSGA2GJJ
- **Slack Username:** brian.sebben
- **Email:** brian.sebben@gusto.com

## MCP Server Notes

### Slack (slack-gusto)
- Can send messages to channels
- Can mention users with `<@USER_ID>` format
- Cannot send direct messages (DMs)

### Google Drive (gdrive-gusto)
- Search and fetch files

### Jira/Confluence (jira-confluence-gusto)
- Search across both Jira issues and Confluence pages
