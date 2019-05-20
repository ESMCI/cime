!>
!! @file
!! @brief Derived datatypes and constants for PIO Fortran API
!!
!<
module pio_types
    use pio_kinds
    use iso_c_binding
    implicit none
    private
    !-------------------------------------------
    !  data structure to describe decomposition
    !-------------------------------------------
    type, public :: DecompMap_t
#ifdef SEQUENCE
        sequence
#endif
        integer(i4) :: start  !< start
        integer(i4) :: length !< length
    end type

    !------------------------------------
    !  a file descriptor data structure
    !------------------------------------
!>
!! @public
!! @struct iosystem_desc_t
!! @brief A defined PIO system descriptor created by @ref PIO_init (see pio_types)
!<
    type, public :: IOSystem_desc_t
        integer(kind=c_int) :: iosysid = -1 !< iosysid
     end type IOSystem_desc_t

!>
!! @private
!! @struct io_data_list
!! @brief Linked list of buffers for pnetcdf non-blocking interface
!>
!    type, public :: io_data_list
!       integer :: request
!       real(r4), pointer :: data_real(:) => null()
!       integer(i4), pointer :: data_int(:) => null()
!       real(r8), pointer :: data_double(:) => null()
!       type(io_data_list), pointer :: next => null()
!    end type io_data_list


!>
!! @public
!! @struct file_desc_t
!! @brief File descriptor returned by \ref PIO_openfile or \ref PIO_createfile (see pio_types)
!!
!>
    type, public :: File_desc_t
       integer(kind=c_int) :: fh !< file handle
       type(iosystem_desc_t), pointer :: iosystem => null() !< iosystem
    end type File_desc_t


!>
!! @private
!! @defgroup iodesc_generate io descriptors, generating
!! @brief The io descriptor structure in defined in this subroutine
!! and subsequently used in @ref PIO_read_darray, @ref PIO_write_darray,
!! @ref PIO_put_var, @ref PIO_get_var calls (see pio_types).
!<

!>
!! @public
!! @struct io_desc_t
!! @brief  An io descriptor handle that is generated in @ref PIO_initdecomp
!! (see pio_types)
!<
   type, public :: io_desc_t
#ifdef SEQUENCE
        sequence
#endif
        integer(i4)         :: ioid !< decomposition id
    end type

!>
!! @public
!! @struct var_desc_t
!! @brief A variable descriptor returned from @ref PIO_def_var (see pio_types)
!<
    type, public :: Var_desc_t
#ifdef SEQUENCE
       sequence
#endif
       integer(i4) :: varID !< variable id
       integer(i4) :: ncid  !< file id
    end type Var_desc_t

!>
!! @defgroup PIO_iotype PIO_iotype
!! @public
!! @brief An integer parameter which controls the iotype
!! @details
!!   - PIO_iotype_pnetcdf : parallel read/write of pNetCDF files (netcdf3)
!!   - PIO_iotype_netcdf : serial read/write of NetCDF files using 'base_node' (netcdf3)
!!   - PIO_iotype_netcdf4c : parallel read/serial write of NetCDF4 (HDF5) files with data compression
!!   - PIO_iotype_netcdf4p : parallel read/write of NETCDF4 (HDF5) files
!>
    integer(i4), public, parameter ::  &
        PIO_iotype_pnetcdf = 1, &   !< parallel read/write of pNetCDF files
        PIO_iotype_netcdf  = 2, &   !< serial read/write of NetCDF file using 'base_node'
        PIO_iotype_netcdf4c = 3, &  !< netcdf4 (hdf5 format) file opened for compression (serial write access only)
        PIO_iotype_netcdf4p = 4     !< netcdf4 (hdf5 format) file opened in parallel (all netcdf4 files for read will be opened this way)


! These are for backward compatability and should not be used or expanded upon
    integer(i4), public, parameter ::                       &
        iotype_pnetcdf = PIO_iotype_pnetcdf,                & !< pnetcdf iotype
        iotype_netcdf  = PIO_iotype_netcdf                    !< netcdf iotype


!>
!! @defgroup PIO_rearr_method PIO_rearr_method
!! @public
!! @brief The three choices to control rearrangement are:
!! @details
!!  - PIO_rearr_none : Do not use any form of rearrangement
!!  - PIO_rearr_box : Use a PIO internal box rearrangement
!!  - PIO_rearr_subset : Use a PIO internal subsetting rearrangement
!<
    integer(i4), public, parameter :: PIO_rearr_box =  1    !< box rearranger
    integer(i4), public, parameter :: PIO_rearr_subset =  2 !< subset rearranger

