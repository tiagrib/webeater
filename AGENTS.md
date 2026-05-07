# MetaKitchen Agent Guide

This is a multi-repository workspace. Each sub-repo may have its own agent instruction files.

## Structure

```
meta-repo/
├── .claude/CLAUDE.md                ← root instructions (read by ALL agents)
├── AGENTS.md                        ← you are here
├── CUSTOM.md                        ← project-wide rules for all agents
├── metak-shared/                    ← shared docs: architecture, API contracts, glossary
│   ├── overview.md                  ← project goals and current state
│   ├── architecture.md              ← system boundaries and data flow
│   ├── api-contracts/               ← interface specs between components
│   ├── coding-standards.md          ← linting, commits, reviews
│   ├── glossary.md                  ← domain terms
│   └── LEARNED.md                   ← discovered methods and tricks
├── metak-orchestrator/              ← orchestrator workspace (TASKS.md, STATUS.md, EPICS.md)
├── <subfolder..>*/                  ← application sub-repos with subagent
├── <subfolder..>*/                  ← application sub-repos with subagent
├── <...>*/
└── <project>.code-workspace         ← VS Code multi-root workspace
```

## Agent Roles

### Orchestrator

The orchestrator agent coordinates cross-repo work. It:

- **Writes and maintains `metak-shared/` docs** (overview, architecture, API contracts, glossary) for user review.
- **Breaks work into tasks** in `metak-orchestrator/TASKS.md` with acceptance criteria.
- **Configures workers** by writing `CUSTOM.md` files in each target repo.
- **Spawns worker agents** scoped to individual repos and monitors progress.
- **Reviews worker completion reports** against acceptance criteria and product goals, iterating with follow-up tasks until quality is met.
- **Never writes application code** — only shared docs, tasks, and CUSTOM.md files.

See `metak-orchestrator/AGENTS.md` for full orchestrator instructions.

### Worker Agents

Worker agents operate within a single sub-repo. They:

- Read their assignment from the orchestrator (or `metak-orchestrator/TASKS.md`).
- Read `AGENTS.md` and `CUSTOM.md` in their target directory for instructions.
- Consult `metak-shared/api-contracts/` for interfaces they must conform to.
- **Write a completion report** when done. Summarize what was implemented, what tests were run and their results, any deviations from the task spec, and any open concerns. Update `metak-orchestrator/STATUS.md` with this report.
- **Treat `metak-shared/` as read-only.** Propose changes via the orchestrator.
- **Document learnings** in `metak-shared/LEARNED.md`.

## Agent Rules

1. **Read `.claude/CLAUDE.md` at the repo root** — it determines your role based on the task scope.
2. **One agent, one subfolder, one repo.** Workers do not work across multiple repos.
3. **API contracts live in `metak-shared/api-contracts/`.** Always reference these for cross-component interfaces.
4. **Consult `metak-shared/architecture.md`** for system boundaries and data flow.
5. **Verify integration contracts.** After modifying an interface, verify the implementation matches the contract in `metak-shared/api-contracts/` exactly.
6. **Check known deviations.** API contract files may list known bugs or deviations in an appendix — check before working against a contract.

## Coding Standards

Follow `metak-shared/coding-standards.md` for your repo's language.

## Project Structure

- Maintain a description of the current project structure in `STRUCT.md` within each sub-repo
- The structure should be a tree view with brief descriptions of each file and folder
- If at any point `STRUCT.md` does not exist, pause your current task and create it by analyzing the project
- Update `STRUCT.md` with every change to the project structure

## When Stuck

- Re-read the relevant `CUSTOM.md`, and `STRUCT.md` for context you may have missed
- Check `metak-shared/LEARNED.md` for known pitfalls and solutions
- Verify your assumptions against the running system, not documentation
- If still blocked, update `metak-orchestrator/STATUS.md` with what you tried and what failed

## Custom Instructions

Read and follow `CUSTOM.md` at the project root for project-wide rules that apply to all agents.
