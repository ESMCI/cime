MESSAGE("   + SLND:")
FILE(GLOB SLND_SOURCE cpl/*F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
          ${MCT_BINARY_DIR}
          ${MPEU_BINARY_DIR}
)
ADD_LIBRARY (slnd ${SLND_SOURCE})
ADD_DEPENDENCIES(slnd  shrsys shr seq esmf gptl)
