#include "config.h"
!>
!! @file
!! These are the extra functions added to support netCDF
!! integration. In most cases these functions are wrappers for
!! existing PIO_ functions, but with names that start with nf_.
!!
!! @author Ed Hartnett
!<

!>
!! @defgroup PIO_ncint NetCDF Integration
!! Integrate netCDF and PIO code.
!!
module ncint_mod
  use iso_c_binding
  !--------------
  use pio_kinds
  !--------------
  use pio_types, only : file_desc_t, iosystem_desc_t, var_desc_t, io_desc_t, &
       pio_iotype_netcdf, pio_iotype_pnetcdf, pio_iotype_netcdf4p, pio_iotype_netcdf4c, &
       pio_noerr, pio_rearr_subset, pio_rearr_opt_t
  !--------------
  use pio_support, only : piodie, debug, debugio, debugasync, checkmpireturn
  use pio_nf, only : pio_set_log_level
  use piolib_mod, only : pio_init, pio_finalize
  !

#ifndef NO_MPIMOD
  use mpi    ! _EXTERNAL
#endif
  implicit none
  private
#ifdef NO_MPIMOD
  include 'mpif.h'    ! _EXTERNAL
#endif
  ! !public member functions:

  public :: nf_init_intracom, nf_free_iosystem

  interface nf_init_intracom
     module procedure nf_init_intracom
  end interface nf_init_intracom

  !>
  !! Shuts down an IOSystem and associated resources.
  !<
  interface nf_free_iosystem
     module procedure nf_free_iosystem
  end interface nf_free_iosystem

contains

  !>
  !! @public
  !! @ingroup PIO_init
  !! Initialize the pio subsystem. This is a collective call. Input
  !! parameters are read on comp_rank=0 values on other tasks are
  !! ignored. This variation of PIO_init locates the IO tasks on a
  !! subset of the compute tasks.
  !!
  !! @param comp_rank mpi rank of each participating task,
  !! @param comp_comm the mpi communicator which defines the
  !! collective.
  !! @param num_iotasks the number of iotasks to define.
  !! @param num_aggregator the mpi aggregator count
  !! @param stride the stride in the mpi rank between io tasks.
  !! @param rearr @copydoc PIO_rearr_method
  !! @param iosystem a derived type which can be used in subsequent
  !! pio operations (defined in PIO_types).
  !! @param base @em optional argument can be used to offset the first
  !! io task - default base is task 1.
  !! @param rearr_opts the rearranger options.
  !! @author Ed Hartnett
  !<
  subroutine nf_init_intracom(comp_rank, comp_comm, num_iotasks, &
       num_aggregator, stride,  rearr, iosystem, base, rearr_opts)
    use pio_types, only : pio_internal_error, pio_rearr_opt_t
    use iso_c_binding

    integer(i4), intent(in) :: comp_rank
    integer(i4), intent(in) :: comp_comm
    integer(i4), intent(in) :: num_iotasks
    integer(i4), intent(in) :: num_aggregator
    integer(i4), intent(in) :: stride
    integer(i4), intent(in) :: rearr
    type (iosystem_desc_t), intent(out)  :: iosystem  ! io descriptor to initalize
    integer(i4), intent(in),optional :: base
    type (pio_rearr_opt_t), intent(in), optional :: rearr_opts
    integer :: ierr

    interface
       integer(C_INT) function nc_set_iosystem(iosystemid) &
            bind(C,name="nc_set_iosystem")
         use iso_c_binding
         integer(C_INT), intent(in), value :: iosystemid
       end function nc_set_iosystem
    end interface

    call PIO_init(comp_rank, comp_comm, num_iotasks, num_aggregator, &
         stride,  rearr, iosystem, base, rearr_opts)

    ierr = nc_set_iosystem(iosystem%iosysid)

  end subroutine nf_init_intracom

  !>
  !! @public
  !! @ingroup PIO_finalize
  !! Finalizes an IO System. This is a collective call.
  !!
  !! @param iosystem @copydoc io_desc_t
  !! @retval ierr @copydoc error_return
  !! @author Ed Hartnett
  !<
  subroutine nf_free_iosystem(iosystem, ierr)
    type (iosystem_desc_t), intent(inout) :: iosystem
    integer(i4), intent(out) :: ierr
    call PIO_finalize(iosystem, ierr)
  end subroutine nf_free_iosystem

end module ncint_mod
