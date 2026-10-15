---
name: cime-sys-testing-claude
description: Use when writing or running CIME Python system tests with pytest. Routes to the shared CIME system-testing guidance and test runner.
---

# CIME system testing

The canonical, harness-independent system-testing guidance is in
``.agents/skills/cime-sys-testing/SKILL.md``. Read and follow it for test
structure, placement, and style.

Before running system tests on a batch-enabled host, ask the user whether batch
submission is approved. Use ``--allow-batch`` only after approval. The runner
selects a suitable host or container, defaults to retaining artifacts, and
caches the versioned input data for container runs.

Run the full system-test suite with:

```bash
./scripts/run_tests system
```

Pass one or more pytest paths or node IDs after ``--`` to target tests:

```bash
./scripts/run_tests system -- CIME/tests/test_sys_example.py CIME/tests/test_sys_other.py::TestOther::test_case
```

Pytest prints its test summary and terminal coverage table. Report validation
that was not run.
