cmake_minimum_required(VERSION 2.8)
include(ExternalProject)
set(CIME_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")

list(APPEND CMAKE_MODULE_PATH ${CIME_CMAKE_MODULE_DIRECTORY})
include(CIME_initial_setup)

project(cime_tests Fortran C)

# We rely on pio for cmake utilities like findnetcdf.cmake, so that we don't
# need to duplicate this cmake code
if (EXISTS ${SRC_ROOT}/libraries/parallelio/cmake)
  list(APPEND CMAKE_MODULE_PATH "${SRC_ROOT}/libraries/parallelio/cmake")
else()
  list(APPEND CMAKE_MODULE_PATH "${SRC_ROOT}/externals/scorpio/cmake")
endif()

include(CIME_utils)
find_package(NetCDF COMPONENTS C Fortran)
include_directories(${NetCDF_C_INCLUDE_DIRS} ${NetCDF_Fortran_INCLUDE_DIRS})

# TODO: Some of the below should be done in the relevant directories, not in
# this top level CMakeLists.

# Now a bunch of includes for share code.

# csm_share (we don't build it here because it seems to be built differently
# by different tests?)

if (EXISTS ${SRC_ROOT}/share/src)
  add_subdirectory(${SRC_ROOT}/share/src share_src)
  add_subdirectory(${SRC_ROOT}/share/unit_test_stubs/util csm_share_stubs)
  include_directories(${SRC_ROOT}/share/include)
else()
  add_subdirectory(${SRC_ROOT}/share/util csm_share)
  add_subdirectory(${SRC_ROOT}/share/unit_test_stubs/util csm_share_stubs)
  include_directories(${SRC_ROOT}/share/include)
endif()

# esmf_wrf_timemgr not built here because it depends on csm_share.
if (EXISTS ${SRC_ROOT}/share/src/esmf_wrf_timemgr)
  add_subdirectory(${SRC_ROOT}/share/src/esmf_wrf_timemgr esmf_wrf_timemgr)
  include_directories(${SRC_ROOT}/share/src/esmf_wrf_timemgr)
else()
  add_subdirectory(${SRC_ROOT}/share/esmf_wrf_timemgr esmf_wrf_timemgr)
  include_directories(${SRC_ROOT}/share/esmf_wrf_timemgr)
endif()

# Now the actual test directories.
add_subdirectory(${SRC_ROOT}/share/test/unit ${CMAKE_BINARY_DIR}/unittests)
