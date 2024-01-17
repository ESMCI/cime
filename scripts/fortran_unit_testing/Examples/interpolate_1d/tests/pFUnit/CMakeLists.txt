extract_sources("interpolate_1d.F90" "${interpolate_sources}" test_sources)

add_pfunit_ctest(pFunit_interpolate
  TEST_SOURCES "test_interpolate_point.pf"
  OTHER_SOURCES "${test_sources}")
