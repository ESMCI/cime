!> This is a test program for the Fortran API use of the netCDF
!! integration layer.
!!
!! @author Ed Hartnett, 7/19/19

program ftst_pio
  use pio
  implicit none
  include 'mpif.h'
  include 'netcdf.inc'

  integer :: myRank, ntasks
  integer :: niotasks = 1, numAggregator = 0, stride = 1, base = 0
  integer :: ncid
  character*(*) FILE_NAME
  parameter (FILE_NAME = 'ftst_pio.nc')
  integer(kind = PIO_OFFSET_KIND), dimension(3) :: data_buffer, compdof
  integer, dimension(1) :: dims
  integer, dimension(3) :: var_dims
  integer :: decompid, iosysid
  integer :: NDIMS, NRECS
  parameter (NDIMS = 4, NRECS = 2)
  integer NLATS, NLONS
  parameter (NLATS = 6, NLONS = 12)
  character*(*) LAT_NAME, LON_NAME, REC_NAME
  parameter (LAT_NAME = 'latitude', LON_NAME = 'longitude', REC_NAME = 'time')
  integer :: lon_dimid, lat_dimid, rec_dimid
  integer :: ierr

  ! Set up MPI.
  call MPI_Init(ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, myRank, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, ntasks, ierr)

  ! These control logging in the PIO and netCDF libraries.
  ierr = pio_set_log_level(3)
  ierr = nf_set_log_level(2)
  if (ierr .ne. nf_noerr) call handle_err(ierr)

  ! Define an IOSystem.
  ierr = nf_def_iosystem(myRank, MPI_COMM_WORLD, niotasks, numAggregator, &
       stride, PIO_rearr_subset, iosysid, base)

  ! Define a decomposition.
  dims(1) = 3 * ntasks
  compdof = 3 * myRank + (/1, 2, 3/)  ! Where in the global array each task writes
  ierr = nf_def_decomp(iosysid, PIO_int, dims, compdof, decompid)

  ! Create a file.
  ierr = nf_create(FILE_NAME, 64, ncid)

  ! Define dimensions.
  ierr = nf_def_dim(ncid, LAT_NAME, NLATS, lat_dimid)
  ierr = nf_def_dim(ncid, LON_NAME, NLONS, lon_dimid)
  ierr = nf_def_dim(ncid, REC_NAME, NF_UNLIMITED, rec_dimid)

  data_buffer = myRank

  ! Close the file.
  ierr = nf_close(ncid)

  ! Free resources.
  ierr = nf_free_decomp(decompid)
  ierr = nf_free_iosystem()

  ! We're done!
  call MPI_Finalize(ierr)
  if (myRank .eq. 0) then
     print *, '*** SUCCESS running ftst_pio!'
  endif
end program ftst_pio

subroutine handle_err(errcode)
  implicit none
  include 'netcdf.inc'
  integer errcode

  print *, 'Error: ', nf_strerror(errcode)
  stop 2
end subroutine handle_err
