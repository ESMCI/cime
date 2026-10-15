---
name: cime-unit-testing-claude
description: Use when writing or running CIME Python unit tests with pytest. Routes to the shared CIME unit-testing guidance and test runner.
---

# CIME unit testing

The canonical, harness-independent unit-testing guidance is in
``.agents/skills/cime-unit-testing/SKILL.md``. Read and follow it for test
structure, placement, and style.

Run the full unit-test suite with:

```bash
./devtools/run_tests unit
```

Pass one or more pytest paths or node IDs after ``--`` to target tests:

```bash
./devtools/run_tests unit -- CIME/tests/test_unit_example.py CIME/tests/test_unit_other.py::TestOther::test_case
```

Pytest prints its test summary and terminal coverage table. Report validation
that was not run.