!>
!! @public
!! @defgroup PIO_error_method error_methods
!! @details
!! The three types of error handling methods are:
!!  - PIO_INTERNAL_ERROR  : abort on error from any task
!!  - PIO_BCAST_ERROR     : broadcast an error from io_rank 0 to all tasks in comm
!!  - PIO_RETURN_ERROR    : do nothing - allow the user to handle it
!<
  integer(i4), public, parameter :: PIO_INTERNAL_ERROR = -51 !< abort on error from any task
  integer(i4), public, parameter :: PIO_BCAST_ERROR = -52    !< broadcast an error
  integer(i4), public, parameter :: PIO_RETURN_ERROR = -53   !< do nothing

!>
!! @public
!! @defgroup PIO_error_method error_methods
!! @details
!! Use this instead of ios to set error handling for the library.
!<
  integer(i4), public, parameter :: PIO_DEFAULT = -1 !< default error handler

!>
!! @public
!! @defgroup error_return error return codes
!! @brief : The error return code; ierr != PIO_noerr indicates
!! an error. (see @ref PIO_seterrorhandling )
!>

!>
!! @struct use_PIO_kinds
!! @brief The type of variable(s) associated with this iodesc.
!! @copydoc PIO_kinds
!<

!>
!! @public
!! @defgroup PIO_kinds PIO_kinds
!! @brief The base types supported by PIO are:
!! @details
!!  - PIO_double : 8-byte reals or double precision
!!  - PIO_real : 4-byte reals
!!  - PIO_int :  4-byte integers
!!  - PIO_char : character
!<
#ifdef _PNETCDF
#include <pnetcdf.inc>   /* _EXTERNAL */
   integer, public, parameter :: PIO_global = nf_global       !< global atts
   integer, public, parameter :: PIO_unlimited = nf_unlimited !< unlimited dimension
   integer, public, parameter :: PIO_double = nf_double       !< double type
   integer, public, parameter :: PIO_real   = nf_real         !< real type
   integer, public, parameter :: PIO_int    = nf_int          !< int type
   integer, public, parameter :: PIO_char   = nf_char         !< char type
   integer, public, parameter :: PIO_noerr  = nf_noerr        !< no error
   integer, public, parameter :: PIO_WRITE  = nf_write        !< read-write
   integer, public, parameter :: PIO_nowrite  = nf_nowrite    !< read-only
   integer, public, parameter :: PIO_CLOBBER = nf_clobber     !< clobber existing file
   integer, public, parameter :: PIO_NOCLOBBER = nf_NOclobber !< do not clobber existing file
   integer, public, parameter :: PIO_NOFILL = nf_nofill       !< do not use fill values
   integer, public, parameter :: PIO_MAX_NAME = nf_max_name   !< max name len
   integer, public, parameter :: PIO_MAX_VAR_DIMS = min(6,nf_max_var_dims) !< max dims for a var
   integer, public, parameter :: PIO_64BIT_OFFSET = nf_64bit_offset        !< 64bit offset format
   integer, public, parameter :: PIO_64BIT_DATA = nf_64bit_data            !< CDF5 format
   integer, public, parameter :: PIO_FILL_INT = nf_fill_int;               !< int fill value
   real, public, parameter :: PIO_FILL_FLOAT = nf_fill_float;              !< float fill value
   double precision, public, parameter :: PIO_FILL_DOUBLE = nf_fill_double; !< double fill value

#else
#ifdef _NETCDF
#include <netcdf.inc>   /* _EXTERNAL */
   integer, public, parameter :: PIO_global = nf_global       !< global atts
   integer, public, parameter :: PIO_unlimited = nf_unlimited !< unlimited dimension
   integer, public, parameter :: PIO_double = nf_double       !< double type
   integer, public, parameter :: PIO_real   = nf_real         !< real type
   integer, public, parameter :: PIO_int    = nf_int          !< int type
   integer, public, parameter :: PIO_char   = nf_char         !< char type
   integer, public, parameter :: PIO_noerr  = nf_noerr        !< no error
   integer, public, parameter :: PIO_WRITE  = nf_write        !< read-write
   integer, public, parameter :: PIO_nowrite = nf_nowrite     !< read-only
   integer, public, parameter :: PIO_CLOBBER = nf_clobber     !< clobber existing file
   integer, public, parameter :: PIO_NOCLOBBER = nf_NOclobber !< do not clobber existing file
   integer, public, parameter :: PIO_NOFILL = nf_nofill       !< do not use fill values
   integer, public, parameter :: PIO_MAX_NAME = nf_max_name   !< max name len
   integer, public, parameter :: PIO_MAX_VAR_DIMS = min(6,nf_max_var_dims) !< max dims for a var
   integer, public, parameter :: PIO_64BIT_OFFSET = nf_64bit_offset        !< 64bit offset format
   integer, public, parameter :: PIO_64BIT_DATA = 0                        !< CDF5 format
   integer, public, parameter :: PIO_FILL_INT = nf_fill_int;               !< int fill value
   real, public, parameter :: PIO_FILL_FLOAT = nf_fill_float;              !< float fill value
   double precision, public, parameter :: PIO_FILL_DOUBLE = nf_fill_double; !< double fill value
