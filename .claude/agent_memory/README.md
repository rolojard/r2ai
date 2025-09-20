# Agent Memory Tracking

## Purpose
Each agent maintains local memory of their work progress, current tasks, project context, and learning patterns. This ensures continuity across sessions and enables intelligent task resumption.

## Structure
```
.claude/agent_memory/
├── super-coder/
│   ├── current_work.json     # Active tasks and progress
│   ├── project_context.json  # Project understanding and state
│   ├── code_patterns.json    # Learned patterns and solutions
│   └── session_history.json  # Historical work summary
├── imagineer-specialist/
│   ├── build_progress.json   # R2D2 component status and next steps
│   ├── hardware_state.json   # Current hardware configuration
│   └── animation_library.json # Motion patterns and sequences
└── [similar structure for each agent]
```

## Memory Files
- **current_work.json**: Active tasks, progress, next steps
- **project_context.json**: Understanding of project goals and state
- **patterns.json**: Learned solutions and reusable knowledge
- **session_history.json**: Summary of completed work

## Usage Guidelines
- Update memory after significant work completion
- Use memory to resume work intelligently
- Share relevant context with other agents
- Maintain clean, structured memory records