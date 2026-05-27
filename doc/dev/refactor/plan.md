# CIME Refactor Plan

Incremental refactor to improve modularity, error handling, and testability
while preserving compatibility with external models (E3SM, CESM, NorESM).

**Core principle: reorganize existing code, don't rewrite it.** Move functions
to better homes, break apart oversized modules, improve error handling. Don't
wrap standard library APIs in abstraction layers — `os.path`, `subprocess`,
`os.environ`, and `time` are already easily mockable with `unittest.mock.patch`.

See also: `implementation.md` for detailed tasks, `feature_srcroot.md` for
config loading changes.

---

## Compatibility-First Policy

**Preserve current usage patterns unless change is absolutely required.**

Breaking changes must be:
- Explicitly justified
- Accompanied by migration plan
- Validated with external models

---

## Package Structure

```
CIME/
├── core/             # Reorganized internals (all implementation lives here)
│   ├── config/       # Bootstrap, SRCROOT, config loading
│   ├── batch/        # Batch/scheduler logic (from existing code)
│   ├── build/        # Build logic (from existing code)
│   ├── status/       # Status tracking (from status.py, case)
│   ├── locking/      # Lock management (from locked_files.py, case)
│   ├── exceptions.py # Typed exception hierarchy
│   ├── shell.py      # run_cmd, run_cmd_no_fail (from utils.py)
│   ├── logging.py    # Logging setup (from utils.py)
│   ├── fileops.py    # File helpers: safe_copy, symlink_force (from utils.py)
│   ├── time.py       # Time conversion helpers (from utils.py)
│   └── convert.py    # Type conversion helpers (from utils.py)
├── utils.py          # Thin re-exports only (was 2700 lines)
├── build.py          # Thin re-exports only
├── case/             # Case modules (thinned, delegates to core/)
├── XML/              # XML parsers (existing)
├── data/             # Config files (existing)
├── build_scripts/    # Compatibility wrapper (stable, unchanged)
├── SystemTests/      # System tests (existing)
├── Tools/            # CLI tools (existing)
└── tests/            # Tests
```

**Principle**: Move existing code into focused modules. Existing import paths
continue to work via re-exports until downstream models migrate.

---

## Migration Pattern

All implementation code moves to `CIME/core/`. Existing modules become thin
wrappers that import from `core/` and re-export, preserving current usage.

**Workflow for each piece of code**:
1. Move the function/class from its current location into the appropriate
   `CIME/core/` module
2. In the original file, add a thin re-export (so **external** callers like
   E3SM/CESM/NorESM are unaffected)
3. Update all **internal** CIME imports to point to the new `CIME/core/` location
4. Add/update tests against the new location

**Example** — moving `run_cmd` from `utils.py`:
```python
# CIME/core/batch/submitter.py  (new home — real code lives here)
def run_cmd(cmd, ...):
    # actual implementation moved here
    ...

# CIME/utils.py  (thin re-export for external consumers only)
from CIME.core.batch.submitter import run_cmd  # noqa: F401

# CIME/case/case_submit.py  (internal — updated to import from core/)
# Before:
#   from CIME.utils import run_cmd
# After:
from CIME.core.batch.submitter import run_cmd
```

This means:
- `CIME/core/` holds all implementation code
- **Internal** CIME code imports from `CIME/core/` directly
- `CIME/utils.py`, `CIME/build.py`, `CIME/case/*.py`, etc. keep thin
  re-exports **only** for external downstream consumers
- `CIME/build_scripts/`, `CIME/Tools/`, and case symlinked scripts remain
  as-is — they're entrypoints, not implementation
- Downstream models (E3SM, CESM, NorESM) continue working with zero changes
- Over time, downstream models can migrate to importing from `CIME/core/`
  directly, and the old re-exports can eventually be deprecated

---

## Approach: Reorganize, Don't Rewrite

### What we DO
- **Move** functions from bloated modules (`utils.py` at 2700 lines) into
  focused modules under `CIME/core/`
- **Consolidate** scattered functionality back into the classes that own it —
  free functions that take `case` as a parameter and mutate Case state should
  become methods on `Case` or its subsystem classes
- **Extract** coherent subsystems from `Case` (status tracking, locking,
  XML manipulation) into their own modules
- **Consolidate** scattered patterns (e.g. `sys.path` manipulation in 11 files)
- **Deduplicate** overlapping functionality (e.g. four copy functions in utils.py)
- **Improve** error handling with typed exceptions
- **Eliminate** star imports, global mutable state, and import-time side effects
- **Add** tests for code that currently lacks coverage
- **Fix** test infrastructure so unit tests can run without host model config

### Consolidation principle
If a free function takes an object and operates on its state, it should be a
method on that object. This is especially prevalent with `case`:

