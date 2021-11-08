string(APPEND SLIBS " -L$(NETCDF_PATH)/lib -Wl,-rpath,$(NETCDF_PATH)/lib -lnetcdff -lnetcdf")
