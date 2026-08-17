---
name: cime-sys-testing
description: Use when writing or modifying CIME sys (end-to-end) tests.
---

# CIME System Tests

## Overview

### Requirements
- Supported model, if this cannot be determined as the user.

### Goals
- Consistency between tests.
- Idempotency between runs.
- Create and reuse common helpers instead of ad-hoc setups.
- Verify behavior.
- Test side effects.
- Check for regression.

## When to use

Use this skill when writing/modifying python system tests under `CIME/tests` that are prefixed with `test_sys`.

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

- Test file: `test_sys_<feature>.py`
- Test method: `test_<feature>_<condition>`

## Unit test workflow
1. Identify the feature and conditions for end-to-end test.
2. Place test in matching `CIME/tests/test_sys_<feature>.py`.
3. Write tests for target feature.
4. Run tests.
6. Test outputs are located in `${PWD}/storage`. If you cannot access, ask user to fix permissions, then continue.
7. If tests failed, return to step 3 and adjust the test.
5. Check for regression.

# Run Testing
Try to determine `<model>`, ask user if unable.

```bash
docker run -it --rm -e CIME_MODEL=<model> -e CIME_MACHINE=docker -v ${PWD}/..:/root/model -v ${PWD}/storage:/root/storage -w /root/model/cime ghcr.io/esmci/cime:latest pytest --no-teardown --no-fortran CIME/tests/test_sys_<target>.py
```

## Common Mistakes
