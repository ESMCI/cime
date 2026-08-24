
if (COMP_NAME STREQUAL gptl)
    string(APPEND CPPDEFS " -DHAVE_NANOTIME -DBIT64 -DHAVE_SLASHPROC -DHAVE_GETTIMEOFDAY")
endif()

# Select the CIME_MODEL-specific pixi environment (see docker/pixi.toml).
set(PIXI_ENV "/opt/pixi-env/.pixi/envs/$ENV{CIME_MODEL}")

string(APPEND CMAKE_C_FLAGS " -I${PIXI_ENV}/include -O1 -g -fno-fast-math -frounding-math -fsignaling-nans -fno-inline -fno-aggressive-loop-optimizations")
# Note: -ffpe-trap is intentionally omitted. Under conda-forge MPICH/UCX in a
# container, UCX performs a benign IEEE div-by-zero while probing the veth
# interface speed (reported as 0) during MPI_Init. With an FPE trap active that
# benign operation raises a fatal SIGFPE before the model starts. The trap only
# aids model (science-code) debugging, which is out of scope for this run
# infrastructure, so it is dropped here.
string(APPEND CMAKE_Fortran_FLAGS " -I${PIXI_ENV}/include -O1 -g -fno-fast-math -frounding-math -fsignaling-nans -fno-inline -fno-aggressive-loop-optimizations")
string(APPEND CMAKE_CXX_FLAGS " -I${PIXI_ENV}/include")

# required for grid generation tests that use make
if (CMAKE_SOURCE_DIR MATCHES "^.*TestGridGeneration.*$")
    string(APPEND FFLAGS " -I${PIXI_ENV}/include")
    string(APPEND SLIBS " -L${PIXI_ENV}/lib -lnetcdf -lnetcdff")
endif()

# DEBUGGING variables
# get_cmake_property(_variableNames VARIABLES)
# foreach (_variableName ${_variableNames})
#     message("${_variableName}=${${_variableName}}")
# endforeach()
# message( FATAL_ERROR "EXIT")
