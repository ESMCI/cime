# Implementation Plan

Detailed tasks for the CIME refactor. See `plan.md` for architecture and principles.

**Key rule: move existing code, don't rewrite it.** Extract functions into
focused modules. Only refactor when a module is too large or too tangled to
move as-is.

**Target: Python 3.9+.** Do not use 3.10+ syntax (`X | Y` unions,
`match`/`case`). Use `typing.Union`, `typing.Optional`, etc.

**Migration pattern**: Move code to `CIME/core/`, then make the original
module import from `CIME/core/` and re-export. See `plan.md` "Migration
Pattern" for details and examples.

## Timeline: 22-24 weeks (5 slices)

| Slice | Weeks | Focus |
|-------|-------|-------|
| 1. Foundation | 1-3 | Exceptions, bootstrap |
| 2. Batch | 4-7 | Scheduler/submit |
| 3A. SRCROOT | 8-11 | Config loading (NEW) |
| 3B. Build | 12-16 | Build system |
| 4. Case | 17-22 | Case refactor |

---

## Handling `utils.py` (2700 lines, 104 functions)

`utils.py` is the largest module and doesn't belong to any single slice.
It contains functions across every category:

| Category | Count | Examples |
|----------|-------|---------|
| General utilities | 57 | `run_cmd`, `safe_copy`, logging, time conversion |
| SRCROOT/config | 19 | `get_cime_root`, `get_src_root`, `get_model` |
| Foundation | 9 | `CIMEError`, `expect`, `fixup_sys_path` |
| Case | 9 | `parse_test_name`, `wait_for_unlocked` |
| Batch | 7 | `batch_jobid`, `get_project`, `transform_vars` |
| Build | 3 | `analyze_build_log`, `copy_local_macros_to_dir` |

**Strategy**: Each slice moves its own functions **plus the general utilities
those functions depend on**. As general utils get pulled into `core/`, they
land in focused modules:

- `CIME/core/shell.py` — `run_cmd`, `run_cmd_no_fail` (pulled by Slice 2/Batch)
- `CIME/core/logging.py` — logging setup, formatters (pulled by Slice 1)
- `CIME/core/time.py` — time conversion helpers (pulled by Slice 4/Case)
- `CIME/core/fileops.py` — `safe_copy`, `symlink_force`, `find_files` (pulled as needed)
- `CIME/core/convert.py` — type conversion helpers (pulled as needed)

By the end of Slice 4, `utils.py` should be a thin re-export file with no
implementation code of its own.

---

## Slice 1: Foundation (Weeks 1-3)

**Goal**: Typed exceptions, centralized bootstrap, and eliminate the worst
cross-cutting code smells. No behavior changes.

### Tasks
- `CIME/core/exceptions.py` — Typed exception hierarchy extending existing `CIMEError`.
  **Important**: `CIMEError` currently lives in `utils.py:155` — move it to
  `core/exceptions.py` and re-export from `utils.py`. The typed subclasses
  (`ConfigurationError`, `BuildError`, etc.) won't have callers yet but
  establish the hierarchy for later slices.
- `CIME/core/config/bootstrap.py` — Centralized `sys.path` management (consolidates
  the `sys.path.insert` calls currently scattered across 11+ files, plus the
  duplicate logic in `standard_script_setup.py` and `standard_module_setup.py`)
- Move from `utils.py`: `CIMEError`, `expect`, `deprecate_action`,
  `fixup_sys_path`, `import_from_file`, `import_and_run_sub_or_cmd`,
  `run_sub_or_cmd`, and their helpers
- Move logging infrastructure from `utils.py` → `CIME/core/logging.py`
  (`IndentFormatter`, `set_logger_indent`, `configure_logging`,
  `setup_standard_logging_options`, etc.)
- Migrate `sys.path` call-sites incrementally to use bootstrap module
- Update internal CIME imports; leave re-exports in `utils.py`
- **Eliminate star imports from `standard_module_setup`** — this single
  `from CIME.XML.standard_module_setup import *` appears in ~60 files,
  polluting every module's namespace with `os`, `sys`, `re`, `expect`,
  `run_cmd`, etc. Replace with explicit imports in each file. This is the
  highest-impact code quality fix in the entire refactor.
- **Eliminate star imports from `test_status`** — `from CIME.test_status import *`
  appears in ~10 files, exporting ~30 constants. Replace with explicit imports.
- **Remove `GLOBAL = {}` mutable state** from `utils.py:21` — this dict is used
  to pass `SRCROOT` between `case.py`, `create_test.py`, and `utils.get_src_root()`
  via implicit global mutation. Replace with explicit parameter passing.
