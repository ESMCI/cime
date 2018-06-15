# AGS: This file already existed for unit test build --
#      Leaving that logic alone under NOT E3SM_BUILD
#

IF (NOT E3SM_BUILD)
# CMake for Unit Test build

set(genf90_files shr_infnan_mod.F90.in shr_assert_mod.F90.in)

process_genf90_source_list("${genf90_files}" ${CMAKE_CURRENT_BINARY_DIR}
  share_genf90_sources)

sourcelist_to_parent(share_genf90_sources)

list(APPEND share_sources "${share_genf90_sources}")

list(APPEND share_sources
  shr_file_mod.F90
  shr_kind_mod.F90
  shr_const_mod.F90
  shr_sys_mod.F90
  shr_log_mod.F90
  shr_orb_mod.F90
  shr_spfn_mod.F90
  shr_strconvert_mod.F90
  shr_cal_mod.F90
  shr_nl_mod.F90
  shr_precip_mod.F90
  shr_string_mod.F90
  shr_timer_mod.F90
  shr_vmath_mod.F90
  shr_wv_sat_mod.F90
  shr_flds_mod.F90
  shr_infnan_mod.F90)

# Build a separate list containing the mct wrapper and its dependencies. That
# way, this list can be easily included in unit test builds that link to mct,
# but excluded from builds that do not include mct.
list(APPEND share_mct_sources
  mct_mod.F90
  shr_mct_mod.F90
  shr_mpi_mod.F90
  shr_pcdf_mod.F90)

# Build a separate list containing the pio wrapper and its dependencies. That
# way, this list can be easily included in unit test builds that include PIO or
# a stub of PIO, but excluded from builds that do not include PIO.
list(APPEND share_pio_sources
  shr_pio_mod.F90)

sourcelist_to_parent(share_sources)
sourcelist_to_parent(share_mct_sources)
sourcelist_to_parent(share_pio_sources)
ELSE()
# CMake for E3SM build
  MESSAGE("   + SHRSYS, SHRCAL, SHR:")

  SET(TEMPSRCF90 shr_assert_mod.F90  shr_frz_mod.F90  shr_infnan_mod.F90)

FOREACH(tempfile IN LISTS TEMPSRCF90)
MESSAGE("Add custom generation command for ${tempfile}")
ADD_CUSTOM_COMMAND(
	OUTPUT ${tempfile}
	COMMAND ${GENF90_EXE}/genf90.pl ${CMAKE_CURRENT_SOURCE_DIR}/${tempfile}.in > ${tempfile}
	DEPENDS  ${tempfile}.in
)
ENDFOREACH()


  #First build these files, which have no dependencies and are depended on elsewhere
  FILE(GLOB SHR_SYS_SOURCE shr_sys_mod.F90 shr_kind_mod.F90
                           shr_mpi_mod.F90 shr_log_mod.F90 shr_pio_mod.F90
                           shr_file_mod.F90 shr_string_mod.F90 shr_timer_mod.F90
                           shr_const_mod.F90 shr_orb_mod.F90
                           shr_nl_mod.F90 shr_strconvert_mod.F90
                           shr_wv_sat_mod.F90 shr_flds_mod.F90
                           shr_abort_mod.F90 shr_ncread_mod.F90 shr_map_mod.F90)

  # infnan required  -DCPRGNU to compile on gnu)
  INCLUDE_DIRECTORIES (${E3SM_SHR_DIR}) #shr_assert.h
  ADD_LIBRARY (shrsys ${SHR_SYS_SOURCE} ${TEMPSRCF90})
  ADD_DEPENDENCIES(shrsys  PIO)

  #Later, build these files, teasing out circular directory dependencies
  FILE(GLOB SHR_CAL_SOURCE
          shr_cal_mod.F90 # need esmf timers
          shr_mct_mod.F90
          shr_pcdf_mod.F90
          mct_mod.F90) # need m_attrvec
  ADD_LIBRARY (shrcal ${SHR_CAL_SOURCE})
  ADD_DEPENDENCIES(shrcal  esmf mct)

  #Then build the rest of the files, which have dependencies
  FILE(GLOB SHR_SOURCE  *F90 *c)
  LIST(REMOVE_ITEM SHR_SOURCE ${SHR_SYS_SOURCE} ${SHR_CAL_SOURCE})
  INCLUDE_DIRECTORIES (${MCT_BINARY_DIR}
                       ${MPEU_BINARY_DIR}
                       ${GPTL_BINARY_DIR}  #Need perf_mod.mod
                       ${ESMF_BINARY_DIR} # esmf.mod
                       ${SEQ_BINARY_DIR}  #seq_flds_mod
                       ${STREAMS_BINARY_DIR}  #shr_dmodel_mod
                       ${E3SM_PIO_LIBRARY_DIR} #Need pio.mod
                       ${MPI_Fortran_INCLUDE_PATH})
  ADD_LIBRARY (shr ${SHR_SOURCE})
  ADD_DEPENDENCIES(shr  mct mpeu gptl esmf seq streams)
  ADD_DEPENDENCIES(shr  PIO)

ENDIF()
