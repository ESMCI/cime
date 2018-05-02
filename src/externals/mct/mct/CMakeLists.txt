# AGS: CMake logic already existed -- preserving that functionalituy
#       within !E3SM_BUILD.
if (NOT E3SM_BUILD)

set(genf90_files shr_infnan_mod.F90.in shr_assert_mod.F90.in)

process_genf90_source_list("${genf90_files}" ${CMAKE_CURRENT_SOURCE_DIR}
  share_genf90_sources)

sourcelist_to_parent(share_genf90_sources)

list(APPEND share_sources "${share_genf90_sources}")

list(APPEND share_sources shr_kind_mod.F90 shr_const_mod.F90
  shr_sys_mod.F90 shr_log_mod.F90 shr_spfn_mod.F90)

sourcelist_to_parent(share_sources)

ELSE() #E3SM_BUILD

MESSAGE("   + MCT:")
FILE(GLOB MCT_SOURCE *F90)
INCLUDE_DIRECTORIES (${MPEU_BINARY_DIR} ${MPI_Fortran_INCLUDE_PATH})
ADD_LIBRARY (mct ${MCT_SOURCE})
ADD_DEPENDENCIES(mct mpeu)

ENDIF()

