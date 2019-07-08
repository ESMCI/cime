  !> This is a test program for the Fortran API use of the netCDF
  !! integration layer.

program ftst_pio
  use pio
  implicit none
  include 'mpif.h'

  integer :: myRank, ntasks
  integer :: ierr

  call MPI_Init(ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, myRank, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, ntasks, ierr)

  call MPI_Finalize(ierr)
  if (myRank .eq. 0) then
     print *, '*** SUCCESS running ftst_pio!'
  endif
end program ftst_pio
