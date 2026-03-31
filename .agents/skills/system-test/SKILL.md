---
name: unit-test
description: Use when writing or modifying CIME end-to-end tests.
---

# CIME System Tests

## Overview

Use this skill to write system tests that match CIME conventions exactly.

The goal is consistency and reliability:
- Each test should be self contained.
- Keep tests deterministic.
- Match project structure and naming.
- Reuse common helpers instead of ad-hoc setup.
- Verify behavior and side effects.

## When to use

Use this skill when:
- You are writing or modifying python system tests under `CIME/tests`. Test files will be prefixed with `test_sys`.

Do not use this skill to write unit tests.

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

- Test file: `test_sys_<target>.py`
- Test method: `test_<target>_<condition>`

## Unit test workflow

1. Identify the target and condition under `CIME/`.
2. Place test in matching `CIME/tests/test_sys_<target>.py`.
3. Name class/methods with project naming convention.
4. Execute method once in Act section.
5. Assert result + mock interactions.
6. Run the specific test, then broader suite if needed.
7. Check `${PWD}/storage` for the output from the tests.
7. Check coverage.

## Commands

```bash
docker run -it --rm -e CIME_MODEL=<model> -e CIME_MACHINE=docker -v ${PWD}/..:/root/model -v ${PWD}/storage:/root/storage -w /root/model/cime ghcr.io/esmci/cime:latest pytest --no-teardown CIME/tests/test_sys_<target>.py
```

## Common Mistakes
