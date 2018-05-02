MESSAGE("   + DLND:")
FILE(GLOB DLND_SOURCE *F90 mct/*F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
          ${STREAMS_BINARY_DIR}  #shr_strdata_mod
          ${E3SM_PIO_LIBRARY_DIR}
          ${MCT_BINARY_DIR}
          ${MPEU_BINARY_DIR}
)
ADD_LIBRARY (dlnd ${DLND_SOURCE})
ADD_DEPENDENCIES(dlnd shrsys shr seq esmf gptl streams)