- **Fix `Servers/__init__.py`** — runs `shutil.which()` at import time for
  `globus-url-copy`, `svn`, `wget`, making package import non-deterministic.
  Make discovery lazy.
- Standardize error handling: audit `sys.exit()` calls (6 sites) and bare
  `raise RuntimeError` (~30 sites) and migrate to `CIMEError` / `expect()`
  where appropriate
- **Fix `conftest.py`** — currently requires host model config and machine XML
  to run any tests. Split so unit tests (`test_unit_*.py`) can run standalone
  without machine initialization; keep machine setup for system tests only.
- **Fix circular imports** in Case — `case.py:84-102` injects methods from
  10 sibling modules at class body level. The move to `core/` modules should
  start breaking these cycles.

### What we're NOT doing in Slice 1
- No Protocol classes wrapping stdlib (`os.path`, `subprocess`, `time`, `os.environ`)
- No factory functions or service locators
- No new abstraction layers

### Success
- All existing tests pass
- Zero star imports from `standard_module_setup` and `test_status`
- `GLOBAL = {}` eliminated; SRCROOT passed explicitly
- `sys.path` manipulation consolidated
- Consistent error handling (no bare `sys.exit()` in library code)
- `Servers/__init__.py` no longer runs executables at import time
- Unit tests (`test_unit_*.py`) run without host model / machine config
- Exception hierarchy in place for later slices to use

---

## Slice 2: Batch System (Weeks 4-7)

**Goal**: Move batch logic from scattered locations into `CIME/core/batch/`.

### Tasks
- Move scheduler-specific logic from XML classes into `CIME/core/batch/`
- Move submission logic from `case_submit.py` internals
- Move from `utils.py`: `batch_jobid`, `get_batch_script_for_job`,
  `get_project`, `get_charge_account`, `add_mail_type_args`,
  `resolve_mail_type_args`, `transform_vars`
- Move `run_cmd`, `run_cmd_no_fail` from `utils.py` → `CIME/core/shell.py`
  (general utility, pulled here because batch is the first heavy consumer)
- A `Scheduler` protocol is appropriate here — PBS, Slurm, and LSF are genuine
  polymorphic backends worth abstracting behind a common interface
- Keep existing entrypoints as thin wrappers calling into new location
- Update internal CIME imports; leave re-exports in old locations

### Consolidation
- `transform_vars` (utils.py:2118) takes `case` and calls `case.get_value()`
  repeatedly — consolidate as a `Case` method, with the core template logic
  in `CIME/core/batch/`
- `batch_jobid` (utils.py:2360) calls `case.get_job_id()` — consolidate into
  the batch subsystem
- **`EnvBatch`** (XML/env_batch.py, 1590 lines, 43 methods) — this is the
  second-largest class in CIME. It handles batch config parsing, job submission,
  queue management, and directive generation all in one class. Decompose into:
  - `CIME/core/batch/config.py` — batch config/queue parsing (from EnvBatch)
  - `CIME/core/batch/submit.py` — job submission logic (from EnvBatch + case_submit.py)
  - `CIME/core/batch/directives.py` — directive generation (from EnvBatch)
  - `EnvBatch` becomes a thinner wrapper that delegates to these modules

### Success
- All batch tests pass
- External models submit jobs unchanged
- Batch logic in one place instead of spread across XML/ and case/

---

## Slice 3A: SRCROOT Standardization (Weeks 8-11) **NEW**

**Goal**: Remove config_files.xml, standardize SRCROOT.

See `feature_srcroot.md` for details.

### Tasks
- `CIME/core/config/srcroot.py` — SRCROOT resolution logic
- `CIME/core/config/loader.py` — Config file loading
- Move from `utils.py`: `get_cime_root`, `get_src_root`, `get_model`,
  `set_model`, `get_cime_config`, `get_config_path`, `get_schema_path`,
  `get_template_path`, `get_tools_path`, `get_cime_default_driver`,
  `get_all_cime_models`, `get_model_config_location_within_cime`,
  `get_scripts_root`, `get_model_config_root`, `get_htmlroot`, `get_urlroot`,
  and their helpers
- Add `--srcroot` flag to CLI tools
- Refactor `CIME/XML/files.py` with feature flag
- 4-stage migration (opt-in → opt-out → deprecate → remove)
- Update internal CIME imports; leave re-exports in `utils.py`

### Success
- Works with E3SM, CESM, NorESM
- Standalone mode for unit tests
- config_files.xml deprecated

---

## Slice 3B: Build System (Weeks 12-16)

**Goal**: Move build logic from `build.py` (1350 lines) into focused modules.

### Tasks
- Extract build planning logic into `CIME/core/build/`
- Extract build execution/orchestration
- Move from `utils.py`: `analyze_build_log`, `run_bld_cmd_ensure_logging`,
  `copy_local_macros_to_dir`
