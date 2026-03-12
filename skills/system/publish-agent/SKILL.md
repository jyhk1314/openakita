---
name: publish-agent
description: Publish a local Agent to the Synapse Platform Agent Store. Use when user wants to share, distribute, or publish an Agent to the community hub.
system: true
handler: agent_hub
tool-name: publish_agent
category: Platform
---

# Publish Agent

将本地 Agent 发布到 Synapse 平台 Agent 商店。

## Tools

- `publish_agent` - Package and prepare a local Agent for publishing

## Usage

Use this skill when the user wants to:
- Share a local Agent to the community
- Publish an Agent to the Synapse hub
- Package an Agent for distribution

## Parameters

- `profile_id` (required): The local Agent profile ID to publish
- `description` (optional): Description for the platform listing
- `category` (optional): Category for the listing
- `tags` (optional): Tags for discoverability

## Examples

- "把我的客服 Agent 发布到 Hub"
- "分享这个 Agent 到社区"
