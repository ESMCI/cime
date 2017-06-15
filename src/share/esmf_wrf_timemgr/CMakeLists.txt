# AGS: CMake logic already existed -- preserving that functionalituy
#       within !ACME_BUILD.
if (NOT ACME_BUILD)

list(APPEND esmf_wrf_timemgr_sources
  ESMF.F90
  ESMF_AlarmClockMod.F90
  ESMF_AlarmMod.F90
  ESMF_BaseMod.F90
  ESMF_BaseTimeMod.F90
  ESMF_CalendarMod.F90
  ESMF_ClockMod.F90
  ESMF_FractionMod.F90
  ESMF_ShrTimeMod.F90
  ESMF_Stubs.F90
  ESMF_TimeIntervalMod.F90
  ESMF_TimeMod.F90
  MeatMod.F90
  wrf_error_fatal.F90
  wrf_message.F90
  )

sourcelist_to_parent(esmf_wrf_timemgr_sources)

ELSE() #ACME_BUILD

MESSAGE("   + ESMF:")
FILE(GLOB ESMF_SOURCE  *F90 *c)
INCLUDE_DIRECTORIES (${CMAKE_CURRENT_SOURCE_DIR}   #ESMF_TimeMgr.inc
     ${SHR_BINARY_DIR} #sys_shr_mod
     ${MPI_Fortran_INCLUDE_PATH})
ADD_LIBRARY (esmf ${ESMF_SOURCE})
ADD_DEPENDENCIES(esmf shrsys)

ENDIF()