- Move file operation helpers from `utils.py` → `CIME/core/fileops.py`
  (`safe_copy`, `safe_recursive_copy`, `symlink_force`, `copy_globs`,
  `copy_over_file`, `copyifnewer` — pulled here because build is a heavy consumer)
- Keep `CIME/build_scripts/` as stable wrappers
- `build.py` becomes thin re-export layer
- Update internal CIME imports; leave re-exports in old locations

### Consolidation
- `case_build()`, `clean()`, `_clean_impl()`, `post_build()` (build.py)
  all take `case`, access `case._gitinterface` (private!), call
  `case.get_value()` / `case.set_value()` / `case.flush()` — these should
  become `Case` methods that delegate to `CIME/core/build/`
- `get_standard_cmake_args()`, `get_standard_makefile_args()`, `uses_kokkos()`
  (build.py) extract ~15 values from Case — consolidate as Case methods or a
  `BuildConfig` data class populated from Case
- `generate_makefile_macro()` (build.py) calls `case.get_value()` — same pattern
- Deduplicate the four copy functions in `utils.py` (`safe_copy`,
  `copy_over_file`, `copyifnewer`, `copy_globs`) into a coherent
  `CIME/core/fileops.py` API

### Success
- All build tests pass
- `build_scripts` compatibility maintained
- External models build unchanged

---

## Slice 4: Case Refactoring (Weeks 17-22)

**Goal**: Decompose the `Case` class into focused subsystems while
consolidating scattered Case-related functions.

### Why Case needs refactoring

`Case` (`case.py`, 2600 lines) is a god object. It directly handles:
- XML value get/set across multiple env files
- Status tracking (CaseStatus file)
- Lock management (LockedFiles directory)
- Build orchestration
- Job submission
- Namelist generation
- Clone/setup/test workflows

On top of that, many Case operations live *outside* the class as free
functions in `utils.py`, `build.py`, `status.py`, `locked_files.py`, and
`case_run.py` — functions that take `case` as a parameter and reach into
its internals (including private attributes like `case._gitinterface`).

The result: Case responsibility is smeared across ~10 files with no clear
boundaries, and the class itself is too large to reason about or test in
isolation.

### Two-phase approach

**Phase 1 — Consolidate into Case**: Bring the scattered free functions
back into Case (or into subsystem classes that Case owns). This *temporarily*
makes Case bigger, but it gathers all the responsibility in one place so we
can see the seams clearly.

**Phase 2 — Extract subsystems out of Case**: Once the responsibility is
consolidated, decompose Case into focused subsystem modules that Case
delegates to. Case becomes a thinner coordinator/facade.

The end result is a Case that's smaller than today, with clear delegation
to subsystems that are independently testable.

### Phase 1 tasks — Consolidate

Bring free functions into Case (or subsystem classes Case will delegate to):

- **Status** (from `status.py`): `append_case_status()`,
  `run_and_log_case_status()` — every caller extracts `caseroot` and
  `case._gitinterface` just to pass them in
- **Locking** (from `locked_files.py`): `check_lockedfiles()`,
  `check_lockedfile()`, `diff_lockedfile()`, `check_diff()` — pure Case
  integrity checks deeply coupled to Case env XML subsystem
- **Case queries** (from `utils.py`): `is_comp_standalone()`,
  `find_system_test()`, `get_lids()`, `new_lid()` — predicates and queries
  on Case state
- **Case run helpers** (from `case/case_run.py`): `_pre_run_check()`,
  `_run_model_impl()`, `_post_run_check()`, `_resubmit_check()` — free
  functions that take `case`; make them methods
- **TestScheduler** (from `test_scheduler.py`): `_get_time_est()`,
  `_order_tests_by_runtime()`, `_translate_test_names_for_new_pecount()` —
  module-level helpers with `_TIME_CACHE` that should be instance state

### Phase 2 tasks — Extract subsystems

Decompose Case into focused modules it delegates to:

- `CIME/core/status/` — status tracking (CaseStatus file, `append_status`,
  `run_and_log_status`)
- `CIME/core/locking/` — lock management (LockedFiles, `check_locked`,
  `diff_locked`)
- `CIME/core/xml/` — XML value storage (env file get/set/flush, the
  `_env_entryid_files` and `_env_generic_files` arrays)

Case keeps its public API (`get_value`, `set_value`, `build`, `submit`, etc.)
but each method delegates to the appropriate subsystem:

