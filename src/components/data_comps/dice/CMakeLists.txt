MESSAGE("   + DICE:")
FILE(GLOB DICE_SOURCE *F90)

INCLUDE_DIRECTORIES (
          ${SHR_BINARY_DIR}
          ${ESMF_BINARY_DIR}
          ${GPTL_BINARY_DIR}
          ${SEQ_BINARY_DIR}
)
ADD_LIBRARY (dice ${DICE_SOURCE})
ADD_DEPENDENCIES(dice  shrsys shr seq esmf gptl)
