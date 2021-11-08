string(APPEND FFLAGS " -I/project/s824/edavin/OASIS3-MCT_2.0/build.pgi/build/lib/mct -I/project/s824/edavin/OASIS3-MCT_2.0/build.pgi/build/lib/psmile.MPI1")
string(APPEND SLIBS " -llapack -lblas")
string(APPEND SLIBS " -L/project/s824/edavin/OASIS3-MCT_2.0/build.pgi/lib -lpsmile.MPI1 -lscrip -lmct_oasis -lmpeu_oasis")