#else
   integer, public, parameter :: PIO_global = 0  !< global atts
   integer, public, parameter :: PIO_double = 6  !< double type
   integer, public, parameter :: PIO_real   = 5  !< real type
   integer, public, parameter :: PIO_int    = 4  !< int type
   integer, public, parameter :: PIO_char   = 2  !< char type
   integer, public, parameter :: PIO_noerr  = 0  !< no error
   integer, public, parameter :: PIO_MAX_NAME = 25    !< max name len
   integer, public, parameter :: PIO_MAX_VAR_DIMS = 6 !< max dims for a var
   integer, public, parameter :: PIO_CLOBBER = 10     !< clobber existing file
   integer, public, parameter :: PIO_NOCLOBBER = 11   !< do not clobber existing file
   integer, public, parameter :: PIO_WRITE = 20       !< read-write
   integer, public, parameter :: PIO_NOWRITE = 21     !< read-only
   integer, public, parameter :: PIO_64BIT_OFFSET = 0 !< 64bit offset format
   integer, public, parameter :: PIO_64BIT_DATA = 0   !< CDF5 format
   integer, public, parameter :: PIO_FILL_INT = -2147483647;  !< int fill value
   real, public, parameter :: PIO_FILL_FLOAT =  9.9692099683868690e+36; !< float fill value
   double precision, public, parameter :: PIO_FILL_DOUBLE = 9.9692099683868690e+36; !< double fill value
#endif
#endif
   integer, public, parameter :: PIO_num_OST =  16 !< num ost

!>
!! @defgroup PIO_rearr_comm_t PIO_rearr_comm_t
!! @public
!! @brief The two choices for rearranger communication
!! @details
!!  - PIO_rearr_comm_p2p : Point to point
!!  - PIO_rearr_comm_coll : Collective
!>
    enum, bind(c)
      enumerator :: PIO_rearr_comm_p2p = 0
      enumerator :: PIO_rearr_comm_coll
    end enum

!>
!! @defgroup PIO_rearr_comm_dir PIO_rearr_comm_dir
!! @public
!! @brief The four choices for rearranger communication direction
!! @details
!!  - PIO_rearr_comm_fc_2d_enable : COMM procs to IO procs and vice versa
!!  - PIO_rearr_comm_fc_1d_comp2io: COMM procs to IO procs only
!!  - PIO_rearr_comm_fc_1d_io2comp: IO procs to COMM procs only
!!  - PIO_rearr_comm_fc_2d_disable: Disable flow control
!>
    enum, bind(c)
      enumerator :: PIO_rearr_comm_fc_2d_enable = 0
      enumerator :: PIO_rearr_comm_fc_1d_comp2io
      enumerator :: PIO_rearr_comm_fc_1d_io2comp
      enumerator :: PIO_rearr_comm_fc_2d_disable
    end enum

!>
!! @defgroup PIO_rearr_comm_fc_options PIO_rearr_comm_fc_options
!! @brief Type that defines the PIO rearranger options
!! @details
!!  - enable_hs : Enable handshake (true/false)
!!  - enable_isend : Enable Isends (true/false)
!!  - max_pend_req : Maximum pending requests (To indicated unlimited
!!                    number of requests use PIO_REARR_COMM_UNLIMITED_PEND_REQ)
!>
   type, bind(c), public :: PIO_rearr_comm_fc_opt_t
      logical(c_bool) :: enable_hs            !< Enable handshake?
      logical(c_bool) :: enable_isend         !< Enable isends?
      integer(c_int) :: max_pend_req          !< Maximum pending requests
    end type PIO_rearr_comm_fc_opt_t

    integer, public, parameter :: PIO_REARR_COMM_UNLIMITED_PEND_REQ = -1 !< unlimited requests
!>
!! @defgroup PIO_rearr_options PIO_rearr_options
!! @brief Type that defines the PIO rearranger options
!! @details
!!  - comm_type : @copydoc PIO_rearr_comm_t
!!  - fcd : @copydoc PIO_rearr_comm_dir
!!  - comm_fc_opts_comp2io : @copydoc PIO_rearr_comm_fc_options
!!  - comm_fc_opts_io2comp : @copydoc PIO_rearr_comm_fc_options
!>
    type, bind(c), public :: PIO_rearr_opt_t
      integer(c_int)                         :: comm_type !< comm type
      integer(c_int)                         :: fcd       !< Flow control direction
      type(PIO_rearr_comm_fc_opt_t)   :: comm_fc_opts_comp2io !< comp2io
      type(PIO_rearr_comm_fc_opt_t)   :: comm_fc_opts_io2comp !< io2comp
    end type PIO_rearr_opt_t

    public :: PIO_rearr_comm_p2p, PIO_rearr_comm_coll,&
              PIO_rearr_comm_fc_2d_enable, PIO_rearr_comm_fc_1d_comp2io,&
              PIO_rearr_comm_fc_1d_io2comp, PIO_rearr_comm_fc_2d_disable

end module pio_types
