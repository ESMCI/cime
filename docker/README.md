# Docker development/testing container

This container provides a reproducible environment for building and testing
CIME with either E3SM or CESM. It mirrors the environment used by the GitHub
Actions CI matrix.

**Platform support:** Linux amd64 only. The image uses x86-64 binaries (pixi, uv)
and `linux-64` conda-forge packages. It is designed to run as root with storage
under `/root/storage`.

## Dependencies via pixi + conda-forge

All scientific dependencies come from [conda-forge](https://conda-forge.org)
and are pinned in [`pixi.toml`](./pixi.toml) / [`pixi.lock`](./pixi.lock). Two
[pixi](https://pixi.sh) environments are baked into the image:

| Environment | Adds  | Purpose |
| ----------- | ----- | ------- |
| `e3sm`      | MOAB (tempest-remap) | E3SM builds/tests |
| `cesm`      | ESMF  | CESM builds/tests |

Both environments share a single solve group, so their compilers and their
`HDF5` / `netCDF` / `parallel-netCDF` stack resolve to byte-identical builds
(all `mpi_mpich_*` variants). Keeping one consistent I/O stack is what fixes
the broken `cprnc` seen with the previous spack-based image, where
`concretizer.unify: when_possible` allowed multiple `netCDF`/`HDF5` copies into
the dependency graph.

The environments are installed to `/opt/pixi-env/.pixi/envs/{e3sm,cesm}`. At
runtime the [`entrypoint.sh`](./entrypoint.sh) selects one based on
`CIME_MODEL` and puts it on the compiler/linker search paths.

> The legacy spack environment is kept for reference at
> [`legacy/spack.yaml`](./legacy/spack.yaml).

## Build the container

BuildKit is **required** (the Dockerfile uses cache mounts). Build from the
repository root so the build context includes the CIME sources:

```bash
DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile --platform linux/amd64 -t cime:latest .
```

### Targets

| Target | Description |
| ------ | ----------- |
| `base` | Ubuntu 24.04 with pixi and both environments installed. |
| `cprnc`| Builds the `cprnc` comparison tool against the `e3sm` netCDF. |
| `main` | Final image: `base` + Python test env (uv), input data, and `cprnc`. Default target. |

```bash
# e.g. build just the base image
DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile --platform linux/amd64 --target base -t cime:base .
```

### Customizing the pixi version

The pinned pixi release can be overridden (checksum must match):

```bash
DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile --platform linux/amd64 \
  --build-arg PIXI_VERSION=0.73.0 \
  --build-arg PIXI_SHA256=<sha256> \
  -t cime:latest .
```

## Running the container

`CIME_MODEL` selects both the pixi environment and the `config_machines.xml`
that is linked (`config_machines.v2.xml` for E3SM, `config_machines.v3.xml` for
CESM). It is **required** and must be set to `e3sm` or `cesm` (lowercase) — the
entrypoint validates this and exits with an error if invalid or unset.

```bash
# E3SM
docker run -it --hostname docker --shm-size=1g -e CIME_MODEL=e3sm cime:latest bash

# CESM
docker run -it --hostname docker --shm-size=1g -e CIME_MODEL=cesm cime:latest bash
```

### Required flags

- **`--hostname docker`** — Matches the custom machine name in `config_machines.xml`.
  If omitted, add `--machine docker` to all CIME commands.

- **`--shm-size=1g`** — Required for running the Fortran model with MPI.
  MPICH/UCX place their shared-memory transport buffers in `/dev/shm`, whose
  Docker default of 64 MB is exhausted by multi-rank runs (e.g. the 64-PE
  `f19_g16` layout), producing an out-of-memory abort. Use `--shm-size=1g` (or
  larger for bigger layouts), or `--ipc=host`. This is not needed for build-only
  or `--no-fortran-run` test invocations.

- **`-e CIME_MODEL=<model>`** — Must be `e3sm` or `cesm` (lowercase). Activates
  the corresponding pixi environment and config files.

## PE layout and core count

Default grid PE layouts in model repositories often request 32–64 MPI ranks
tuned for full compute nodes. Containers typically have far fewer cores, which
causes either `create_test` proc-pool overflow failures or MPICH
busy-poll livelocks when oversubscribed.

The container automatically sizes `MAX_TASKS_PER_NODE` to available cores
(respecting `docker run --cpus` / `--cpuset-cpus` limits). A generic
`config_pes.xml` is shipped at `/root/.cime/config_pes.xml` that caps any
grid/compset to one node's worth of ranks (negative `NTASKS=-1` scales with
`MAX_MPITASKS_PER_NODE`).

**For automatic capping**, pass `--pesfile` to test runs:

```bash
create_test SMS.f19_g16.X.docker_gnu --pesfile /root/.cime/config_pes.xml
```

**For ad-hoc task counts**, use `--pecount N` or the `_PN` test option:

```bash
create_test SMS_P4.f19_g16.X.docker_gnu  # forces 4 MPI ranks total
```

**Match container resources to intended parallelism** when invoking Docker:

```bash
# Limit to 4 cores for smaller tests
docker run --cpus=4 --hostname docker --shm-size=1g -e CIME_MODEL=e3sm cime:latest bash
```

## Persisting data

`config_machines.xml` stores inputdata, cases, archives and tools under
`/root/storage`. Mount volumes to persist them:

```bash
docker run -it --hostname docker --shm-size=1g -e CIME_MODEL=e3sm -v ${PWD}/data-cache:/root/storage/inputdata cime:latest bash
```

Source repositories can also be mounted:

```bash
docker run -it --hostname docker --shm-size=1g -e CIME_MODEL=e3sm \
  -v ${PWD}:/src/cime cime:latest bash
```

### Running without a shell

You can run CIME commands directly without entering a shell:

```bash
# Run pytest
docker run --rm --hostname docker --shm-size=1g -e CIME_MODEL=e3sm \
  -v ${PWD}:/src/cime -w /src/cime \
  cime:latest pytest CIME/tests/test_unit*

# Run create_test
docker run --rm --hostname docker --shm-size=1g -e CIME_MODEL=e3sm \
  -v ${PWD}:/src/cime -w /src/cime \
  cime:latest ./scripts/create_test SMS.f19_g16.X --pesfile /root/.cime/config_pes.xml
```
