# AGS: CMake logic already existed -- preserving that functionalituy
#       within !E3SM_BUILD.

MESSAGE("   + STREAMS:")
FILE(GLOB STREAMS_SOURCE  *F90)
INCLUDE_DIRECTORIES (
      ${SHR_BINARY_DIR} #sys_shr_mod
      ${E3SM_SHR_DIR}
      ${E3SM_PIO_LIBRARY_DIR} #pio.mod
      ${GPTL_BINARY_DIR}  #perf.mod
      ${SEQ_BINARY_DIR}  #seq_flds_mod
      ${ESMF_BINARY_DIR} # esmf.mod
      ${MCT_BINARY_DIR}
      ${MPEU_BINARY_DIR}
      )
ADD_LIBRARY (streams ${STREAMS_SOURCE})
ADD_DEPENDENCIES(streams shrsys shrcal seq gptl PIO)

