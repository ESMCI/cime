MESSAGE("   + DLND:")
FILE(GLOB DLND_SOURCE *F90 mct/*F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
          ${STREAMS_BINARY_DIR}  #shr_strdata_mod
          ${ACME_PIO_LIBRARY_DIR}
)
ADD_LIBRARY (dlnd ${DLND_SOURCE})
ADD_DEPENDENCIES(dlnd shrsys shr seq esmf gptl streams)
