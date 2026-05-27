# CIME Refactor Documentation

Documentation for the CIME refactoring effort.

## Quick Start

- **New to refactor?** Read `plan.md`
- **Implementing a slice?** See `implementation.md`
- **Working on SRCROOT feature?** See `feature_srcroot.md`
- **Working on single entrypoint?** See `feature_single_entrypoint.md`

## Documents

### [plan.md](plan.md)
Architecture, principles, and migration strategy.
- Compatibility-first policy
- Reorganize-don't-rewrite approach
- 5 implementation slices
- Success criteria

### [implementation.md](implementation.md)
Detailed tasks, timeline, and testing approach.
- Slice-by-slice breakdown
- Standard mocking strategy (no custom DI)
- Code review checklist

### [feature_srcroot.md](feature_srcroot.md)
SRCROOT standardization feature (Slice 3A).
- Removes config_files.xml indirection
- Migration plan

### [feature_single_entrypoint.md](feature_single_entrypoint.md)
Single CIME entrypoint feature.
- Replaces ~20 symlinks with one
- Shell wrappers for tool compatibility
- Can run parallel with other slices

## Overview

**Goal**: Improve CIME's modularity, error handling, and testability while
maintaining compatibility with E3SM, CESM, and NorESM.

**Timeline**: 22-24 weeks (5 slices)

**Approach**: Move existing code into focused modules. Consolidate scattered
functions back into the classes that own them. Don't rewrite working code or
wrap stdlib behind abstraction layers.

## Implementation Slices

1. **Foundation** (3 weeks): Typed exceptions, centralized bootstrap
2. **Batch** (4 weeks): Move batch/submit logic to `CIME/core/batch/`
3. **SRCROOT** (4 weeks): Standardize config loading (NEW FEATURE)
4. **Build** (5 weeks): Move build logic to `CIME/core/build/`
5. **Case** (6 weeks): Consolidate scattered Case functions, then decompose
   into focused subsystems (status, locking, XML storage)

## Key Principles

- **Compatibility first**: External models must continue working
- **Reorganize, don't rewrite**: Move code to better homes
- **DI where it earns its keep**: Protocols and constructor injection for real
  CIME polymorphism (scheduler backends, config loaders); `mock.patch` for stdlib
- **Incremental**: Each slice independently testable
- **Test-driven**: 80%+ coverage for reorganized code

## For Developers

**Before coding**:
1. Read relevant slice in `implementation.md`
2. Understand the reorganize-don't-rewrite principle in `plan.md`

**During development**:
- Move existing functions, don't rewrite them
- Add re-exports from old import paths
- Write tests with `unittest.mock`, `monkeypatch`, `tmp_path`
- Use DI/protocols for real CIME interfaces, not stdlib wrapping
- Maintain backward compatibility

**Code review checklist**:
- [ ] Code moved, not rewritten (unless simplifying complexity)
- [ ] Free functions that take an object consolidated as methods where appropriate
- [ ] Internal CIME imports updated to `CIME/core/`
- [ ] Old import paths still work via re-exports (for downstream models)
- [ ] Standard mocking for stdlib; DI/protocols for CIME interfaces
- [ ] No unnecessary abstraction layers
- [ ] 80%+ test coverage
- [ ] All tests pass
- [ ] Docs updated

## For Downstream Models

**E3SM, CESM, NorESM integrators**:
- Each slice maintains compatibility
- Old import paths continue to work via re-exports
- SRCROOT feature (Slice 3A) has migration guide
- Test during opt-in periods
- Provide feedback early

## Questions?

File issues in CIME repository or discuss in development meetings.
