  !> This is a test program for the Fortran API use of the netCDF
  !! integration layer.

program ftst_pio
  use pio
  implicit none
  include 'mpif.h'
  include 'netcdf.inc'

  integer :: myRank, ntasks
  type(iosystem_desc_t) :: ioSystem
  integer :: niotasks = 1, numAggregator = 0, stride = 1, base = 0
  integer :: ncid
  character*(*) FILE_NAME
  parameter (FILE_NAME='ftst_pio.nc')
  integer :: ierr

  call MPI_Init(ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, myRank, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, ntasks, ierr)

  ierr = pio_set_log_level(2)
  ierr = nf_set_log_level(2)
  call nf_init_intracom(myRank, MPI_COMM_WORLD, niotasks, numAggregator, &
       stride, PIO_rearr_subset, ioSystem, base)

  ierr = nf_create(FILE_NAME, 64, ncid)
  ierr = nf_close(ncid)

  ierr = nf_free_iosystem()
  call MPI_Finalize(ierr)
  if (myRank .eq. 0) then
     print *, '*** SUCCESS running ftst_pio!'
  endif
end program ftst_pio
