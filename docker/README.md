# Docker development container
This container is built for development and testing purposes.

The default base image is `condaforge/mambaforge:4.11.0-0`.

The only supported compiler is `gnu` provided by `conda-forge`.

## Targets

There are three possible build targets in the Dockerfile. The `slurm` and `pbs` targets are built on top of the `base`.

| Target | Description
| ------ | -----------
| base | Base image with no batch system.
| slurm | Slurm batch system with configuration and single queue.
| pbs | PBS batch system with configuration and single queue.

## Build the container
```bash
docker build -t {image}:{tag} --target {target} docker/dev/

# e.g.
# Building the base image
docker build -t cime:latest --target base docker/dev/

# Building the slurm image
docker build -t cime:latest --target slurm docker/dev
```

### Build with custom base tag
```bash
docker build -t {image}:{tag} --build-arg MAMBAFORGE_VERSION={version}
```

## Running the container
The default environment is similar to the one used by GitHub Actions. It will clone CIME into `/src/cime`, set `CIME_MODEL=cesm` and run CESM's `checkout_externals`. This will create a minimum base environment to run both unit and system tests.

The `CIME_MODEL` environment vairable will change the environment that is created.

Setting it to `E3SM` will clone E3SM into `/src/E3SM`, checkout the submodules and update the CIME repository using `CIME_REPO` and `CIME_BRANCH`.

Setting it to `CESM` will clone CESM into `/src/CESM`, run `checkout_externals` and update the CIME repository using `CIME_REPO` and `CIME_BRANCH`.

The container can further be modified using the environment variables defined below.

```bash
docker run -it --name cime --hostname docker cime:latest bash

# Run with E3SM
docker run -it --name cime --hostname docker -e CIME_MODEL=e3sm cime:latest bash
```

> It's recommended when running the container to pass `--hostname docker` as it will match the custom machine defined in `config_machines.xml`. If this is omitted, `--machine docker` must be passed to CIME commands in order to use the correct machine definition.

### Environment variables

Environment variables to modify the container environment.

| Name | Description | Default |
| ---- | ----------- | ------- |
| INIT | Set to false to skip init | true |
| GIT_SHALLOW | Performs shallow checkouts, to save time | false |
| UPDATE_CIME | Setting this will cause the CIME repository to be updated using `CIME_REPO` and `CIME_BRANCH` | "false" |
| CIME_MODEL | Setting this will change which environment is loaded | |
| CIME_REPO | CIME repository URL | https://github.com/ESMCI/cime |
| CIME_BRANCH | CIME branch that will be cloned | master |
| E3SM_REPO | E3SM repository URL | https://github.com/E3SM-Project/E3SM |
| E3SM_BRANCH | E3SM branch that will be cloned | master |
| CESM_REPO | CESM repository URL | https://github.com/ESCOMP/CESM |
| CESM_BRANCH | CESM branch that will be cloned | master |

## Persisting data

The `config_machines.xml` definition as been setup to provided persistance for inputdata, cases, archives and tools. The following paths can be mounted as volumes to provide persistance.

* /storage/inputdata
* /storage/cases
* /storage/archives
* /storage/tools

```bash
docker run -it -v {hostpath}:{container_path} cime:latest bash

e.g.
docker run -it -v ${PWD}/data-cache:/storage/inputdata cime:latest bash
```

It's also possible to persist the source git repositories.
```bash
docker run -it -v ${PWD}/src:/src cime:latest bash
```

Local git respositories can be mounted as well.
```bash
docker run -v ${PWD}:/src/cime cime:latest bash

docker run -v ${PWD}:/src/E3SM cime:latest bash
```
