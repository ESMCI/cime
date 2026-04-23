# CIME Refactor Documentation

Comprehensive documentation for the CIME refactoring effort.

## Quick Start

- **New to refactor?** Read `plan.md`
- **Implementing a slice?** See `implementation.md`
- **Working on SRCROOT feature?** See `feature_srcroot.md`
- **Working on single entrypoint?** See `feature_single_entrypoint.md`

## Documents

### [plan.md](plan.md)
Architecture, principles, and migration strategy.
- Compatibility-first policy
- Package structure and DI patterns
- 5 implementation slices
- Success criteria

### [implementation.md](implementation.md)
Detailed tasks, code patterns, and timeline.
- Week-by-week breakdown
- Code examples for each slice
- Testing strategy
- Code review checklist

### [feature_srcroot.md](feature_srcroot.md)
SRCROOT standardization feature (Slice 3A).
- Removes config_files.xml indirection
- DI-compliant implementation
- Migration plan
- Testing with mocks

### [feature_single_entrypoint.md](feature_single_entrypoint.md)
Single CIME entrypoint feature.
- Replaces ~20 symlinks with one
- Shell wrappers for tool compatibility
- Simplifies CIME version switching
- Can run parallel with other slices

## Overview

**Goal**: Improve CIME's dependency injection, resiliency, and testability while maintaining compatibility with E3SM, CESM, and NorESM.

**Timeline**: 22-24 weeks (5 slices)

**Approach**: Incremental refactor with compatibility preserved at each step.

## Implementation Slices

1. **Foundation** (3 weeks): Core abstractions (FileSystem, ProcessRunner, etc.)
2. **Batch** (4 weeks): Extract batch/submit logic
3. **SRCROOT** (4 weeks): Standardize config loading (NEW FEATURE)
4. **Build** (5 weeks): Extract build logic
5. **Case** (6 weeks): Extract Case internals to focused components

## Key Principles

- **Compatibility first**: External models must continue working
- **Constructor injection**: All dependencies injected, no globals
- **Incremental**: Each slice independently testable
- **Test-driven**: 80%+ coverage requirement

## For Developers

**Before coding**:
1. Read relevant slice in `implementation.md`
2. Understand DI patterns in `plan.md`
3. Review code examples

**During development**:
- Use constructor injection
- Write tests with mocks
- Maintain backward compatibility
- Update documentation

**Code review checklist**:
- [ ] Constructor injection used
- [ ] No direct filesystem/process/env access in core classes
- [ ] Factory functions provide defaults
- [ ] 80%+ test coverage
- [ ] All tests pass
- [ ] Docs updated

## For Downstream Models

**E3SM, CESM, NorESM integrators**:
- Each slice maintains compatibility
- SRCROOT feature (Slice 3A) has migration guide
- Test during opt-in periods
- Provide feedback early

## Questions?

File issues in CIME repository or discuss in development meetings.
