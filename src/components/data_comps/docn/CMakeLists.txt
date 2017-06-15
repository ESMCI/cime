MESSAGE("   + DOCN:")
FILE(GLOB DOCN_SOURCE *F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
)
ADD_LIBRARY (docn ${DOCN_SOURCE})
ADD_DEPENDENCIES(docn  shrsys shr seq esmf gptl)
