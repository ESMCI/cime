# CIME Refactor Plan

Incremental refactor to improve dependency injection, resiliency, modularity, and testability while preserving compatibility with external models (E3SM, CESM, NorESM).

See also: `implementation.md` for detailed tasks, `feature_srcroot.md` for config loading changes.

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
├── api/              # Stable user-facing facades (Case, etc.)
├── cli/              # Optional thin CLI layer
├── core/             # Core implementation (DI-based)
│   ├── build/
│   ├── batch/
│   ├── config/       # Bootstrap, SRCROOT, config loading
│   ├── xml/
│   ├── status/
│   ├── locking/
│   └── ...
├── data/
├── build_scripts/    # Compatibility wrapper (stable)
├── SystemTests/
└── tests/
```

**Principle**: Internal evolution behind stable surfaces.

---

## Architecture Patterns

### Dependency Injection

**Strategy**: Lightweight DI via constructor injection, protocols, factory functions.

**Injectable boundaries**:
- Filesystem operations → `FileSystem` protocol
- Process execution → `ProcessRunner` protocol  
- Environment variables → `EnvironmentProvider` protocol
- Time operations → `Clock` protocol
- XML/config loading → Protocol-based

**Example**:
```python
class BuildOrchestrator:
    def __init__(self, filesystem: FileSystem, process: ProcessRunner):
        self._fs = filesystem  # Injected
        self._proc = process
        
def create_build_orchestrator() -> BuildOrchestrator:
    return BuildOrchestrator(get_filesystem(), get_process_runner())
```

### Resiliency

**Typed exceptions** replace broad fatal errors:
```python
class CIMEError(Exception): pass
class ConfigurationError(CIMEError): pass
class RetryableExternalCommandError(CIMEError): pass
```

**Explicit workflow states**: READY → VALIDATING → RUNNING → SUCCEEDED/FAILED

**Idempotency**: Lock/unlock, status updates, regeneration steps

### Error Handling

- Fail early with clear messages
- Retry policies for transient failures
- Graceful degradation where appropriate

---

## Key Constraints

### Non-Installed Package
CIME is not installed via pip. Cases create symlinked tools that modify `sys.path`. This must continue to work.

**Solution**: Centralized bootstrap in `CIME/core/config/bootstrap.py`

### External Model Compatibility
E3SM, CESM, NorESM rely on CIME. Changes must not break their workflows.

**Validation**: Test representative workflows from each model after major changes.

### Stable Compatibility Surfaces
- `CIME/api/` - User-facing classes
- `CIME/build_scripts/` - External script entrypoints
- Case-created symlinked tools
- Import paths (until coordinated migration)

---

## Migration Slices

### Slice 1: Foundation (Weeks 1-3)
Core abstractions: FileSystem, ProcessRunner, Environment, Clock, Exceptions, Bootstrap

### Slice 2: Batch (Weeks 4-7)
Extract batch/submit to `CIME/core/batch/`, scheduler abstractions

### Slice 3A: SRCROOT Standardization (Weeks 8-11) **NEW FEATURE**
Remove config_files.xml, standardize SRCROOT resolution, direct config loading

### Slice 3B: Build (Weeks 12-16)
Extract build to `CIME/core/build/`, keep `build_scripts` as wrapper

### Slice 4: Case (Weeks 17-22)
Extract Case internals (status, XML, locking) to focused components

---

## Success Criteria

1. **Compatibility**: External models work without modification (or with documented migration)
2. **Testability**: 80%+ coverage, isolated unit tests
3. **Resiliency**: Better error handling and recovery
4. **Maintainability**: Clear boundaries, reduced coupling
5. **Documentation**: Complete docs for new patterns

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

This refactor does NOT require:
- Immediate installed-package conversion
- Immediate CLI layer
- Removal of symlinked tools
- Wholesale rewrite in one step
- Breaking changes to Case API or build_scripts

---

## Documentation

- **This file (plan.md)**: Architecture and principles
- **implementation.md**: Detailed tasks and timeline
- **feature_srcroot.md**: SRCROOT standardization feature spec

---

## Questions?

File issues in CIME repository or discuss in development meetings.
