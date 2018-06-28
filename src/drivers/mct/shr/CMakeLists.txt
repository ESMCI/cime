# AGS: CMake logic already existed -- preserving that functionalituy
#       within !CIME_BUILD.
if (NOT CIME_BUILD)

list(APPEND drv_sources
  glc_elevclass_mod.F90
  seq_cdata_mod.F90
  seq_comm_mct.F90
  seq_infodata_mod.F90
  seq_io_read_mod.F90
  )

sourcelist_to_parent(drv_sources)

ELSE() # Code for CIME build system

FILE(GLOB SEQ_SOURCE  *F90)
INCLUDE_DIRECTORIES (
     ${SHR_BINARY_DIR} #sys_shr_mod, mct_mod. shr_cal
     ${CIME_SHR_DIR} #shr_assert.h
     ${ESMF_BINARY_DIR} #esmf.mod
     ${MPI_Fortran_INCLUDE_PATH} #mpif.h
     ${MCT_BINARY_DIR}
     ${MPEU_BINARY_DIR})
ADD_LIBRARY (seq ${SEQ_SOURCE})
ADD_DEPENDENCIES(seq  shrsys shrcal esmf)

ENDIF()
