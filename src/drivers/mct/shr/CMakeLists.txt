# AGS: CMake logic already existed -- preserving that functionalituy
#       within !E3SM_BUILD.
if (NOT E3SM_BUILD)

list(APPEND drv_sources
  glc_elevclass_mod.F90
  seq_cdata_mod.F90
  seq_comm_mct.F90
  seq_infodata_mod.F90
  seq_io_read_mod.F90
  )

sourcelist_to_parent(drv_sources)

ELSE() # Code for E3SM build system

FILE(GLOB SEQ_SOURCE  *F90)
INCLUDE_DIRECTORIES (
     ${SHR_BINARY_DIR} #sys_shr_mod, mct_mod. shr_cal
     ${E3SM_SHR_DIR} #shr_assert.h
     ${E3SM_PIO_LIBRARY_DIR}  #pio.mod
     ${ESMF_BINARY_DIR} #esmf.mod
     ${MPI_Fortran_INCLUDE_PATH} #mpif.h
     ${MCT_BINARY_DIR}
     ${MPEU_BINARY_DIR})
ADD_LIBRARY (seq ${SEQ_SOURCE})
ADD_DEPENDENCIES(seq  shrsys shrcal esmf)
ADD_DEFINITIONS(" -DNUM_COMP_INST_ATM=1 -DNUM_COMP_INST_LND=1
-DNUM_COMP_INST_OCN=1
-DNUM_COMP_INST_ICE=1 -DNUM_COMP_INST_GLC=1 -DNUM_COMP_INST_ROF=1
-DNUM_COMP_INST_WAV=1 -DNUM_COMP_INST_ESP=1")

ENDIF()
