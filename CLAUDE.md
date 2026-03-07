# CLAUDE.md

This file provides guidance for AI assistants (Claude Code and similar tools) working in this repository.

## Repository Status

This repository is newly initialized. As the project grows, this file should be updated to reflect the actual codebase structure, conventions, and workflows.

---

## Development Workflow

### Branch Conventions

- Feature branches: `feature/<short-description>`
- Bug fixes: `fix/<short-description>`
- Claude Code branches: `claude/<task-description>-<session-id>`
- Never commit directly to `main` or `master`

### Commit Messages

Use clear, imperative-style commit messages:

```
Add user authentication module
Fix null pointer exception in data parser
Refactor database connection pooling
```

- First line: 50 characters or fewer, imperative mood
- Blank line, then body if needed (wrap at 72 characters)
- Reference issue numbers where applicable: `Fixes #42`

### Git Push Protocol

- Always push with tracking: `git push -u origin <branch-name>`
- Claude Code branches must follow: `claude/<description>-<session-id>`
- Retry on network failure with exponential backoff: 2s, 4s, 8s, 16s

---

## Code Conventions

### General Principles

- **Simplicity first**: Write the minimum code needed. Avoid over-engineering.
- **No speculative features**: Only implement what is explicitly requested.
- **No unnecessary comments**: Only comment where logic is non-obvious.
- **No unused code**: Delete unused variables, imports, and dead code.

### Security

- Never commit secrets, API keys, or credentials.
- Validate all user input at system boundaries.
- Avoid command injection, SQL injection, XSS, and other OWASP Top 10 vulnerabilities.
- Use `.env` files for secrets; add them to `.gitignore`.

### Error Handling

- Handle errors at system boundaries (user input, external APIs, file I/O).
- Do not add error handling for impossible scenarios.
- Let internal errors propagate unless there is a specific recovery strategy.

---

## Project Structure (To Be Updated)

As this project is new, the structure will be defined as development progresses. Update this section once files and directories are established:

```
<root>/
├── CLAUDE.md          # This file
├── README.md          # Project overview and setup instructions
└── ...                # To be added
```

---

## Testing

- Write tests for new functionality before or alongside implementation.
- Run the full test suite before pushing.
- Do not skip tests or use workarounds to make tests pass artificially.

Update this section with actual test commands once a testing framework is established.

---

## Key Reminders for AI Assistants

1. **Read before editing**: Always read a file before modifying it.
2. **Minimal changes**: Only make changes directly required by the task.
3. **Check reversibility**: Confirm with the user before destructive operations (force push, deleting branches, dropping data).
4. **No speculative refactoring**: Do not clean up surrounding code when fixing a bug.
5. **Update CLAUDE.md**: When new conventions, tooling, or significant structure is added, update this file.
6. **Verify the branch**: Always confirm you are on the correct feature branch before committing.
