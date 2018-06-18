MESSAGE("   + SATM:")
FILE(GLOB XATM_SOURCE *F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
          ${MCT_BINARY_DIR}
          ${MPEU_BINARY_DIR}
	  ${XSHR_BINARY_DIR}
)
ADD_LIBRARY (xatm ${XATM_SOURCE})
ADD_DEPENDENCIES(xatm shrsys shr seq esmf gptl xshr)
