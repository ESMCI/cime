  ! This is a test of the PIO Fortran library.

  ! This tests var functions.

  ! Ed Hartnett, 8/28/20
#include "config.h"

program ftst_vars
  use mpi
  use pio
  
  type(iosystem_desc_t) :: pio_iosystem
  type(file_desc_t)     :: pio_file  
  integer :: my_rank, ntasks
  integer :: niotasks = 1, stride = 1
  character(len=64) :: filename = 'ftst_vars.nc'
  integer :: iotype = PIO_iotype_netcdf4c
  integer :: ierr
  
  ! Set up MPI
  call MPI_Init(ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, my_rank, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, ntasks , ierr)
  
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

  ! Close the file.
  call PIO_closefile(pio_file)

  ! Open the file.

  

  ! Finalize PIO.
  call PIO_finalize(pio_iosystem, ierr)
  
  if (my_rank .eq. 0) print *,'SUCCESS!'
  call MPI_Finalize(ierr)        
end program ftst_vars
