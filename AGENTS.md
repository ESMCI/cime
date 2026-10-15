# AGENTS.md

## Project Standards
- Avoid adding external dependencies.

## Coding Standards
- Follow `PEP8` style guide.
- Always prefer dependency injection.
- Prefer implementations that work across Earth system models that use CIME. If model-specific logic seems necessary, ask the user how to proceed before adding it.
- Always lint and format files after creating or modifying.

## Testing Standards
- Always follow TDD principals.
- Cover success, failure, and edge cases.
- Use pytest for new test modules. When adding tests to an existing module, follow that module's established style, including `unittest.TestCase` if it already uses it. Don't convert an existing module or mix styles just to follow this preference. If the appropriate style is unclear, ask the user how to proceed.

## Documentation Standards
- Follow `Google Python Style Guide` for docstrings.
- Write documentation using Sphinx ReStructuredText.
- User documentation should answer what and how.
- Developer documentation should answer why and how.
- Follow the AI usage and human review policy in `doc/source/contributing-guide.rst` when assisting with contributions.
- Remind the human operator to review and understand the complete PR changes before requesting review; do not claim they have done so unless they confirm it.
- Update relevant documentation when changes affect user-facing behavior, workflows, or configuration. Document non-obvious code where needed.

## Commits and PRs
- Use Conventional Commits standard for PR titles, and commit messages.
- Commit or push changes only when the user explicitly asks.
- Submit jobs to batch systems only with the user's approval.
- Clearly report which validation checks were run and their results; identify checks that were not run.
