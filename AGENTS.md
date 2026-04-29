# AGENTS.md

## Project Standards
- Avoid adding external dependencies.

## Coding Standards
- Follow `PEP8` style guide.
- Always prefer dependency injection.
- Always prefer generalized implementation; avoid split logic that depends on a specific model.
- Always lint and format files after creating or modifying.

## Testing Standards
- Always follow TDD principals.
- Cover success, failure, and edge cases.
- Always follow pytest patterns, not `unittest.TestCase`.

## Documentation Standards
- Follow `Google Python Style Guide` for docstrings.
- Write documentation using Sphinx ReStructuredText.
- User documentation should answer what and how.
- Developer documentation should answer why and how.

## Commits and PRs
- Use Conventional Commits standard for PR titles, and commit messages.
