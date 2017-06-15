# AGS: CMake logic already existed -- preserving that functionalituy
#       within !ACME_BUILD.
if (NOT ACME_BUILD)

list(APPEND drv_sources
  component_type_mod.F90
  map_glc2lnd_mod.F90
  map_lnd2glc_mod.F90
  map_lnd2rof_irrig_mod.F90
  seq_map_mod.F90
  seq_map_type_mod.F90
  vertical_gradient_calculator_base.F90
  vertical_gradient_calculator_2nd_order.F90
  )

sourcelist_to_parent(drv_sources)

ELSE () # Code for ACME build system

MESSAGE("   + Driver:")
FILE(GLOB DRIVER_SOURCE  *F90)

#Glob everything but main program files into libdriver
#  ccsm_comp_mod depends on which dycores are built (i.e. clm vs dlnd)
#  The two ccsm* files are compiled for each executable which link
#  against the precompiled driver library.
FILE(GLOB MAIN_SOURCE  cesm_*F90)
LIST(REMOVE_ITEM DRIVER_SOURCE ${MAIN_SOURCE})

INCLUDE_DIRECTORIES (
     ${SHR_BINARY_DIR}  #sys_shr_mod, mct_mod. shr_cal
     ${ACME_SHR_DIR} #shr_assert.h
     ${SEQ_BINARY_DIR}  #seq_comm_mct
     ${GPTL_BINARY_DIR} #Need perf_mod.mod
     ${ESMF_BINARY_DIR} #esmf.mod
     ${MPI_Fortran_INCLUDE_PATH}) #mpif.h

ADD_LIBRARY (driver ${DRIVER_SOURCE})
ADD_DEPENDENCIES(driver  shr gptl seq esmf)

ENDIF()
