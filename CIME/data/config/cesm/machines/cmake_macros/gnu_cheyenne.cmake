if (MODEL STREQUAL pio1)
  string(APPEND CPPDEFS " -DNO_MPIMOD")
endif()
string(APPEND SLIBS " -ldl")
