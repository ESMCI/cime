# AGENTS.md

## Project Standards

- Avoid adding external dependencies.

## Coding Standards

- Follow `PEP8` style guide.
- Always prefer dependency injection.
- Prefer implementations that work across Earth system models that use CIME. If model-specific logic seems necessary, ask the user how to proceed before adding it.
- Always lint and format files after creating or modifying.

### Python typing

- Fully annotate new Python functions and methods, including parameter and return types. Add variable annotations when inference is unclear or when they make an interface or data shape easier to understand.
- When changing existing Python code, add or update annotations on the functions and helpers being changed, but do not expand the task into typing unrelated legacy code.
- Prefer precise types and narrow optional values at runtime. Avoid `Any` and broad ignores; if unavoidable at an untyped or dynamic boundary, keep them local and explain why.
- Follow the Python-version compatibility and typing conventions of the files being changed. Prefer standard-library typing tools and do not add dependencies just for typing.
- Run `basedpyright` on changed Python files when it is available. Address errors introduced by the change; distinguish pre-existing findings from new ones and report any unresolved findings.

## Testing Standards

- Always follow TDD principals.
- Cover success, failure, and edge cases.
- When a test fails, verify the intended behavior before changing code or tests. Fix the implementation when it violates the requirement. Change a test only when the test is incorrect or the intended behavior has deliberately changed, and explain why. Do not weaken or rewrite tests just to make a failing implementation pass.
- Use pytest for new test modules. When adding tests to an existing module, follow that module's established style, including `unittest.TestCase` if it already uses it. Don't convert an existing module or mix styles just to follow this preference. If the appropriate style is unclear, ask the user how to proceed.
- Run CIME pytest tests with `./devtools/run_tests unit`, `./devtools/run_tests system`, or both suites with `./devtools/run_tests all`; pass multiple pytest targets after `--` to run a subset.
- Before running system tests on a batch-enabled host, ask the user whether batch submission is approved. Use `--allow-batch` only after approval.

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
- Before creating a commit, run `pre-commit` on all changed files and resolve any failures. If a hook cannot be run, report that before committing.
- When asked to open a PR or create an issue, first read and follow the repository templates: `.github/pull_request_template.md` for PRs and the relevant template under `.github/ISSUE_TEMPLATE/` for issues. Preserve the template's sections and checklist, filling in or adapting placeholders as needed.
- Before opening a PR or creating an issue, draft the title and body using the applicable template and present them to the user for review. Do not submit until the user approves the draft.
- Before creating an approved PR, inspect the working-tree status, base branch, remote tracking, all commits in the PR, and the complete diff from the base. Confirm relevant validation results.
- Clearly report which validation checks were run and their results; identify checks that were not run.