```python
# Before: free function reaching into Case
def case_build(case, ...):
    case._gitinterface  # accessing private state!
    case.get_value("EXEROOT")
    case.set_value("BUILD_COMPLETE", "TRUE")
    case.flush()

# After: method on Case (or delegated subsystem)
class Case:
    def build(self, ...):
        ...
```

**Key consolidation targets identified**:

| Current location | Functions | Problem |
|-----------------|-----------|---------|
| `build.py` | `case_build`, `clean`, `_clean_impl`, `post_build` | Access `case._gitinterface`, mutate Case state |
| `locked_files.py` | `check_lockedfiles`, `check_lockedfile`, `diff_lockedfile` | Pure Case integrity checks |
| `status.py` | `append_case_status`, `run_and_log_case_status` | Every caller extracts `caseroot` and `_gitinterface` from Case |
| `utils.py` | `transform_vars`, `is_comp_standalone`, `find_system_test` | Case queries living in a utility grab-bag |
| `test_scheduler.py` | `_get_time_est`, `_order_tests_by_runtime` | Module-level cache should be instance state on `TestScheduler` |
| `utils.py` | `safe_copy`, `copy_over_file`, `copyifnewer`, `copy_globs` | Overlapping copy semantics |

### Large classes and modules requiring decomposition

Beyond `Case`, several other classes and modules have grown too large and
exhibit the same god-object or scattered-function patterns:

**Large classes (>20 methods):**

| Class | File | Methods | Lines | Problem |
|-------|------|--------:|------:|---------|
| `Case` | `case/case.py` | 63 | 2600 | God object; functions scattered across ~10 files |
| `EnvBatch` | `XML/env_batch.py` | 43 | 1590 | Batch config, submission, queues, directives all in one |
| `GenericXML` | `XML/generic_xml.py` | 41 | 700 | Very wide interface; base for all XML classes |
| `NamelistGenerator` | `nmlgen.py` | 36 | 870 | Mixes definition lookup, resolution, streams, file I/O |
| `EnvMachSpecific` | `XML/env_mach_specific.py` | 35 | 770 | Module loading + env vars + mpirun + GPU config |
| `SystemTestsCommon` | `SystemTests/system_tests_common.py` | 33 | 1020 | Large but intentional base class |
| `TestScheduler` | `test_scheduler.py` | 28 | 1340 | Test creation + phase mgmt + submission + results |

**Procedural modules (free functions taking `case`, no class):**

| File | Lines | Funcs w/ `case` | Problem |
|------|------:|----------------:|---------|
| `case/case_st_archive.py` | 1395 | ~20 | Largest procedural module, all Case operations |
| `case/check_input_data.py` | 693 | ~12 | Scattered Case queries |
| `baselines/performance.py` | 612 | ~12 | Baseline comparison, all Case-dependent |
| `hist_utils.py` | 836 | ~7 | History file handling, all Case-dependent |

These are addressed primarily in **Slice 2** (EnvBatch → `core/batch/`),
**Slice 3B** (build decomposition), and **Slice 4** (Case, TestScheduler,
and procedural case/ modules).

### Cross-cutting issues (addressed primarily in Slice 1)

These issues cut across all modules and should be fixed early:

**Star imports** — `from CIME.XML.standard_module_setup import *` appears in
~60 source files, injecting `os`, `sys`, `re`, `expect`, `run_cmd`, etc. into
every namespace. `from CIME.test_status import *` appears in ~10 files,
exporting ~30 constants. These must be replaced with explicit imports to enable
static analysis and make dependencies visible.

**Global mutable state** — `GLOBAL = {}` in `utils.py:21` is used to pass
`SRCROOT` between `case.py`, `create_test.py`, and `utils.get_src_root()` via
implicit mutation. Other globals include `_CIMECONFIG` (singleton config cache),
`_TIME_CACHE` (test scheduler cache), and `_ALL_TESTS` (test registry cache).
Replace with explicit parameter passing or instance state.

**Import-time side effects** — `Servers/__init__.py` runs `shutil.which()` for
external tools at import time. `standard_script_setup.py` modifies `sys.path`
and `os.environ` at import time. `standard_module_setup.py` also modifies
`sys.path` at import time. These make imports non-deterministic and prevent
clean test isolation.

**Inconsistent error handling** — 5 different patterns in use: `expect()`,
`raise CIMEError`, `sys.exit()`, `raise RuntimeError`, and
`logger.fatal()` + `sys.exit()`. Standardize on `expect()` / `CIMEError`
for library code; `sys.exit()` only in CLI entrypoints.

**Circular imports** — The `Case` class injects methods from 10 sibling modules
at class body level (case.py:84-102) to work around circular dependencies. Other
circular imports are handled by deferred imports inside function bodies
(utils.py:456, env_batch.py:198). The `core/` reorganization should break
these cycles.

