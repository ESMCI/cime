set(sources_needed circle.F90)
extract_sources("${sources_needed}" "${circle_area_sources}" test_sources)

add_pfunit_ctest(pFunit_circle_area
  TEST_SOURCES "test_circle.pf"
  OTHER_SOURCES "${test_sources}")
