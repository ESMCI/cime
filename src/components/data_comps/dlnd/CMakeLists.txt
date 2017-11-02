MESSAGE("   + DLND:")
FILE(GLOB DLND_SOURCE *F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
          ${ACME_PIO_LIBRARY_DIR}
)
ADD_LIBRARY (dlnd ${DLND_SOURCE})
ADD_DEPENDENCIES(dlnd shrsys shr seq esmf gptl)
