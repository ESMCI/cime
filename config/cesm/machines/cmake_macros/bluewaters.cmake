if (MODEL STREQUAL gptl)
  string(APPEND CPPDEFS " -DHAVE_PAPI")
endif()
set(PIO_FILESYSTEM_HINTS "lustre")
