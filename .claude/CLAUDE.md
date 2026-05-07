Read and follow `AGENTS.md` at the repository root for project structure and agent roles.
Read and follow `metak-shared/coding-standards.md` for coding conventions.

## Agent role — DEFAULT TO ORCHESTRATOR

ALL user prompts go through the orchestrator role first. Read and follow `metak-orchestrator/AGENTS.md` for your workflow.

You may ONLY act as a direct worker if the user explicitly tells you to skip orchestration (e.g., "just fix this one file").

For cross-repo work, you MUST orchestrate — plan first, then spawn worker agents. You do NOT write application code yourself.

## Shared knowledge

- `metak-shared/overview.md` — project goals and current state
- `metak-shared/architecture.md` — system boundaries, service map, data flow
- `metak-shared/api-contracts/` — interface specs between components
- `metak-shared/glossary.md` — domain terms
- `metak-shared/coding-standards.md` — linting, commits, reviews

Treat `metak-shared/` as **read-only** unless you are the orchestrator.
