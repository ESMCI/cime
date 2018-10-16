# AGS: CMake logic already existed -- preserving that functionalituy
#       within !E3SM_BUILD.

MESSAGE("   + CIMESHARE:")
FILE(GLOB CIMESHARE_SOURCE  *F90)
INCLUDE_DIRECTORIES (
      ${E3SM_SHR_DIR}
      ${E3SM_PIO_LIBRARY_DIR} #pio.mod
      ${GPTL_BINARY_DIR}  #perf.mod
      ${SEQ_BINARY_DIR}  #seq_flds_mod
      ${ESMF_BINARY_DIR} # esmf.mod
      ${MCT_BINARY_DIR}
      ${MPEU_BINARY_DIR}
      )
ADD_LIBRARY (cimeshare ${CIMESHARE_SOURCE})
ADD_DEPENDENCIES(cimeshare seq gptl mct mpeu PIO)

