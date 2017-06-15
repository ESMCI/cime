MESSAGE("   + SROF:")
FILE(GLOB SROF_SOURCE *F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
)
ADD_LIBRARY (srof ${SROF_SOURCE})
ADD_DEPENDENCIES(srof  shrsys shr seq esmf gptl)
