  ! This is a test of the PIO Fortran library.

  ! This tests var functions.

  ! Ed Hartnett, 8/28/20
#include "config.h"

program ftst_vars
  use mpi
  use pio
  integer :: my_rank, ntasks
  integer :: ierr
  
  ! Set up MPI
  call MPI_Init(ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, my_rank, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, ntasks , ierr)
  
  if (my_rank .eq. 0) print *,'Testing variables...'

  call PIO_
     
  if (my_rank .eq. 0) print *,'SUCCESS!'
  call MPI_Finalize(ierr)        
end program ftst_vars
