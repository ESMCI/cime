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
- Follow the AI usage and human review policy in `doc/source/contributing-guide.rst` when assisting with contributions.
- Remind the human operator to review and understand the complete PR changes before requesting review; do not claim they have done so unless they confirm it.

## Commits and PRs
- Use Conventional Commits standard for PR titles, and commit messages.
- Commit or push changes only when the user explicitly asks.
- Submit jobs to batch systems only with the user's approval.
- Clearly report which validation checks were run and their results; identify checks that were not run.
