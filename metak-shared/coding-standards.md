# Coding Standards

- All code must pass linting and tests before committing.
- Never import directly from another repo's source code. Use shared contracts in `metak-shared/api-contracts/`.
- When in doubt about system boundaries, consult `metak-shared/architecture.md`.
- **No emojis in code, commits, or documentation.** Use text alternatives like `[OK]`, `[FAIL]`, `[WARN]` when status indicators are needed.

## Commit Messages

Follow Conventional Commits: `type(scope): description`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Code Review

- All changes go through PRs.
- At least one human approval required before merge.
- CI must pass.

## Testing

- All code must have tests that pass before committing.
- Integration test conventions are project-specific — define them in the `tests/CUSTOM.md` file.

## Documentation

- Do not document every change you made — docs should reflect the current state of the project, not its history
- Before writing documentation, check if the information already exists elsewhere
- Check STRUCT.md to understand where documentation files are located
