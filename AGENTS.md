# AGENTS.md

This file provides guidance to AI agents when working with code in this repository.

## Project Overview

CIME (Common Infrastructure for Modeling the Earth) provides a Case Control System (CCS) for configuring, compiling, and executing Earth System Models, plus a framework for system testing. CIME is a Python-based infrastructure currently used by CESM, E3SM and NorESM. It does NOT contain model source code itself, but provides the infrastructure to manage model runs.

## Running Tests

### Unit and System Tests

From the repository root, run tests using either:

```bash
# Using pytest (recommended)
pytest CIME/tests

# Using the custom test runner
cd CIME/tests
./scripts_regression_tests.py

# Run specific test file
pytest CIME/tests/test_unit_foo.py

# Run specific test class
pytest CIME/tests/test_unit_foo.py::TestClass

# Run specific test case
pytest CIME/tests/test_unit_foo.py::TestClass::test_method
```

Test files follow a naming convention:
- Unit tests: `test_unit_*.py`
- System tests: `test_sys_*.py`

### Pre-commit Hooks

Before committing, always run:

```bash
pip install pre-commit
pre-commit run -a
```

This runs:
- `black` formatter on CIME code
- `pylint` with project-specific configuration
- XML validation on config files
- End-of-file and trailing whitespace checks

## Code Quality

- Code is formatted with `black`
- Linted with `pylint` (see `.pre-commit-config.yaml` for disabled checks)
- Python 3.9+ required
- Follow PEP8 style guidelines

## Key Architecture Concepts

### Case Control System (CCS)

The heart of CIME is the `Case` class (`CIME/case/case.py`), which manages all interactions with a CIME case. The Case class coordinates between:

1. **Config XML Classes** (readonly) - Located in `CIME/XML/`, these read CIME distribution config files like `config_*.xml`. Python classes are named after the XML they read (e.g., `Machines` reads machine configs).

2. **Env XML Classes** (read/write) - Also in `CIME/XML/`, these manage case-specific `env_*.xml` files. Classes are named `Env*` (e.g., `EnvRun`, `EnvBuild`).

The Case class contains an array of Env classes and uses Config classes to populate them during case creation/configuration.

### Directory Structure

```
CIME/
├── case/              # Case control modules (setup, run, submit, etc.)
├── XML/               # XML parsers for config and env files
├── SystemTests/       # System test implementations (ERS, ERT, etc.)
├── Tools/             # Case manipulation tools (xmlchange, xmlquery, etc.)
├── scripts/           # Top-level user-facing scripts
├── data/              # Config files, XML schemas
├── tests/             # Unit and system tests
├── BuildTools/        # Build system utilities
└── non_py/            # Non-Python components (C/Fortran)

scripts/
├── create_newcase     # Create new case
├── create_test        # Create and run tests
├── create_clone       # Clone existing case
├── query_config       # Query available configurations
└── query_testlists    # Query test lists

tools/
└── mapping/           # Grid mapping file generation tools
```

### Common Workflows

**Create a case** (requires machine configuration):
```bash
./scripts/create_newcase --case CASENAME --compset COMPSET --res GRID [--machine MACHINE]
```

**Create and run tests**:
```bash
./scripts/create_test TESTNAME
./scripts/create_test TESTNAME1 TESTNAME2 ...
./scripts/create_test -f TESTFILE  # from file
```

**Query configurations**:
```bash
./scripts/query_config --compsets
./scripts/query_config --grids
./scripts/query_config --machines
```

### System Tests

System tests inherit from `SystemTestsCommon` base class (`CIME/SystemTests/system_tests_common.py`). Common test types:
- **ERS**: Exact restart test
- **ERT**: Exact restart with different threading
- **SMS**: Smoke test
- **SEQ**: Sequencing test

Each test type has its own module in `CIME/SystemTests/`.

### XML-Based Configuration

CIME is heavily XML-driven. Key concepts:
- Generic XML handling is in `CIME/XML/generic_xml.py`
- All XML classes inherit from `GenericXML`
- XML schemas are in `CIME/data/config/xml_schemas/`
- Config files define machines, compsets, grids, tests

### Case Management Tools

Located in `CIME/Tools/`, these are executable scripts:
- `xmlchange`: Modify case XML variables
- `xmlquery`: Query case XML variables
- `case.setup`: Setup case directory structure
- `case.build`: Build the case
- `case.submit`: Submit case to batch system
- `preview_namelists`: Generate and preview namelists

## Documentation

Build Sphinx documentation:
```bash
cd doc
make clean
make api
make html
```

Requires: `sphinx`, `sphinxcontrib-programoutput`, and custom theme (see `doc/README`).

Online documentation: https://esmci.github.io/cime

## Development Notes

- When modifying Case env classes, changes affect the case's XML files
- The Case class extends across multiple files using imports (see imports at end of `case.py`)
- CIME must be integrated with host models (CESM, E3SM, NorESM) to run system tests and must be
on a supported machine (found using `./scripts/query_config --machines`)/
- Machine-specific configurations are in XML files, not hardcoded
- Git submodules may need initialization: `git submodule update --init`