**Test infrastructure** — `conftest.py` requires a valid `srcroot` with
`cime_config/` directory and calls `Machines()` which requires machine config
XML. This means unit tests cannot run standalone without host model integration.
Fix by making conftest machine-aware only for system tests, not unit tests.

### Where DI / Protocols make sense
Use DI, protocols, and factory functions where CIME has **real polymorphism**
or **complex internal interfaces** worth decoupling:
- **Scheduler backends** (PBS, Slurm, LSF) — a `Scheduler` protocol with
  concrete implementations is natural here
- **XML config loading** — swappable loaders for testing without real config files
- **Components that cross subsystem boundaries** — e.g. build orchestration
  depending on a batch submitter interface

### What we DON'T do
- Don't wrap stdlib behind Protocol classes — `os.path.exists()` doesn't need
  a `FileSystem` abstraction; use `unittest.mock.patch` for testing
- Don't introduce DI frameworks or service locators
- Don't rewrite working code just to match a pattern
- Don't create abstractions without a concrete need (real polymorphism or
  testability problem that `mock.patch` can't solve cleanly)

### Testing
- Use `unittest.mock.patch` for mocking stdlib calls
- Use `tmp_path` / `tempfile` for filesystem tests
- Use `monkeypatch` for environment variables
- Protocols and constructor injection where the code genuinely benefits
  (e.g. testing submission logic without a real scheduler)

---

## Key Constraints

### Python 3.9+
All code must target Python 3.9 as the minimum supported version. Use
`typing.Protocol` (available since 3.8), `typing.Union`, `typing.Optional`, etc.
Do not use syntax that requires 3.10+ (e.g. `X | Y` union syntax,
`match`/`case` statements).

### Non-Installed Package
CIME is not installed via pip. Cases create symlinked tools that modify
`sys.path`. This must continue to work.

**Solution**: Centralized bootstrap in `CIME/core/config/bootstrap.py`

### Missing Package Structure
`CIME/Tools/xmlconvertors/` and `CIME/ParamGen/` lack `__init__.py` files
and use try/except import fallbacks. Fix during Slice 1.

### External Model Compatibility
E3SM, CESM, NorESM rely on CIME. Changes must not break their workflows.

**Validation**: Test representative workflows from each model after major changes.

### Stable Compatibility Surfaces
- `CIME/build_scripts/` — External script entrypoints
- Case-created symlinked tools
- Import paths (re-export from old locations during transition)

---

## Migration Slices

### Slice 1: Foundation (Weeks 1-3)
Typed exceptions, centralized bootstrap. Groundwork only.

### Slice 2: Batch (Weeks 4-7)
Move batch/submit logic from `case_submit.py` and XML classes into
`CIME/core/batch/`. Existing entrypoints become thin wrappers.

### Slice 3A: SRCROOT Standardization (Weeks 8-11) **NEW FEATURE**
Remove config_files.xml, standardize SRCROOT resolution, direct config loading.

### Slice 3B: Build (Weeks 12-16)
Move build logic from `build.py` into `CIME/core/build/`. Keep
`build_scripts/` as stable wrappers.

### Slice 4: Case (Weeks 17-22)
Decompose the `Case` god object (2600 lines). Phase 1: consolidate scattered
free functions (from `utils.py`, `build.py`, `status.py`, `locked_files.py`,
`case_run.py`) back into Case. Phase 2: extract subsystems (status, locking,
XML storage) into focused modules that Case delegates to. Case ends up smaller
than today with clear internal boundaries.

---

## Success Criteria

1. **Compatibility**: External models work without modification (or with documented migration)
2. **Testability**: 80%+ coverage for reorganized code
3. **Maintainability**: No module over ~500 lines; clear boundaries
4. **Documentation**: Updated docs for reorganized structure

---

## Validation Requirements

Each slice must pass:
- All existing CIME tests
- E3SM representative workflows
- CESM representative workflows
- NorESM representative workflows
- Performance benchmarks (no regression)

---

## Non-Goals

This refactor does NOT:
- Wrap stdlib in abstraction layers (`os.path`, `subprocess`, etc.)
- Introduce heavyweight DI frameworks or service locators
- Convert CIME to an installed package (yet)
- Rewrite working code for aesthetics
- Break Case API or build_scripts

DI, protocols, and factory functions ARE used where CIME has genuine
polymorphism (scheduler backends, config loaders, etc.).

---

## Documentation

- **This file (plan.md)**: Architecture and principles
- **implementation.md**: Detailed tasks and timeline
- **feature_srcroot.md**: SRCROOT standardization feature spec

---

## Questions?

File issues in CIME repository or discuss in development meetings.
