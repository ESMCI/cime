  ! This is a test of the PIO Fortran library.

  ! This tests var functions.

  ! Ed Hartnett, 8/28/20
#include "config.h"

program ftst_vars
  use mpi
  use pio
  
  type(iosystem_desc_t) :: pio_iosystem
  type(file_desc_t)     :: pio_file
  type(var_desc_t)      :: pio_var  
  integer :: my_rank, ntasks
  integer :: niotasks = 1, stride = 1
  character(len=64) :: filename = 'ftst_vars.nc'
  character(len=64) :: dim_name = 'influence_on_Roman_history'
  character(len=64) :: var_name = 'Caesar'
  integer :: iotype = PIO_iotype_netcdf4c
  integer :: dimid, dim_len = 4
  integer :: ierr
  
  ! Set up MPI
  call MPI_Init(ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, my_rank, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, ntasks , ierr)

#ifdef _NETCDF4
  if (my_rank .eq. 0) print *,'Testing variables...'

  ! Initialize PIO.
  call PIO_init(my_rank, MPI_COMM_WORLD, niotasks, 0, stride, &
       PIO_rearr_subset, pio_iosystem, base=1)

  ! Set error handling for test.
  call PIO_seterrorhandling(pio_iosystem, PIO_RETURN_ERROR)  
  call PIO_seterrorhandling(PIO_DEFAULT, PIO_RETURN_ERROR)

  ! Create a file.
  ierr = PIO_createfile(pio_iosystem, pio_file, iotype, filename)
  if (ierr .ne. PIO_NOERR) stop 3

  ! Define a dim.
  ret_val = PIO_def_dim(pio_file, dim_name, dim_len, dimid)
  if (ierr .ne. PIO_NOERR) stop 5
  
  ! Define a var.
  ret_val = PIO_def_var(pio_file, var_name, PIO_int, (/dimid/), pio_var)
  if (ierr .ne. PIO_NOERR) stop 7

  ! Close the file.
  call PIO_closefile(pio_file)

  ! Open the file.
  ret_val = PIO_openfile(pio_iosystem, pio_file, iotype, filename, PIO_nowrite)  
  if (ierr .ne. PIO_NOERR) stop 23

  ! Find var chunksizes.

  ! Close the file.
  call PIO_closefile(pio_file)

  ! Finalize PIO.
  call PIO_finalize(pio_iosystem, ierr)
  
  if (my_rank .eq. 0) print *,'SUCCESS!'
#endif 
  call MPI_Finalize(ierr)        
end program ftst_vars
