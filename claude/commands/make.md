---
description: Create a new specialized sub-agent using the agent-config-generator
allowed-tools: Task
---

# Make Agent Command

Task: Use the agent-config-generator to create a new sub-agent for: $ARGUMENTS

The agent-config-generator will:
- Analyze the requirements
- Consult with expert models via Zen MCP
- Select appropriate tools and MCP servers
- Generate comprehensive workflows
- Write the complete agent configuration to `.claude/agents/`