MESSAGE("   + SESP:")
FILE(GLOB SESP_SOURCE *F90)
INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
#          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
          ${MCT_BINARY_DIR}
          ${MPEU_BINARY_DIR}
)
ADD_LIBRARY (sesp ${SESP_SOURCE})
ADD_DEPENDENCIES(sesp  shrcal seq esmf) #gptl
