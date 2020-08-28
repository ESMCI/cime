  ! This is a test of the PIO Fortran library.

  ! This tests var functions.

  ! Ed Hartnett, 8/28/20
#include "config.h"

program ftst_vars
  use mpi
  use pio
  use pio_nf
  
  type(iosystem_desc_t) :: pio_iosystem
  type(file_desc_t)     :: pio_file
  type(var_desc_t)      :: pio_var  
  integer :: my_rank, ntasks
  integer :: niotasks = 1, stride = 1
  character(len=64) :: filename = 'ftst_vars.nc'
  character(len=64) :: dim_name = 'influence_on_Roman_history'
  character(len=64) :: var_name = 'Caesar'
  integer :: dimid, dim_len = 40
  integer :: chunksize = 10
  integer :: storage_in
  integer (kind=PIO_OFFSET_KIND) :: chunksizes_in(2)
  integer, parameter :: NUM_IOTYPES = 2
  integer :: iotype(NUM_IOTYPES) = (/ PIO_iotype_netcdf4c, PIO_iotype_netcdf4p /)
  integer :: iotype_idx, ierr
  
  ! Set up MPI
  call MPI_Init(ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, my_rank, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, ntasks , ierr)

  ! This whole test only works for netCDF/HDF5 files, because it is
  ! about chunking.
#ifdef _NETCDF4
  if (my_rank .eq. 0) print *,'Testing variables...'

  ! Initialize PIO.
  call PIO_init(my_rank, MPI_COMM_WORLD, niotasks, 0, stride, &
       PIO_rearr_subset, pio_iosystem, base=1)

  ! Set error handling for test.
  call PIO_seterrorhandling(pio_iosystem, PIO_RETURN_ERROR)  
  call PIO_seterrorhandling(PIO_DEFAULT, PIO_RETURN_ERROR)

  !ret_val = PIO_set_log_level(3)
  do iotype_idx = 1, NUM_IOTYPES
     ! Create a file.
     ierr = PIO_createfile(pio_iosystem, pio_file, iotype(iotype_idx), filename)
     if (ierr .ne. PIO_NOERR) stop 3
     
     ! Define a dim.
     ret_val = PIO_def_dim(pio_file, dim_name, dim_len, dimid)
     if (ierr .ne. PIO_NOERR) stop 5
     
     ! Define a var.
     ret_val = PIO_def_var(pio_file, var_name, PIO_int, (/dimid/), pio_var)
     if (ierr .ne. PIO_NOERR) stop 7
     
     ! Define chunking for var.
     ret_val = PIO_def_var_chunking(pio_file, pio_var, 0, (/chunksize/))
     if (ierr .ne. PIO_NOERR) stop 9
     
     ! Close the file.
     call PIO_closefile(pio_file)
     
     ! Open the file.
     ret_val = PIO_openfile(pio_iosystem, pio_file, iotype(iotype_idx), filename, PIO_nowrite)  
     if (ierr .ne. PIO_NOERR) stop 23
     
     ! Find var chunksizes.
     ret_val = PIO_inq_var_chunking(pio_file, 1, storage_in, chunksizes_in)
     if (ierr .ne. PIO_NOERR) stop 25
     if (chunksizes_in(1) .ne. chunksize) stop 26
     
     ! Close the file.
     call PIO_closefile(pio_file)

  end do
  
  ! Finalize PIO.
  call PIO_finalize(pio_iosystem, ierr)
  
  if (my_rank .eq. 0) print *,'SUCCESS!'
#endif 
  call MPI_Finalize(ierr)        
end program ftst_vars
