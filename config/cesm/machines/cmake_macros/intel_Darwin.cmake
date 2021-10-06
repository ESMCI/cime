if (NOT compile_threaded)
  string(APPEND FFLAGS " -heap-arrays")
endif()
