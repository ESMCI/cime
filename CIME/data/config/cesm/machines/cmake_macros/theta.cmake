string(APPEND CFLAGS " -xMIC-AVX512")
string(APPEND FFLAGS " -xMIC-AVX512")
set(CONFIG_ARGS "--host=cray")
string(APPEND SLIBS " -L$(NETCDF_DIR)/lib -lnetcdff -L$(NETCDF_DIR)/lib -lnetcdf -Wl,-rpath -Wl,$(NETCDF_DIR)/lib")
