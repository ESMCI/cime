---
name: unit-test
description: Use when writing or modifying CIME unit tests.
---

# CIME Unit Tests

## Overview

Use this skill to write unit tests that match CIME conventions exactly.

The goal is consistency and reliability:
- Keep tests deterministic.
- Match project structure and naming.
- Reuse common helpers instead of ad-hoc setup.
- Verify behavior and side effects.

## When to use

Use this skill when:
- You are writing or modifying python unit tests unit under `CIME/tests`. Test files will be prefixed with `test_unit`.

Do not use this skill to write end-to-end tests.

## Required frameworks and style

- Test framework: `pytest`
- Mocks: Use only when neccesary, prefer dependency injection.
- Deterministic: no random behavior in tests.

## Test structure

Follow this exact order within every test method:

```
# Context
values = ["a", "b", "c"]
env_mach = EnvMach()

# Mocks
env = MagicMock()

# Act
output = env_mach.get_values(values, env=env)

# Assert
assert output != None
env.assert_called_with()
```

## Placement rules

- Place tests under `CIME/tests`.

## Naming rules

- Test file: `test_unit_<unit>.py`
- Test method: `test_<unit>_<condition>`

## Unit test workflow

1. Identify class and unit under `CIME/`.
2. Place test in matching `CIME/tests/test_unit_<class>.py`.
3. Name class/methods with project naming convention.
4. Execute method once in Act section.
5. Assert result + mock interactions.
6. Run the specific test, then broader suite if needed.
7. Check coverage.

## Commands

```bash
pytest --machine docker CIME/tests/test_unit_<class>.py
```

## Common Mistakes
