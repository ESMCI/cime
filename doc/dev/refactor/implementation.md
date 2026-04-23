# Implementation Plan

Detailed tasks for the CIME refactor. See `plan.md` for architecture and principles.

## Timeline: 22-24 weeks (5 slices)

| Slice | Weeks | Focus |
|-------|-------|-------|
| 1. Foundation | 1-3 | Core abstractions |
| 2. Batch | 4-7 | Scheduler/submit |
| 3A. SRCROOT | 8-11 | Config loading (NEW) |
| 3B. Build | 12-16 | Build system |
| 4. Case | 17-22 | Case refactor |

---

## Slice 1: Foundation (Weeks 1-3)

**Goal**: Core abstractions with DI, no behavior changes.

### Tasks
- `CIME/core/config/bootstrap.py` - Centralized sys.path management
- `CIME/core/exceptions.py` - Typed exception hierarchy
- `CIME/core/filesystem.py` - FileSystem protocol + RealFileSystem
- `CIME/core/process.py` - ProcessRunner protocol + RealProcessRunner
- `CIME/core/environment.py` - EnvironmentProvider protocol
- `CIME/core/clock.py` - Clock protocol

### Patterns
**All use constructor injection**:
```python
class BatchSubmitter:
    def __init__(self, filesystem: FileSystem, process: ProcessRunner):
        self._fs = filesystem  # Injected, not imported
        self._proc = process

def create_batch_submitter() -> BatchSubmitter:
    return BatchSubmitter(get_filesystem(), get_process_runner())
```

### Success
- 80%+ test coverage
- All existing tests pass
- No external API changes

---

## Slice 2: Batch System (Weeks 4-7)

**Goal**: Extract batch logic to `CIME/core/batch/`.

### Tasks
- `CIME/core/batch/scheduler.py` - Scheduler protocol (PBS, Slurm, LSF)
- `CIME/core/batch/submitter.py` - Job submitter with DI
- Keep existing batch entrypoints as wrappers

### Pattern
```python
class JobSubmitter:
    def __init__(self, scheduler: Scheduler, filesystem: FileSystem):
        self._scheduler = scheduler
        self._fs = filesystem
```

### Success
- All batch tests pass
- External models submit jobs unchanged

---

## Slice 3A: SRCROOT Standardization (Weeks 8-11) **NEW**

**Goal**: Remove config_files.xml, standardize SRCROOT.

See `feature_srcroot.md` for details.

### Tasks
- `CIME/core/config/srcroot.py` - SRCROOTResolver with DI
- `CIME/core/config/loader.py` - ConfigFileLoader with DI
- Add `--srcroot` flag to CLI tools
- Refactor `CIME/XML/files.py` with feature flag
- 4-stage migration (opt-in → opt-out → deprecate → remove)

### Success
- Works with E3SM, CESM, NorESM
- Standalone mode for unit tests
- config_files.xml deprecated

---

## Slice 3B: Build System (Weeks 12-16)

**Goal**: Extract build logic to `CIME/core/build/`.

### Tasks
- `CIME/core/build/planner.py` - Build planning
- `CIME/core/build/orchestrator.py` - Build execution
- Keep `CIME/build_scripts/` as stable wrappers

### Pattern
```python
class BuildOrchestrator:
    def __init__(self, filesystem: FileSystem, process: ProcessRunner):
        self._fs = filesystem
        self._proc = process
```

### Success
- All build tests pass
- `build_scripts` compatibility maintained
- External models build unchanged

---

## Slice 4: Case Refactoring (Weeks 17-22)

**Goal**: Extract Case internals to focused components.

### Tasks
- `CIME/core/status/` - Status tracking
- `CIME/core/xml/` - XML storage
- `CIME/core/locking/` - Lock management
- Case class becomes facade

### Pattern
```python
class Case:
    def __init__(self):
        self._status = create_status_tracker()
        self._xml_store = create_xml_store()
        
    def set_value(self, vid, value):
        # Delegate to xml store
        self._xml_store.set_value(self._caseroot, vid, value)
```

### Success
- Case API unchanged
- Internal complexity reduced
- Better testability

---

## DI Guidelines

### Constructor Injection
```python
# Good
class StatusTracker:
    def __init__(self, filesystem: FileSystem):
        self._fs = filesystem

# Bad
class StatusTracker:
    def do_thing(self):
        import os
        os.path.exists(...)  # Direct global access
```

### Factory Functions
```python
def create_status_tracker(filesystem: Optional[FileSystem] = None) -> StatusTracker:
    if filesystem is None:
        filesystem = get_filesystem()  # Default for production
    return StatusTracker(filesystem)  # Tests inject mocks
```

### Protocol Interfaces
```python
class FileSystem(Protocol):
    def exists(self, path: Path) -> bool: ...
```

---

## Testing Strategy

### Unit Tests (80%+ coverage)
- Mock all injected dependencies
- No global state manipulation
- Fast, isolated tests

```python
def test_status_tracker():
    mock_fs = MockFileSystem(existing_files={...})
    tracker = StatusTracker(mock_fs)
    result = tracker.get_status()
    assert result == expected
```

### Integration Tests
- Key workflows end-to-end
- Real dependencies where needed

### Compatibility Tests
- E3SM, CESM, NorESM workflows
- Case creation, build, submit
- Validate each slice

---

## Success Metrics

- **Compatibility**: 100% external tests pass
- **Coverage**: 80%+ for new code
- **Performance**: No regression (within 5%)
- **Maintainability**: Reduced coupling, clear boundaries

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
- [ ] Constructor injection (no direct imports in business logic)
- [ ] Factory functions provide defaults
- [ ] Tests use mocked dependencies
- [ ] No global state in core classes
- [ ] 80%+ test coverage
- [ ] All existing tests pass
- [ ] Documentation updated
