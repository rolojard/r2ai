# Agent Storage Areas

## Purpose
Each agent has a dedicated storage area for frequently used items, templates, configurations, and reusable components. This allows agents to work efficiently without repeatedly fetching external resources.

## Structure
```
.claude/agent_storage/
├── super-coder/           # Python libraries, code templates, testing frameworks
├── imagineer-specialist/  # R2D2 components, servo configs, audio files
├── qa-tester/            # Test suites, validation tools, quality metrics
├── project-manager/      # Project templates, workflows, coordination tools
├── star-wars-specialist/ # Canon references, audio clips, character data
├── video-model-trainer/  # Model weights, datasets, training configs
├── web-dev-specialist/   # Web templates, frameworks, deployment configs
├── ux-dev-specialist/    # Design patterns, accessibility tools, research data
└── nvidia-orin-nano-specialist/ # Hardware configs, optimization scripts
```

## Usage Guidelines
- Store frequently accessed items to reduce external dependencies
- Keep storage organized with clear naming conventions
- Update storage as projects evolve
- Share storage items between agents when appropriate