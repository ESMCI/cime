---
name: cime-unit-test
description: Use when writing/modifying CIME unit tests.
---

# CIME Unit Tests

## Overview

### Goals
- Consistency between tests.
- Idempotency between runs.
- Create and reuse common helpers instead of ad-hoc setups.
- Verify behavior.
- Test side effects.
- Check coverage, should only ever increase.
- Check for regression.

## When to use

Use this skill when writing/modifying python unit tests under `CIME/tests` that are prefixed with `test_unit`.

Do not use this skill to write `sys` (end-to-end) tests.

## Required frameworks and style

- Test framework: `pytest`, `pytest-cov`
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

- Test file: `test_unit_<class>.py`
- Test method: `test_<unit>_<condition>`

# Testing

## Adding test for existing unit
1. Identify target unit for testing.
2. Analyze function implementation.
3. Write test checking for all combinations of input/output, errors, and edge cases.
4. Run tests and check for adaquate coverage.
5. If failing go back to step 2, continue until tests pass.

## Adding new test for new unit following TDD
1. Identify target unit required inputs/outputs.
2. Write test checking for all combinations of input/output, errors, and edge cases.
3. Run tests, should fail.
4. Implement unit.
5. Run tests and check for adaquate coverage.
6. If failing go back to step 4, continue until tests pass.

# Run Testing
- Identify a supported machine (exclude linux-generic), does not need to be the host.
- Use the machine name to run the tests.

## Commands

### List supported machines

```bash
./scripts/query_config --machines
```

### Run tests
```bash
pytest --machine <machine>  CIME/tests/test_unit_<class>.py --cov=<module> --cov-report term-missing
```

## Common Mistakes
