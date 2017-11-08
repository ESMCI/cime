# AGS: CMake logic already existed -- preserving that functionalituy
#       within !ACME_BUILD.

MESSAGE("   + STREAMS:")
FILE(GLOB STREAMS_SOURCE  *F90)
INCLUDE_DIRECTORIES (
      ${SHR_BINARY_DIR} #sys_shr_mod
      ${ACME_SHR_DIR}
      ${ACME_PIO_LIBRARY_DIR} #pio.mod
      ${GPTL_BINARY_DIR}  #perf.mod
      ${SEQ_BINARY_DIR}  #seq_flds_mod
      ${ESMF_BINARY_DIR} # esmf.mod
      )
ADD_LIBRARY (streams ${STREAMS_SOURCE})
ADD_DEPENDENCIES(streams shrsys shrcal seq gptl PIO)