```python
# After refactoring — Case delegates, doesn't implement
class Case:
    def __init__(self, ...):
        self._status = StatusTracker(self._caseroot, self._gitinterface)
        self._locks = LockManager(self._caseroot)
        self._xml = XmlStore(self._env_files)

    def append_status(self, msg, ...):
        self._status.append(msg, ...)

    def check_lockedfiles(self):
        self._locks.check(self._xml)
```

### Other Slice 4 tasks
- Move from `utils.py`: `wait_for_unlocked`, `normalize_case_id`,
  `parse_test_name`, `get_full_test_name`, `compute_total_time`
- Move remaining general utils from `utils.py`:
  - `CIME/core/time.py` — time conversion (`convert_to_seconds`,
    `convert_to_babylonian_time`, `get_time_in_seconds`, `format_time`)
  - `CIME/core/convert.py` — type conversion (`convert_to_type`,
    `convert_to_unknown_type`, `convert_to_string`, `stringify_bool`)
- `utils.py` should be a thin re-export file by end of Slice 4
- Update all internal CIME imports

### Other large modules to decompose in Slice 4

- **`case/case_st_archive.py`** (1395 lines, ~20 free functions taking `case`)
  — largest procedural module; consolidate functions as Case methods or
  extract into `CIME/core/archive/`
- **`case/check_input_data.py`** (693 lines, ~12 free functions taking `case`)
  — consolidate into Case or a focused input-data module
- **`baselines/performance.py`** (612 lines, ~12 free functions taking `case`)
  — consolidate into a baseline comparison subsystem
- **`hist_utils.py`** (836 lines, ~7 free functions taking `case`)
  — history file handling, consolidate into appropriate subsystem
- **`TestScheduler`** (test_scheduler.py, 1340 lines, 28 methods) — mixes
  test creation, phase management, job submission, and result processing;
  decompose into focused components

### Success
- Case API unchanged from external perspective
- Internal modules are independently testable
- No single module over ~500 lines

---

## Testing Strategy

### Standard mocking for stdlib
```python
# Good: use unittest.mock for stdlib calls
from unittest.mock import patch

def test_build_checks_file():
    with patch("os.path.exists", return_value=True):
        result = check_build_prereqs("/some/path")
    assert result is True

# Good: use tmp_path for filesystem tests
def test_writes_status(tmp_path):
    tracker = StatusTracker(str(tmp_path))
    tracker.set_status("BUILT")
    assert (tmp_path / "CaseStatus").read_text() == "BUILT"

# Good: use monkeypatch for env vars
def test_reads_cimeroot(monkeypatch):
    monkeypatch.setenv("CIMEROOT", "/my/cime")
    assert find_cimeroot() == "/my/cime"
```

### DI / Protocols where they earn their keep
```python
# Good: Scheduler is genuinely polymorphic — PBS, Slurm, LSF are
# different backends behind a common interface
class Scheduler(Protocol):
    def submit(self, job: Job) -> str: ...
    def poll(self, job_id: str) -> JobStatus: ...

def test_submission_retries():
    fake = FakeScheduler(fail_first=2)
    submitter = JobSubmitter(scheduler=fake)
    result = submitter.submit_with_retry(job, max_retries=3)
    assert result.success
```

**Rule of thumb**: if the variation is in *CIME's own code* (scheduler types,
config loaders, model components), a protocol may be warranted. If you're just
calling `os.path` or `subprocess`, use `mock.patch`.

### Coverage
- 80%+ for reorganized code
- Existing tests must continue to pass

### Integration/Compatibility Tests
- Key workflows end-to-end
- E3SM, CESM, NorESM representative workflows
- Validate each slice

---

## Success Metrics

- **Compatibility**: 100% external tests pass
- **Coverage**: 80%+ for reorganized code
- **Performance**: No regression (within 5%)
- **Maintainability**: No module over ~500 lines, clear boundaries

---

## Risk Management

**High-Risk Areas**:
1. SRCROOT standardization (breaking change)
2. config_files.xml removal (migration required)
3. Case refactoring (high external usage)

**Mitigation**:
- Feature flags for transitions
- Multi-stage rollout
- Comprehensive external model testing
- Rollback plans per slice

---

## Code Review Checklist

For each PR, verify:
- [ ] Existing code moved, not rewritten (unless refactoring complexity)
- [ ] Free functions that take an object consolidated as methods where appropriate
- [ ] Internal CIME imports updated to point to new `CIME/core/` location
- [ ] Old import paths still work via re-exports (for external consumers)
- [ ] Tests use standard mocking (`unittest.mock`, `monkeypatch`, `tmp_path`)
- [ ] DI/protocols used only for real CIME polymorphism, not stdlib wrapping
- [ ] No unnecessary abstraction layers
- [ ] 80%+ test coverage for moved/new code
- [ ] All existing tests pass
- [ ] Documentation updated
