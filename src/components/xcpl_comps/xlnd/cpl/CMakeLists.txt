MESSAGE("   + SATM:")
FILE(GLOB XLND_SOURCE *F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
          ${MCT_BINARY_DIR}
          ${MPEU_BINARY_DIR}
	  ${XSHR_BINARY_DIR}
)
ADD_LIBRARY (xlnd ${XLND_SOURCE})
ADD_DEPENDENCIES(xlnd shrsys shr seq esmf gptl xshr)
