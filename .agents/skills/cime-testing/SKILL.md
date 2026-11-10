---
name: cime-testing
description: Use when writing, modifying, or running CIME Python unit or system tests with pytest.
---

# CIME testing

## Common standards

- Use `pytest`; use `pytest-cov` when coverage is needed.
- Prefer dependency injection; use mocks only when necessary.
- Keep tests deterministic.
- Place tests under `CIME/tests`.
- Follow this order within each test: context, mocks, act, assert.
- Follow TDD: for new behavior, write a failing test before implementation.
- Cover success, failure, and edge cases.
- Use pytest for new test modules. When adding to an existing test module,
  follow its established style; do not convert or mix test styles solely to use
  pytest.
- When a test fails, verify intended behavior before changing code or tests;
  do not weaken tests to make them pass.

Use the repository runner for CIME pytest tests.

## Unit tests

Use for `CIME/tests/test_unit*`.

- File name: `test_unit_<class>.py`
- Test method: `test_<unit>_<condition>`
- New functionality: write the failing test first, then implement it.

```bash
./devtools/run_tests unit
./devtools/run_tests unit -- CIME/tests/test_unit_<class>.py
```

For manual runs:

```bash
pytest --machine <machine> CIME/tests/test_unit_<class>.py \
  --cov=<module> --cov-report term-missing
```

## System tests

Use for `CIME/tests/test_sys*`.

- File name: `test_sys_<feature>.py`
- Test method: `test_<feature>_<condition>`
- Test outputs are in `${PWD}/storage`; ask the user to resolve access issues.
- Before every batch submission, ask for approval. Do not reuse a previous
  approval; only then pass `--allow-batch`.

```bash
./devtools/run_tests system
./devtools/run_tests system -- CIME/tests/test_sys_<target>.py
```

The runner retains system-test artifacts, excludes the intentionally failing
full-system test, and supports explicit `docker` or `podman` backends.

## Combined suite

```bash
./devtools/run_tests all
```

Pass one or more pytest paths or node IDs after `--` to target tests. Report
validation that was not run.
