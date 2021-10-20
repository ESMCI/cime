if (MPILIB STREQUAL mpi-serial AND NOT compile_threaded)
  set(PFUNIT_PATH "/fs/cgd/csm/tools/pFUnit/pFUnit3.3.3_izumi_Intel19.0.1_noMPI_noOpenMP")
endif()
