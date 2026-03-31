---
name: documentation writer
description: Use when writing documentation.
---

# CIME documentation writer

## Overview

Use this skill to write documentation.

The goal is to write clear and complete documentation.
- Explain when and how to use tools.
- Provide working examples.
- Note any preconditions that must be met.
- Note any side effects.
- Group related topics in common directories.

## When to use

Use this skill when:
- Writing documentation under `doc/`.
- Writing docstrings under `CIME/`.

## Formats

- Documentation format: `Sphinx ReStructuredText`.
- Docstring format: `Google Style Python Docstrings`.

## Documentation placement rules

- Place Control Case System documentation under `doc/source/ccs/`.
- Place System Testing documentation under `doc/source/system_testing.rst`.
- Place tool documentation under `doc/source/tools/`.
- Place developer documentation under `doc/source/contributing-guide.rst`.

## Naming rules

- File use kebab-case where filename is short description or tool name e.g. `query-configuration.rst`.
- Group similar docuemntations under parent directories e.g. everything under `doc/source/ccs` related to the Case Control System.

## Docuemntation Workflow

1. Identify the topic being documented.
2. Locate where to place file under `doc/source`.
3. Add documentation and examples.
4. Find areas that should link to new documentation.
5. Ask user to review.
6. Apply feedback and loop until user is satisfied with documentation.

## Docstring Workflow

1. Identify the method/function being documented.
2. Review the code.
3. Create the docstring, provide examples and explainations, note side effects.
4. Ask user to review.
5. Apply feedback and loop until user is satisfied with documentation.

## Commands

Build the documentation:

```bash
make -C doc/ html
```
