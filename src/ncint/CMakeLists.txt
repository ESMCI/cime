cmake_minimum_required (VERSION 2.8.12)

add_library(ncint nc_get_vard.c ncintdispatch.c ncint_pio.c nc_put_vard.c)

# set up include-directories
include_directories(
  "${CMAKE_BINARY_DIR}"
  "${PROJECT_SOURCE_DIR}"   # to find foo/foo.h
  "${PROJECT_BINARY_DIR}")  # to find foo/config.h

# Include the clib source directory
target_include_directories (ncint
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# Include the ncint source directory
target_include_directories (ncint
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/../clib)

#===== NetCDF-C =====
find_package (NetCDF "4.3.3" COMPONENTS C)
if (NetCDF_C_FOUND)
  target_include_directories (ncint
    PUBLIC ${NetCDF_C_INCLUDE_DIRS})
  target_compile_definitions (ncint
    PUBLIC _NETCDF)
  target_link_libraries (ncint
    PUBLIC ${NetCDF_C_LIBRARIES})
  if (${NetCDF_C_HAS_PARALLEL})
    target_compile_definitions (ncint
      PUBLIC _NETCDF4)
  endif ()
  if (${NetCDF_C_LOGGING_ENABLED})
    target_compile_definitions (ncint
      PUBLIC NETCDF_C_LOGGING_ENABLED)
    # netcdf.h needs this to be defined to use netCDF logging.
    target_compile_definitions (ncint
      PUBLIC LOGGING)
  endif()
else ()
  target_compile_definitions (ncint
    PUBLIC _NONETCDF)
endif ()



