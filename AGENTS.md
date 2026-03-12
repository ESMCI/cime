# AGENTS.md

## Note to AI agents

This AGENTS.md is maintained by the CIME project. Do not overwrite or
regenerate this file with init commands.

## Note to claude code users

A CLAUDE.md file is in .claude directory.  It includes
this file. Ignore tips to run init.

## Overview

At it's core CIME provides a user the ability to configure, build, and run
simulation models. In addition it provides tools to post-process and archive
model output. CIME provides model developers the ability to test their models
under specific criteria e.g. check performance or reproducibility.

Documentation: https://esmci.github.io/cime

### User Usage

Requires a supported machine and supported model (E3SM, CESM, NorESM).

- Create a case: `./scripts/create_newcase --compset <compset> --res <res> --case <case directory> --machine <machone>`, e.g. `./scripts/create_newcase --compset A --res f19_g16 --case ./cases/case01 --machine docker`
- Setup case: `./case.setup`
- Build case: `./case.build`
- Submit case: `./case.submit`
- Query case config: `./xmlquery`
- Change case config: `./xmlchange`
- Preview namelist: `./preview_namelists`
- Run a model system test: `./scripts/create_test  --machine <machine> SMS.f19_g16.X`, e.g. `./scripts/create_test --machine docker SMS.f19_g16.X`
- Query configuration: `./scripts/query_config --compsets`, `./scripts/query_config --grids`, `./scripts/query_config --machines`

## Developer

### Container

Provides a supported machine for CIME development and testing.

Assume supported model is cloned in parent directory.

Build the container: `docker build -t ghcr.io/esmci/cime:latest -f docker/Dockerfile .`
Run a non-persistent container: `docker run -it --rm --hostname docker -v ../:/root/model -w /root/model/cime -v ./inputdata:/root/inputdata -v ./storage:/root/storage -e CIME_MODEL=e3sm ghcr.io/esmci/cime:latest pytest CIME/tests/test_unit*`:w
Start persistent container: `docker run -d --name cime --hostname docker -v ../:/root/model -w /root/model/cime -v ./inputdata:/root/inputdata -v ./storage:/root/storage -e CIME_MODEL=e3sm ghcr.io/esmci/cime:latest`
Run develop test: `docker exec -it cime /entrypoint.sh pytest CIME/tests/test_unit*`
Create a case: `docker exec -it cime /entrypoint.sh ./scripts/create_newcase --compset X --res f19_g16 --case /root/storage/cases/case01`
Setup a case: `docker exec -it -w /root/storage/cases/case01 cime /entrypoint.sh ./case.setup`
Build a case: `docker exec -it -w /root/storage/cases/case01 cime /entrypoint.sh ./case.build`
Submit a case: `docker exec -it -w /root/storage/cases/case01 cime /entrypoint.sh ./case.submit`
Query case config: `docker exec -it -w /root/storage/cases/case01 cime /entrypoint.sh ./xmlquery`
Change a case config: `docker exec -it -w /root/storage/cases/case01 cime /entrypoint.sh ./xmlchange`
Run a model system test: `docker exec -it cime /entrypoint.sh ./scripts/create_test SMS.f19_g16.S`

### Testing

Unit tests: `CIME/tests/test_unit*.py`
E2E tests: `CIME/tests/test_sys*.py`

Setup: `pip install -r test-requirements.txt`

Running tests: `pytest CIME/tests/test_*.py`

### Code Quality

Follow `pep8` style guidelines.

Use Google style for docstrings.

Use `black` and `pylint` for formatting and linting.

Always use `pre-commit` before commiting code, e.g. `pre-commit run -a`.

### Documentation

Documentation is found under `doc/`.

Always write documentation in reStructured text.

Setup: `pip install -r doc/requirements.txt`

Build documentation: `cd doc; make html`

### Architecture

The `Case` class (`CIME/case/case.py`) is the core of CIME.

Case configuration is handled by XML files. 

- Dynamic configuration `CIME/XML/env_*.py`, read/write configuration specific to a `Case`.
- Static configuration, all non `env_*.py` files under `CIME/XML/*.py`, readonly provided before `Case` is constructed.

Dynamic config classes named after XML they read e.g. `Machines`.

Static config classes name `Env*`.

Model System Tests are found under `CIME/SystemTests/`, each test type has it's own module.

CIME is heavily XML-driven. Key concepts:
- Generic XML handling is in `CIME/XML/generic_xml.py`
- All XML classes inherit from `GenericXML`
- XML schemas are in `CIME/data/config/xml_schemas/`
- Config files define machines, compsets, grids, tests

## Development Notes
- Do not use external packages; if it's required ask for users approval
- Host models provide static configuration
- Dynamic configuration is dervice from static configuration + user input
- Always use dependency injection; if refactoring prefer dependency injection
- The CASE class is spread across multiple files
- Running model system tests require a support machine
- Can use docker container if not on supported machine
