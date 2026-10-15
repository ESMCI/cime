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
- Run CIME pytest tests with `./devtools/run_tests unit` or `./devtools/run_tests system`; pass multiple pytest targets after `--` to run a subset.
- Before running system tests on a batch-enabled host, ask the user whether batch submission is approved. Use `--allow-batch` only after approval.

## Documentation Standards
- Follow `Google Python Style Guide` for docstrings.
- Write documentation using Sphinx ReStructuredText.
- User documentation should answer what and how.
- Developer documentation should answer why and how.
- Update relevant documentation when changes affect user-facing behavior, workflows, or configuration. Document non-obvious code where needed.

## Commits and PRs
- Use Conventional Commits standard for PR titles, and commit messages.
- Commit or push changes only when the user explicitly asks.
- When asked to open a PR or create an issue, first read and follow the repository templates: `.github/pull_request_template.md` for PRs and the relevant template under `.github/ISSUE_TEMPLATE/` for issues. Preserve the template's sections and checklist, filling in or adapting placeholders as needed.
- Before opening a PR or creating an issue, draft the title and body using the applicable template and present them to the user for review. Do not submit until the user approves the draft.
- Before creating an approved PR, inspect the working-tree status, base branch, remote tracking, all commits in the PR, and the complete diff from the base. Confirm relevant validation results.
- Submit jobs to batch systems only with the user's approval.
- Clearly report which validation checks were run and their results; identify checks that were not run.
