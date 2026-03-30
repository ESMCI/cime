# AGENTS.md

## Project specifics and jargon
- Model refers to an Earth System Model.
- CIME requires a model specific configuration.

## Dev environment tips
- Use `python -m venv` or `uv venv` to ceate local dev environment.
 - Use `python -m venv` or `uv venv` to create local dev environment.
- Setup doc environment with `pip install -r doc/requirements.txt`.
- Setup coding environment with `pip install -r test-requirements.txt`.
- Check if host is a supported machine by matching `hostname` to output of `./scripts/query_config --machines`.
- Test files prefixed with `test_unit` can be run locallly using `pytest --machine docker` in a venv.
 - Test files prefixed with `test_unit` can be run locally using `pytest --machine docker` in a venv.
- Test files prefixed with `test_sys` must be run on a supported machine or in the `ghcr.io/esmci/cime:latest` docker container. 
- Build documentation using `make -C doc/ html`.

## Repository Structure
Key paths:
- `CIME` - Project code directory
    - `SystemTests` - Model system tests, used to test specific model behavior and ensure reproducibility.
    - `Tools` - Various tools for working with CIME cases.
    - `XML` - The foundation of CIME, everything is configured through XML classes; prefixed `env` files are mutable case specific, all others are static model defined.
    - `baselines` - Used with system tests to verify reproducibility.
    - `build_scripts` - Scripts to build common libraries for models.
    - `case` - The heart of CIME, everything revolves around a case. Cases contain all information to configure, build, and run a model. System tests use cases to test specific behavior, some tests will create `n` cases and compare.
    - `data` - Stores model configuration entrypoints and general templates.
    - `non_py` - Stores common libraries that CIME provides.
    - `scripts` - Main entrypoints into CIME.
    - `bless_test_results.py` - Used to manage model testing baselines.
    - `config.py` - Used by models to configure CIME runtime.
    - `cs_status.py` - Used to write status files for cases.
    - `get_tests.py` - Used to define internal system tests for CIME.
    - `gitinterface.py` - Used to track case configuration using Git.
    - `locked_files.py` - Provides tooling to lock case configuration files.
    - `provenance.py` - Used to track case provenance.
    - `test_scheduler.py` - Used to run model system tests, automates case creation, configuration, build, and submit. Can process test suites, composed of many test cases.
    - `test_status.py` - Used to write test status for a case.
    - `user_mod_support.py` - Provides ability for users to modify cases in a consistent manner. Adjust model code, namelists, run shell scripts to configure components/model.
- `doc/source` - Documentation source directory
    - `ccs` - User Case Control System.
    - `tools` - User tools.
    - `api.rst` - Developer API.
    - `contributing-guide.rst` - Developer contribution guidelines.
    - `glossary.rst` - User glossary.
    - `system_testing.rst` - User System Testing reference.

## Coding Standards
- Follow `PEP8` style guide.
- Follow `Google Python Style Guide` for docstrings.
- Always prefer generalized implementation; avoid split logic that depends on a specific model.
- Always avoid external dependencies.
- Always run `pre-commit run <file_path>` after you create or modify a python file. Must pass before moving to next step.
- Always prefer dependency injection principles.

## Testing Standards
- Adds tests for new behavior - cover success, failure, and edge cases.
- Use pytest patterns, not `unittest.TestCase`.
- Use `@pytest.mark.parametrize` for multiple similar inputs.

## Documentation Standards
- Documentation written using Sphinx ReStructuredText.
- User documentation needs what/how.
- Developer documentation needs why/how.

## Commits and PRs
- Use Conventional Commits format.

## Boundaries
- Ask first
    - Adding external dependencies.
    - Large refactors.
- Never
    - Commit secrets, credentials, or tokens.
    - Use destructive git operations unless explicitly requested.
