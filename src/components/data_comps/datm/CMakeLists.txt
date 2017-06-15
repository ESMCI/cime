MESSAGE("   + DATM:")
FILE(GLOB DATM_SOURCE *F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
)
ADD_LIBRARY (datm ${DATM_SOURCE})
ADD_DEPENDENCIES(datm  shrsys shr seq esmf gptl)
