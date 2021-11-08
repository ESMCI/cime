string(APPEND FFLAGS " -I/project/s824/edavin/OASIS3-MCT_2.0/build.cray/build/lib/mct -I/project/s824/edavin/OASIS3-MCT_2.0/build.cray/build/lib/psmile.MPI1")
string(APPEND SLIBS " -L/project/s824/edavin/OASIS3-MCT_2.0/build.cray/lib -lpsmile.MPI1 -lscrip -lmct_oasis -lmpeu_oasis")
