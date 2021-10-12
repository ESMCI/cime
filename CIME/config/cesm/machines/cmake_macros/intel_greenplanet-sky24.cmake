set(NETCDF_PATH "$ENV{NCDIR}")
set(PNETCDF_PATH "$ENV{PNDIR}")
string(APPEND SLIBS " -L${NETCDF_PATH}/lib -lnetcdf -lnetcdff")
