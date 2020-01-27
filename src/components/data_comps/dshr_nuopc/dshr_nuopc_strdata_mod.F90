module dshr_nuopc_strdata_mod

  ! holds data and methods to advance data models

  use ESMF
  use shr_const_mod         , only : SHR_CONST_PI
  use shr_kind_mod          , only : in=>shr_kind_in, r8=>shr_kind_r8, cs=>shr_kind_cs, cl=>shr_kind_cl, cxx=>shr_kind_cxx
  use shr_sys_mod           , only : shr_sys_abort, shr_sys_flush
  use shr_mpi_mod           , only : shr_mpi_bcast
  use shr_file_mod          , only : shr_file_getunit, shr_file_freeunit
  use shr_log_mod           , only : logunit => shr_log_Unit
  use shr_cal_mod           , only : shr_cal_calendarname, shr_cal_timeSet
  use shr_cal_mod           , only : shr_cal_noleap, shr_cal_gregorian
  use shr_cal_mod           , only : shr_cal_date2ymd, shr_cal_ymd2date
  use shr_orb_mod           , only : shr_orb_decl, shr_orb_cosz, shr_orb_undef_real
  use shr_nl_mod            , only : shr_nl_find_group_name
  use shr_mpi_mod           , only : shr_mpi_bcast
  use shr_const_mod         , only : shr_const_cDay
  use shr_string_mod        , only : shr_string_listGetNum, shr_string_listGetName
  use shr_tinterp_mod
  use dshr_nuopc_stream_mod , only : shr_stream_streamType
  use dshr_nuopc_stream_mod , only : dshr_nuopc_stream_findBounds
  use dshr_nuopc_stream_mod , only : dshr_nuopc_stream_getFilePath
  use dshr_nuopc_stream_mod , only : dshr_nuopc_stream_getPrevFileName
  use dshr_nuopc_stream_mod , only : dshr_nuopc_stream_getNextFileName
  use dshr_nuopc_stream_mod , only : dshr_nuopc_stream_getFileFieldName
  use dshr_nuopc_stream_mod , only : dshr_nuopc_stream_getModelFieldList
  use dshr_nuopc_stream_mod , only : dshr_nuopc_stream_getCurrFile
  use dshr_nuopc_stream_mod , only : dshr_nuopc_stream_setCurrFile
  use dshr_nuopc_stream_mod ! stream data type and methods
  use perf_mod       ! timing
  use pio            ! pio

  implicit none
  private

  ! !PUBLIC TYPES:
  public shr_strdata_type

  ! !PUBLIC MEMBER FUNCTIONS:
  public ::  dshr_nuopc_strdata_init
  public ::  dshr_nuopc_strdata_readnml
  public ::  dshr_nuopc_strdata_setOrbs
  public ::  dshr_nuopc_strdata_advance
  public ::  dshr_nuopc_strdata_restRead
  public ::  dshr_nuopc_strdata_restWrite

  private :: dshr_nuopc_strdata_print
  private :: dshr_nuopc_strdata_readLBUB
  private :: dshr_nuopc_strdata_readstrm
  !private :: dshr_nuopc_strdata_readstrm_fullfile ! TODO: implememnt this
  private :: dshr_nuopc_strdata_meshCompare

  ! !PRIVATE:
  integer                              :: debug    = 0  ! local debug flag
  integer          ,parameter          :: nStrMax = 30
  integer          ,parameter          :: nVecMax = 30
  character(len=*) ,parameter, public  :: shr_strdata_nullstr = 'null'
  character(len=*) ,parameter          :: shr_strdata_unset = 'NOT_SET'
  real(R8)         ,parameter, private :: dtlimit_default = 1.5_R8

  integer , public, parameter :: nmappers       = 8
  integer , public, parameter :: mapunset       = 0
  integer , public, parameter :: mapbilnr       = 1
  integer , public, parameter :: mapconsf       = 2
  integer , public, parameter :: mapconsd       = 3
  integer , public, parameter :: mappatch       = 4
  integer , public, parameter :: mapfcopy       = 5
  integer , public, parameter :: mapnstod       = 6 ! nearest source to destination
  integer , public, parameter :: mapnstod_consd = 7 ! nearest source to destination followed by conservative dst
  integer , public, parameter :: mapnstod_consf = 8 ! nearest source to destination followed by conservative frac
  character(len=*) , public, parameter :: mapnames(nmappers) = & 
       (/'bilinear   ','consf      ','consd      ',&
         'patch      ','fcopy      ','nstod      ',&
         'nstod_consd','nstod_consf'/)

  type shr_strdata_type

     ! namelist dependent input (shr_strdata_nml)
     integer                        :: nstreams          ! actual number of streams (set in 
     character(CL)                  :: dataMode          ! flags physics options wrt input data
     character(CL)                  :: streams (nStrMax) ! stream description file names
     character(CL)                  :: tintalgo(nStrMax) ! time interpolation algorithm
     character(CL)                  :: taxMode (nStrMax) ! time axis cycling mode
     real(R8)                       :: dtlimit (nStrMax) ! dt max/min limit
     character(CL)                  :: vectors (nVecMax) ! define vectors to vector map
     character(CL)                  :: fillalgo(nStrMax) ! fill algorithm
     character(CL)                  :: fillmask(nStrMax) ! fill mask
     character(CL)                  :: mapalgo (nStrMax) ! scalar map algorithm
     character(CL)                  :: mapmask (nStrMax) ! 
     character(CL)                  :: readmode(nStrMax) ! file read mode
     character(CL)                  :: mapread (nStrMax) ! NOT USED 
     character(CL)                  :: mapwrit (nStrMax) ! NOT USED
     character(CL)                  :: fillread(nStrMax) ! NOT USED
     character(CL)                  :: fillwrit(nStrMax) ! NOT USED
     ! stream info
     type(shr_stream_streamType)    :: stream(nStrMax)
     ! pio settings
     integer                        :: io_type
     integer                        :: io_format
     type(iosystem_desc_t), pointer :: pio_subsystem => null()
     type(io_desc_t)                :: pio_iodesc(nStrMax)
     ! set in call to shr_strdata_setorbs (data required by stream  cosz t-interp method)
     real(R8)                       :: eccen
     real(R8)                       :: mvelpp
     real(R8)                       :: lambm0
     real(R8)                       :: obliqr
     integer                        :: modeldt                          ! model dt in seconds
     ! model mesh and stream meshes
     type(ESMF_Mesh)                :: mesh_model                       ! model mesh
     type(ESMF_Mesh)                :: mesh_stream(nStrnMax)            ! mesh for each stream
     ! stream field bundles
     type(ESMF_FieldBundle)         :: FB_stream_alltimes(nstrMax)      ! stream n containing all time slices for stream
     type(ESMF_FieldBundle)         :: FB_stream_lbound(nstrMax)    ! stream n containing lb of time period (on stream grid)
     type(ESMF_FieldBundle)         :: FB_stream_ubound(nstrMax)    ! stream n containing lb of time period (on stream grid)
     type(ESMF_FieldBundle)         :: FB_model_lbound(nstrMax)     ! stream n containing lb of time period (on model grid)
     type(ESMF_FieldBundle)         :: FB_model_ubound(nstrMax)     ! stream n containing lb of time period (on model grid)
     type(ESMF_FieldBundle)         :: FB_model(nStrMax)                ! time and spatially interpolated streams to model grid
     type(ESMF_RouteHandle)         :: RH_map(nstrMax)                  ! stream n -> model mesh mapping
     type(ESMF_RouteHandle)         :: RH_fill(nstrMax)                 ! stream n - nn fill where mask is 0
     ! mapping and fill route handes
     type(ESMF_RouteHandle)         :: routehandle_fill(nStrMax)        ! mapping weights for fill for stream n -> stream n
     type(ESMF_RouteHandle)         :: routehandle_map(ntypes, nStrMax) ! mapping weights for fill for stream n -> model grid
     ! stream info needed for spatial interpolation
     integer                        :: nvectors                         ! number of vectors
     integer                        :: ustrm (nVecMax)
     integer                        :: vstrm (nVecMax)
     character(CL)                  :: allocstring = 'strdata_allocated'
     ! stream info for time interpolation
     type(ESMF_Field)               :: field_coszen(nStrMax)            ! needed for coszen time interp 
     integer                        :: ymdLB(nStrMax)
     integer                        :: todLB(nStrMax)
     integer                        :: ymdUB(nStrMax)
     integer                        :: todUB(nStrMax)
     real(R8)                       :: dtmin(nStrMax)
     real(R8)                       :: dtmax(nStrMax)
     integer                        :: ymd  ,tod
     character(CL)                  :: calendar          ! model calendar for ymd,tod
  end type shr_strdata_type

  integer ,parameter,public :: CompareXYabs      = 1 ! X,Y  relative error
  integer ,parameter,public :: CompareXYrel      = 2 ! X,Y  absolute error
  integer ,parameter,public :: CompareAreaAbs    = 3 ! area relative error
  integer ,parameter,public :: CompareAreaRel    = 4 ! area absolute error
  integer ,parameter,public :: CompareMaskIdent  = 5 ! masks are identical
  integer ,parameter,public :: CompareMaskZeros  = 6 ! masks have same zeros
  integer ,parameter,public :: CompareMaskSubset = 7 ! mask is subset of other

  real(R8),parameter,private :: deg2rad = SHR_CONST_PI/180.0_R8

!===============================================================================
contains
!===============================================================================

  subroutine dshr_nuopc_strdata_init(gcomp, mesh_file, sdat, mesh_model, reset_domain_mask, compid, mpicom, my_task, rc) 

    ! Note: for the variable strdata_domain_fracname_from_stream:
    ! This variable is applicable for data models that read the model domain from the
    ! domain of the first stream; it is an error to provide this variable in other
    ! situations. If present, then we read the data model's domain fraction from the
    ! first stream file, and this variable provides the name of the frac field on this
    ! file. If absent, then (if we are taking the model domain from the domain of the
    ! first stream) we do not read a frac field, and instead we set frac to 1 wherever
    ! mask is 1, and set frac to 0 wherever mask is 0.
    ! BUG(wjs, 2018-05-01, ESMCI/cime#2515) Ideally we'd like to get this frac variable
    ! name in a more general and robust way; see comments in that issue for more details.

    use shr_pio_mod, only: shr_pio_getiosys, shr_pio_getiotype, shr_pio_getioformat

    ! input/output variables
    type(shr_strdata_type),intent(inout) :: sdat
    type(ESMF_Mesh)       ,intent(in)    :: mesh
    logical, optional     ,intent(in)    :: reset_domain_mask
    integer               ,intent(in)    :: compid
    integer               ,intent(in)    :: mpicom
    integer               ,intent(in)    :: my_task
    integer               ,intent(out)   :: rc 

    ! local variables
    integer                     :: n,m,k    ! generic index
    character(CL)               :: filePath ! generic file path
    character(CL)               :: fileName ! generic file name
    character(CS)               :: timeName ! domain file: time variable name
    character(CS)               :: lonName  ! domain file: lon  variable name
    character(CS)               :: latName  ! domain file: lat  variable name
    character(CS)               :: hgtName  ! domain file: hgt  variable name
    character(CS)               :: maskName ! domain file: mask variable name
    character(CS)               :: areaName ! domain file: area variable name
    integer                     :: nfiles
    character(CL)               :: localFn ! name of acquired file
    character(CXX)              :: fldList ! list of fields
    character(CS)               :: uname   ! u vector field name
    character(CS)               :: vname   ! v vector field name
    type(ESMF_Field) :: lfield_src
    type(ESMF_Field) :: lfield_dst
    integer          ,pointer   :: dof(:)
    integer          ,parameter :: master_task = 0
    character(*)     ,parameter :: F00 = "('(shr_strdata_init_mapping) ',8a)"
    character(len=*) ,parameter :: subname = "(shr_strdata_init_mapping) "
    character(*)     ,parameter :: F00 = "('(shr_strdata_init) ',8a)"
    integer         , parameter :: master_task = 0
    character(len=*), parameter :: subname = "(shr_strdata_init) "
    !-------------------------------------------------------------------------------

    rc = ESMF_SUCCESS

    ! ------------------------------------
    ! Determine the model mesh
    ! ------------------------------------

    ! TODO: pass in the nuopc attribute and the domain name as arguments here
    if (trim(mesh_filename) == 'create_mesh') then
       call NUOPC_CompAttributeGet(gcomp, name='mesh_atm', value=filename, rc=rc)
       if (ChkErr(rc,__LINE__,u_FILE_u)) return
       ! get the datm grid from the domain file
       call NUOPC_CompAttributeGet(gcomp, name='domain_atm', value=filename, rc=rc)
       if (ChkErr(rc,__LINE__,u_FILE_u)) return
       call dshr_create_mesh_from_grid(trim(domain_filename), sdat%mesh, rc=rc)
       if (ChkErr(rc,__LINE__,u_FILE_u)) return
    else
       sdat%mesh = ESMF_MeshCreate(trim(filename), fileformat=ESMF_FILEFORMAT_ESMFMESH, rc=rc)
       if (ChkErr(rc,__LINE__,u_FILE_u)) return
    end if
    if (my_task == master_task) then
       write(logunit,*) trim(subname)// " obtaining datm mesh from " // trim(filename)
    end if

    ! TODO: With ESMF cannot read the model domain from the stream data

    ! TODO: With ESMF - how can you reset the domain mask and fraction as is done for aqua-planet - and
    ! why will this matter - can this be done in the cap and is not even needed here?

    ! if (present(reset_domain_mask)) then
    !    if (reset_domain_mask) then
    !       if (my_task == master_task) write(logunit,F00) ' Resetting the component domain mask and frac to 1'
    !       kmask = mct_aVect_indexRA(sdat%grid%data,'mask')
    !       sdat%grid%data%rattr(kmask,:) = 1
    !       kfrac = mct_aVect_indexRA(sdat%grid%data,'frac')
    !       sdat%grid%data%rattr(kfrac,:) = 1.0_r8
    !    end if
    ! end if

    ! ------------------------------------
    ! Update sdat streams info - assumes that readnml has already been called for the shr_strdata namelist
    ! ------------------------------------

    if (my_task == master_task) then

       do n=1,nStrMax
          ! Determine the number of streams
          if (trim(sdat%streams(n)) /= trim(shr_strdata_nullstr)) then
             sdat%nstreams = max(sdat%nstreams,n)
          end if

          ! check if a filename is defined in the stream
          call dshr_nuopc_stream_getNFiles(sdat%stream(n), nfiles)
          if (nfiles > 0) then
             sdat%nstreams = max(sdat%nstreams,n)
          end if
          if (trim(sdat%taxMode(n)) == trim(shr_stream_taxis_extend)) then
             sdat%dtlimit(n) = 1.0e30
          end if
       end do

       sdat%nvectors = 0
       do n=1,nVecMax
          if (trim(sdat%vectors(n)) /= trim(shr_strdata_nullstr)) then
             sdat%nvectors = n
          end if
       end do
    endif
    call shr_mpi_bcast(sdat%nstreams  ,mpicom,'nstreams')
    call shr_mpi_bcast(sdat%nvectors  ,mpicom,'nvectors')
    call shr_mpi_bcast(sdat%dtlimit   ,mpicom,'dtlimit')

    ! ------------------------------------
    ! Initialize sdat PIO 
    ! ------------------------------------

    sdat%pio_subsystem => shr_pio_getiosys(compid)
    sdat%io_type       =  shr_pio_getiotype(compid)
    sdat%io_format     =  shr_pio_getioformat(compid)

    ! ------------------------------------
    ! Loop through the streams
    ! ------------------------------------

    do n = 1,sdat%nstreams
       
       ! ------------------------------------
       ! Create the stream mesh
       ! ------------------------------------

       if (my_task == master_task) then
          call dshr_nuopc_stream_getDomainInfo(sdat%stream(n), filePath, fileName, timeName)
          stream_grid_file = trim(filePath)//adjustl(fileName)
       endif

       ! Assume for now that the stream_grid_file is in SCRIP format
       call shr_mpi_bcast(stream_grid_file, mpicom)
       grid_stream = ESMF_GridCreate(stream_grid_file, fileformat=ESMF_FILEFORMAT_SCRIP, rc=rc)
       if (ChkErr(rc,__LINE__,u_FILE_u)) return
       mesh_stream =  ESMF_MeshCreate(grid_stream, rc=rc)
       if (ChkErr(rc,__LINE__,u_FILE_u)) return

       ! TODO: how can we access the mask and fraction here?
       ! TODO: what to do witht the mask here?

       ! ------------------------------------
       ! Initialize the stream pio decomp - use the stream mesh distgrid 
       ! ------------------------------------

       call ESMF_DistGridGet(distgrid, dimCount=dimCount, tileCount=tileCount, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return
       allocate(minIndexPTile(dimCount, tileCount), maxIndexPTile(dimCount, tileCount))
       call ESMF_DistGridGet(distgrid, minIndexPTile=minIndexPTile, maxIndexPTile=maxIndexPTile, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return
       lnx = maxval(maxIndexPTile)
       lny = 1

       call ESMF_DistGridGet(distgrid, localDE=0, elementCount=ns, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return
       allocate(dof(ns))
       call ESMF_DistGridGet(distgrid, localDE=0, seqIndexList=dof, rc=rc)
       write(tmpstr,*) subname,' dof = ',ns, size(dof), dof(1), dof(ns)  !,minval(dof),maxval(dof)
       call ESMF_LogWrite(trim(tmpstr), ESMF_LOGMSG_INFO)
       call pio_initdecomp(sdat%pio_subsystem, pio_double, (/sdat%strnxg(n),sdat%strnyg(n)/), dof, sdat%pio_iodesc(n))
       deallocate(dof)

       ! ------------------------------------
       ! broadcast the stream calendar
       ! ------------------------------------

       call shr_mpi_bcast(sdat%stream(n)%calendar, mpicom)

       ! ------------------------------------
       ! Create sdat field bundles 
       ! ------------------------------------

       if (my_task == master_task) then
          call dshr_nuopc_stream_getModelFieldList(sdat%stream(n),fldList)
       endif

       ! Create empty field bundles
       sdat%FB_stream_lbound(n) = ESMF_FieldBundleCreate(rc=rc) ! stream mesh at lower time bound 
       sdat%FB_stream_ubound(n) = ESMF_FieldBundleCreate(rc=rc) ! stream mesh at upper time bound
       sdat%FB_model_lbound(n)  = ESMF_FieldBundleCreate(rc=rc) ! spatial interpolation to model mesh
       sdat%FB_model_lbound(n)  = ESMF_FieldBundleCreate(rc=rc) ! spatial interpolation to model mesh
       sdat%FB_model(n)         = ESMF_FieldBundleCreate(rc=rc) ! time interpolation on model mesh

       ! get number of field names in fldList (colon delimited string)
       nflds = shr_string_listGetNum(fldList)
       ! loop over field names in fldList
       do nfld = 1,nflds
          ! get fldname in colon delimited string
          call shr_string_listGetName(fldlist,nfld,fldname)

          ! create fields on stream mesh at two time levels
          lfield = ESMF_FieldCreate(mesh_stream, ESMF_TYPEKIND_R8, name=trim(fldname), meshloc=ESMF_MESHLOC_ELEMENT, r=rc)
          call ESMF_FieldBundleAdd(sdat%FB_stream_lbound, (/lfield/), rc=rc)
          call ESMF_FieldBundleAdd(sdat%FB_stream_ubound, (/lfield/), rc=rc)
          call ESMF_FieldDestroy(lfield, rc)

          ! create fields on model mesh at two time levels and for the final interpolated time
          lfield = ESMF_FieldCreate(mesh_model, ESMF_TYPEKIND_R8, name=trim(fldname), meshloc=ESMF_MESHLOC_ELEMENT, r=rc)
          call ESMF_FieldBundleAdd(sdat%FB_model_lbound(n), (/lfield/), rc=rc)
          call ESMF_FieldBundleAdd(sdat%FB_model_ubound(n), (/lfield/), rc=rc)
          call ESMF_FieldBundleAdd(sdat%FB_model(n)       , (/lfield/), rc=rc)
          call ESMF_FieldDestroy(lfield, rc)
       end do

       ! Create a field for coszen time interpolation for this stream if needed
       if (trim(sdat%tintalgo(n)) == 'coszen') then
          sdat%field_coszen = ESMF_FieldCreate(mesh_stream, ESMF_TYPEKIND_R8, name='tavCosz', meshloc=ESMF_MESHLOC_ELEMENT, r=rc)
       endif

    end do

    ! ------------------------------------
    ! Create the route handles
    ! ------------------------------------

    ! create the source and destination fields needed for the route handles
    ! these fields will be used to create the route handles
    ! since all fields in a stream share the same mesh and there is only a unique model mesh
    ! can do this outside of a stream loop by just using the first stream index

    call FB_getFieldN(sdat%FB_stream_lbound(1), 1, lfield_src, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return
    call FB_getFieldN(sdat%FB_FB_model(1), 1, lfield_dst, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

    ! Loop over all active streams
    do n = 1,sdat%nstreams

       ! create stream(n) fill map if needed
       method = CompareMaskSubset
       if (dshr_dnuopc_MeshCompare(sdat%mesh_stream(n), sdat%mesh_model, method, mpicom)  &
            .or. trim(sdat%fillalgo(n))=='none') then
          ! Do nothng
       else
          ! TODO: Need to implement nearest neighbor fill for those cells that have a 
          ! mask value of 0 on the stream mesh - note that the source and destination meshes
          ! here are identical
       endif

       ! create stream(n) -> model mesh map
       if (trim(sdat%mapmask(n)) == 'dstmask') then
          method = CompareXYabsMask
       else
          method = CompareXYabs
       endif
       if (dshr_dnuopc_MeshCompare(sdat%mesh_stream(n), sdat%mesh_model, method, mpicom, 0.01_r8) &
            .or. trim(sdat%mapalgo(n))=='none') then

          ! Create redist route handel for stream(n) -> model mapping
          call ESMF_LogWrite(trim(subname) // ' creating stream->model RH redist ', ESMF_LOGMSG_INFO)
          call ESMF_FieldRedistStore(lfield_src, lfield_dst, routehandle=RH(mapbilnr,n), &
               ignoreUnmatchedIndices = .true., rc=rc)
          if (chkerr(rc,__LINE__,u_FILE_u)) return
       else

          ! Create bilinear route handle for stream(n) -> model mapping
          if (sdat%mapalgo(n) == 'bilinear') then
             !dstMaskValue = ispval_mask ! TODO: what should this be here?
             !srcMaskValue = ispval_mask ! TODO: what should this be here?
             call ESMF_FieldRegridStore(lfield_src, lfield_dst, routehandle=is_local%wrap%RH(mapfcopy,n), &
                  !srcMaskValues=(/srcMaskValue/), &
                  !dstMaskValues=(/dstMaskValue/), &
                  regridmethod=ESMF_REGRIDMETHOD_BILINEAR, polemethod=ESMF_POLEMETHOD_ALLAVG, &
                  srcTermProcessing=0, ignoreDegenerate=.true., unmappedaction=ESMF_UNMAPPEDACTION_IGNORE, rc=rc)
          end if
       endif

    end do ! end of loop over streams

    ! ------------------------------------
    ! check vectors and compute ustrm,vstrm
    ! ------------------------------------

    do m = 1,sdat%nvectors
       if (.not. shr_string_listIsValid(sdat%vectors(m))) then
          write(logunit,*) trim(subname),' vec fldlist invalid m=',m,trim(sdat%vectors(m))
          call shr_sys_abort(subname//': vec fldlist invalid:'//trim(sdat%vectors(m)))
       endif
       if (shr_string_listGetNum(sdat%vectors(m)) /= 2) then
          write(logunit,*) trim(subname),' vec fldlist ne 2 m=',m,trim(sdat%vectors(m))
          call shr_sys_abort(subname//': vec fldlist ne 2:'//trim(sdat%vectors(m)))
       endif
       call shr_string_listGetName(sdat%vectors(m),1,uname)
       call shr_string_listGetName(sdat%vectors(m),2,vname)

       nu = 0
       nv = 0
       do n = 1,sdat%nstreams
          if (FB_stream_lbound(n), trim(uname), rc=rc) nu=n
          if (FB_stream_lbound(n), trim(vname), rc=rc) nv=n
       enddo
       if (nu == 0  .or. nv == 0) then
          write(logunit,*) trim(subname),' vec flds not found  m=',m,trim(sdat%vectors(m))
          call shr_sys_abort(subname//': vec flds not found:'//trim(sdat%vectors(m)))
       endif
       if (nu /= nv) then
          if ((.not. dshr_nuopc_strdata_gridCompare(sdat%gridR(nu),sdat%gsmapR(nu), &
               sdat%gridR(nv), sdat%gsmapR(nv), dshr_nuopc_strdata_gridCompareXYabs,mpicom,0.01_r8)) .or. &
               (.not. dshr_nuopc_strdata_gridCompare(sdat%gridR(nu),sdat%gsmapR(nu), &
               sdat%gridR(nv),sdat%gsmapR(nv), dshr_nuopc_strdata_gridCompareMaskZeros,mpicom))) then
             write(logunit,*) trim(subname),' vec fld doms not same m=',m,trim(sdat%vectors(m))
             call shr_sys_abort(subname//': vec fld doms not same:'//trim(sdat%vectors(m)))
          endif
       endif
       sdat%ustrm(m) = nu
       sdat%vstrm(m) = nv
    enddo

  end subroutine dshr_nuopc_strdata_init

  !===============================================================================

  subroutine dshr_nuopc_strdata_advance(sdat,ymd,tod,mpicom,istr,timers)

    ! ------------------------------------------------------- !
    ! tcraig, Oct 11 2010.  Mismatching calendars: 4 cases    !
    ! ------------------------------------------------------- !
    ! ymdmod and todmod are the ymd and tod to time           !
    ! interpolate to.  Generally, these are just the model    !
    ! date and time.  Also, always use the stream calendar    !
    ! for time interpolation for reasons described below.     !
    ! When there is a calendar mismatch, support Feb 29 in a  !
    ! special way as needed to get reasonable values.         !
    ! Note that when Feb 29 needs to be treated specially,    !
    ! a discontinuity will be introduced.  The size of that   !
    ! discontinuity will depend on the time series input data.!
    ! ------------------------------------------------------- !
    ! (0) The stream calendar and model calendar are          !
    ! identical.  Proceed in the standard way.                !
    ! ------------------------------------------------------- !
    ! (1) If the stream is a no leap calendar and the model   !
    ! is gregorian, then time interpolate on the noleap       !
    ! calendar.  Then if the model date is Feb 29, compute    !
    ! stream data for Feb 28 by setting ymdmod and todmod to  !
    ! Feb 28.  This results in duplicate stream data on       !
    ! Feb 28 and Feb 29 and a discontinuity at the start of   !
    ! Feb 29.                                                 !
    ! This could be potentially updated by using the gregorian!
    ! calendar for time interpolation when the input data is  !
    ! relatively infrequent (say greater than daily) with the !
    ! following concerns.
    !   - The forcing will not be reproduced identically on   !
    !     the same day with climatological inputs data        !
    !   - Input data with variable input frequency might      !
    !     behave funny
    !   - An arbitrary discontinuity will be introduced in    !
    !     the time interpolation method based upon the        !
    !     logic chosen to transition from reproducing Feb 28  !
    !     on Feb 29 and interpolating to Feb 29.              !
    !   - The time gradient of data will change by adding a   !
    !     day arbitrarily.
    ! ------------------------------------------------------- !
    ! (2) If the stream is a gregorian calendar and the model !
    ! is a noleap calendar, then just time interpolate on the !
    ! gregorian calendar.  The causes Feb 29 stream data      !
    ! to be skipped and will lead to a discontinuity at the   !
    ! start of March 1.                                       !
    ! ------------------------------------------------------- !
    ! (3) If the calendars mismatch and neither of the three  !
    ! cases above are recognized, then abort.                 !
    ! ------------------------------------------------------- !
    
    type(shr_strdata_type) ,intent(inout)       :: sdat
    integer                ,intent(in)          :: ymd    ! current model date
    integer                ,intent(in)          :: tod    ! current model date
    integer                ,intent(in)          :: mpicom
    character(len=*)       ,intent(in),optional :: istr
    logical                ,intent(in),optional :: timers

    integer                 :: n,m,i,kf  ! generic index
    integer                 :: my_task,npes
    integer    ,parameter   :: master_task = 0
    logical                 :: mssrmlf
    logical,allocatable     :: newData(:)
    integer                 :: ierr
    integer                 :: nu,nv
    integer                 :: lsize,lsizeR,lsizeF
    integer    ,allocatable :: ymdmod(:) ! modified model dates to handle Feb 29
    integer                 :: todmod    ! modified model dates to handle Feb 29
    character(len=32)       :: lstr
    logical                 :: ltimers
    real(R8)                :: flb,fub   ! factor for lb and ub

    !--- for cosz method ---
    real(R8),pointer           :: lonr(:)              ! lon radians
    real(R8),pointer           :: latr(:)              ! lat radians
    real(R8),pointer           :: cosz(:)              ! cosz
    real(R8),pointer           :: tavCosz(:)           ! cosz, time avg over [LB,UB]
    real(R8),pointer           :: xlon(:),ylon(:)
    real(R8),parameter         :: solZenMin = 0.001_R8 ! minimum solar zenith angle

    type(ESMF_Time)            :: timeLB, timeUB       ! lb and ub times
    type(ESMF_TimeInterval)    :: timeint              ! delta time
    integer                    :: dday                 ! delta days
    real(R8)                   :: dtime                ! delta time
    integer                    :: uvar,vvar
    character(CS)              :: uname                ! u vector field name
    character(CS)              :: vname                ! v vector field name
    integer                    :: year,month,day       ! date year month day
    character(len=*),parameter :: timname = "_strd_adv"
    integer    ,parameter      :: tadj = 2

    !----- formats -----
    character(*),parameter :: subname = "(shr_strdata_advance) "
    !-------------------------------------------------------------------------------

    if (sdat%nstreams < 1) return

    lstr = ''
    if (present(istr)) then
       lstr = trim(istr)
    endif

    ltimers = .true.
    if (present(timers)) then
       ltimers = timers
    endif

    if (.not.ltimers) call t_adj_detailf(tadj)

    call t_barrierf(trim(lstr)//trim(timname)//'_total_BARRIER',mpicom)
    call t_startf(trim(lstr)//trim(timname)//'_total')

    call MPI_COMM_SIZE(mpicom,npes,ierr)
    call MPI_COMM_RANK(mpicom,my_task,ierr)

    mssrmlf = .false.

    sdat%ymd = ymd
    sdat%tod = tod

    if (sdat%nstreams > 0) then
       allocate(newData(sdat%nstreams))
       allocate(ymdmod(sdat%nstreams))

       do n = 1,sdat%nstreams

          ! case(0)
          ymdmod(n) = ymd
          todmod    = tod
          if (trim(sdat%calendar) /= trim(sdat%stream(n)%calendar)) then
             if ( (trim(sdat%calendar) == trim(shr_cal_gregorian)) .and. &
                  (trim(sdat%stream(n)%calendar) == trim(shr_cal_noleap))) then

                ! case (1), set feb 29 = feb 28
                call shr_cal_date2ymd (ymd,year,month,day)
                if (month == 2 .and. day == 29) then
                   call shr_cal_ymd2date(year,2,28,ymdmod(n))
                endif

             else if ((trim(sdat%calendar) == trim(shr_cal_noleap)) .and. &
                      (trim(sdat%stream(n)%calendar) == trim(shr_cal_gregorian))) then
                ! case (2), feb 29 input data will be skipped automatically

             else
                ! case (3), abort
                write(logunit,*) trim(subname),' ERROR: mismatch calendar ', &
                     trim(sdat%calendar),':',trim(sdat%stream(n)%calendar)
                call shr_sys_abort(trim(subname)//' ERROR: mismatch calendar ')
             endif
          endif

          ! Read lower bound data
          call t_barrierf(trim(lstr)//trim(timname)//'_readLBUB_BARRIER',mpicom)
          call t_startf(trim(lstr)//trim(timname)//'_readLBUB')

          call dshr_nuopc_strdata_readLBUB(sdat%stream(n), &
               sdat%pio_subsystem, sdat%io_type, sdat%pio_iodesc(n),  &
               ymdmod(n), todmod, mpicom, &
               
               sdat%FB_stream_lbound(n), sdat%ymdLB(n), sdat%todLB(n),  &
               sdat%FB_stream_ubound(n), sdat%ymdUB(n), sdat%todUB(n),  &
               sdat%avRFile(n),  trim(sdat%readmode(n)), newData(n), &
               istr=trim(lstr)//'_readLBUB')

          if (debug > 0) then
             write(logunit,*) trim(subname),' newData flag = ',n,newData(n)
             write(logunit,*) trim(subname),' LB ymd,tod = ',n,sdat%ymdLB(n),sdat%todLB(n)
             write(logunit,*) trim(subname),' UB ymd,tod = ',n,sdat%ymdUB(n),sdat%todUB(n)
          endif

          ! If new data was read in - then set sdat%ymdLB, sdat%ymdUB, sdat%dtmin and sdat%dtmax
          if (newData(n)) then
             if (debug > 0) then
                ! diagnostic
                write(logunit,*) trim(subname),' newData RLB = ',n,minval(sdat%FB_stream_lbound(n)%rAttr), &
                     maxval(sdat%FB_stream_lbound(n)%rAttr),sum(sdat%FB_stream_lbound(n)%rAttr)
                write(logunit,*) trim(subname),' newData RUB = ',n,minval(sdat%FB_stream_ubound(n)%rAttr), &
                     maxval(sdat%FB_stream_ubound(n)%rAttr),sum(sdat%FB_stream_ubound(n)%rAttr)
             endif

             call shr_cal_date2ymd(sdat%ymdLB(n),year,month,day)
             call shr_cal_timeSet(timeLB,sdat%ymdLB(n),0,sdat%stream(n)%calendar)
             call shr_cal_timeSet(timeUB,sdat%ymdUB(n),0,sdat%stream(n)%calendar)
             timeint = timeUB-timeLB
             call ESMF_TimeIntervalGet(timeint,StartTimeIn=timeLB,d=dday)
             dtime = abs(real(dday,R8) + real(sdat%todUB(n)-sdat%todLB(n),R8)/shr_const_cDay)

             sdat%dtmin(n) = min(sdat%dtmin(n),dtime)
             sdat%dtmax(n) = max(sdat%dtmax(n),dtime)
             if ((sdat%dtmax(n)/sdat%dtmin(n)) > sdat%dtlimit(n)) then
                write(logunit,*) trim(subname),' ERROR: for stream ',n
                write(logunit,*) trim(subName),' ERROR: dt limit1 ',sdat%dtmax(n),sdat%dtmin(n),sdat%dtlimit(n)
                write(logunit,*) trim(subName),' ERROR: dt limit2 ',sdat%ymdLB(n),sdat%todLB(n), &
                     sdat%ymdUB(n),sdat%todUB(n)
                call shr_sys_abort(trim(subName)//' ERROR dt limit for stream')
             endif
          endif
          call t_stopf(trim(lstr)//trim(timname)//'_readLBUB')

          ! If new data was read in, then fill, interpolate the lower and upper bound data to the model grid
          if (newData(n)) then
             if (sdat%doFill(n)) then
                call t_startf(trim(lstr)//trim(timname)//'_fill')
                call FB_fieldRegrid(sdat%FB_stream_lbound, sdat%FB_stream_lbound, sdat%rh_fill(n), rc=rc) 
                if (ChkErr(rc,__LINE__,u_FILE_u)) return
                call FB_fieldRegrid(sdat%FB_stream_ubound, sdat%FB_stream_ubound, sdat%rh_fill(n), rc=rc) 
                if (ChkErr(rc,__LINE__,u_FILE_u)) return
                call t_stopf(trim(lstr)//trim(timname)//'_fill')
             endif
             if (sdat%domaps(n)) then
                call t_startf(trim(lstr)//trim(timname)//'_map')
                call FB_fieldRegrid(sdat%FB_stream_lbound, sdat%FB_model_lbound, sdat%rh_map(n), rc=rc) 
                if (ChkErr(rc,__LINE__,u_FILE_u)) return
                call FB_fieldRegrid(sdat%FB_stream_ubound, sdat%FB_model_ubound, sdat%rh_map(n), rc=rc) 
                if (ChkErr(rc,__LINE__,u_FILE_u)) return
                call t_stopf(trim(lstr)//trim(timname)//'_map')
             end if
             if (debug > 0) then
                call FB_diagnose(sdat%FB_model_lb, subname//':FB_model_lb',rc=rc)
                if (ChkErr(rc,__LINE__,u_FILE_u)) return
             endif
          endif
       enddo

       ! remap with vectors if needed
       do m = 1,sdat%nvectors
          nu = sdat%ustrm(m)
          nv = sdat%vstrm(m)
          if ((sdat%domaps(nu) .or. sdat%domaps(nv)) .and. (newdata(nu) .or. newdata(nv))) then

             call t_startf(trim(lstr)//trim(timname)//'_vect')
             call shr_string_listGetName(sdat%vectors(m), 1, uname)
             call shr_string_listGetName(sdat%vectors(m), 2, vname)

             ! get source mesh and coordinates
             call ESMF_MeshGet(sdat%mesh_stream(n), spatialDim=spatialDim, numOwnedElements=numOwnedElements, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             allocate(ownedElemCoords_src(spatialDim*numOwnedElements))
             call ESMF_MeshGet(sdat%mesh_stream(n), ownedElemCoords=ownedElemCoords_src)
             if (chkerr(rc,__LINE__,u_FILE_u)) return

             ! get destination mesh and coordinates
             call ESMF_MeshGet(sdat%mesh_model(n), spatialDim=spatialDim, numOwnedElements=numOwnedElements, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             allocate(ownedElemCoords_src(spatialDim*numOwnedElements))
             call ESMF_MeshGet(sdat%mesh_model(n), ownedElemCoords=ownedElemCoords_src)
             if (chkerr(rc,__LINE__,u_FILE_u)) return

             ! create source field and destination fields
             field2d_src = ESMF_FieldCreate(lmesh_src, ESMF_TYPEKIND_R8, name='src2d', &
                  ungriddedLbound=(/1/), ungriddedUbound=(/2/), gridToFieldMap=(/2/), &
                  meshloc=ESMF_MESHLOC_ELEMENT, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             field2d_dst = ESMF_FieldCreate(lmesh_dst, ESMF_TYPEKIND_R8, name='dst2d', &
                  ungriddedLbound=(/1/), ungriddedUbound=(/2/), gridToFieldMap=(/2/), &
                  meshloc=ESMF_MESHLOC_ELEMENT, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return

             ! get pointers to source and destination data that will be filled in with rotation to cart3d
             call ESMF_FieldGet(field2d_src, farrayPtr=data2d_src, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call ESMF_FieldGet(field2d_dst, farrayPtr=data2d_dst, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             
             ! map LB: rotate source data, regrid, then rotate back 
             call FB_getFldPtr(sdat%FB_stream_lbound, trim(uname), data_u_src, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call FB_getFldPtr(sdat%FB_stream_lbound, trim(vname), data_v_src, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call FB_getFldPtr(sdat%FB_stream_lbound, trim(uname), data_u_dst, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call FB_getFldPtr(sdat%FB_stream_lbound, trim(vname), data_v_dst, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             do n = 1,size(data_u_src)
                lon = ownedElemCoords_src(2*n-1)
                lat = ownedElemCoords_src(2*n)
                sinlon = sin(lon*deg2rad)
                coslon = cos(lon*deg2rad)
                sinlat = sin(lat*deg2rad)
                coslat = cos(lat*deg2rad)
                data2d_src(1,n) = coslon * data_u_src(n) - sinlon * data_v_src(n)
                data2d_src(2,n) = sinlon * data_u_src(n) + coslon ( data_v_src(n)
             enddo
             call ESMF_FieldRegrid(field2d_src, field2d_dst, RouteHandle, &
                  termorderflag=ESMF_TERMORDER_SRCSEQ, checkflag=checkflag, zeroregion=ESMF_REGION_TOTAL, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             do n = 1,size(data_u_dst)
                lon = ownedElemCoords_dst(2*n-1)
                lat = ownedElemCoords_dst(2*n)
                sinlon = sin(lon*deg2rad)
                coslon = cos(lon*deg2rad)
                sinlat = sin(lat*deg2rad)
                coslat = cos(lat*deg2rad)
                ux = data2d_dst(1,n)
                uy = data2d_dst(2,n)
                uz = data2d_dst(3,n)
                data_u_dst(n) =  coslon * data_u_dst(n) + sinlon * data_v_dst(n)
                data_v_dst(n) = -sinlon * data_u_dst(n) + coslon * data_v_dst(n)
             enddo

             ! map UB: rotate source data, regrid, then rotate back 
             call FB_getFldPtr(sdat%FB_stream_ubound, trim(uname), data_u_src, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call FB_getFldPtr(sdat%FB_stream_ubound, trim(vname), data_v_src, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call FB_getFldPtr(sdat%FB_stream_ubound, trim(uname), data_u_dst, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call FB_getFldPtr(sdat%FB_stream_ubound, trim(vname), data_v_dst, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             do n = 1,size(data_u_src)
                lon = ownedElemCoords_src(2*n-1)
                lat = ownedElemCoords_src(2*n)
                sinlon = sin(lon*deg2rad)
                coslon = cos(lon*deg2rad)
                sinlat = sin(lat*deg2rad)
                coslat = cos(lat*deg2rad)
                data2d_src(1,n) = coslon * data_u_src(n) - sinlon * data_v_src(n)
                data2d_src(2,n) = sinlon * data_u_src(n) + coslon ( data_v_src(n)
             enddo
             call ESMF_FieldRegrid(field2d_src, field2d_dst, RouteHandle, &
                  termorderflag=ESMF_TERMORDER_SRCSEQ, checkflag=checkflag, zeroregion=ESMF_REGION_TOTAL, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             do n = 1,size(data_u_dst)
                lon = ownedElemCoords_dst(2*n-1)
                lat = ownedElemCoords_dst(2*n)
                sinlon = sin(lon*deg2rad)
                coslon = cos(lon*deg2rad)
                sinlat = sin(lat*deg2rad)
                coslat = cos(lat*deg2rad)
                ux = data2d_dst(1,n)
                uy = data2d_dst(2,n)
                uz = data2d_dst(3,n)
                data_u_dst(n) =  coslon * data_u_dst(n) + sinlon * data_v_dst(n)
                data_v_dst(n) = -sinlon * data_u_dst(n) + coslon * data_v_dst(n)
             enddo

             call t_stopf(trim(lstr)//trim(timname)//'_vect')
          endif
       enddo

       do n = 1,sdat%nstreams

          !--- method: coszen -------------------------------------------------------
          if (trim(sdat%tintalgo(n)) == 'coszen') then
             call t_startf(trim(lstr)//trim(timname)//'_coszen')

             !--- make sure orb info has been set ---
             if (sdat%eccen == SHR_ORB_UNDEF_REAL) then
                call shr_sys_abort(subname//' ERROR in orb params for coszen tinterp')
             else if (sdat%modeldt < 1) then
                call shr_sys_abort(subname//' ERROR: model dt < 1 for coszen tinterp')
             endif

             !--- allocate avg cosz array ---
             lsizeF = mct_aVect_lsize(sdat%FB_model_lbound(n))
             allocate(tavCosz(lsizeF),cosz(lsizeF),lonr(lsizeF),latr(lsizeF))

             !--- get lat/lon data ---
             kf = mct_aVect_indexRA(sdat%grid%data,'lat')
             latr(:) = sdat%grid%data%rAttr(kf,:) * deg2rad
             kf = mct_aVect_indexRA(sdat%grid%data,'lon')
             lonr(:) = sdat%grid%data%rAttr(kf,:) * deg2rad

             call t_startf(trim(lstr)//trim(timname)//'_coszenC')
             cosz = 0.0_r8
             call dshr_nuopc_tInterp_getCosz(cosz,lonr,latr,ymdmod(n),todmod, &
                  sdat%eccen,sdat%mvelpp,sdat%lambm0,sdat%obliqr,sdat%stream(n)%calendar)
             call t_stopf(trim(lstr)//trim(timname)//'_coszenC')

             if (newdata(n)) then
                !--- compute a new avg cosz ---
                call t_startf(trim(lstr)//trim(timname)//'_coszenN')
                call shr_tInterp_getAvgCosz(tavCosz,lonr,latr, &
                     sdat%ymdLB(n),sdat%todLB(n), sdat%ymdUB(n),sdat%todUB(n), &
                     sdat%eccen,sdat%mvelpp,sdat%lambm0,sdat%obliqr,sdat%modeldt,&
                     sdat%stream(n)%calendar)
                call mct_avect_importRAttr(sdat%avCoszen(n),'tavCosz',tavCosz,lsizeF)
                call t_stopf(trim(lstr)//trim(timname)//'_coszenN')
             else
                !--- reuse existing avg cosz ---
                call mct_avect_exportRAttr(sdat%avCoszen(n),'tavCosz',tavCosz)
             endif

             !--- t-interp is LB data normalized with this factor: cosz/tavCosz ---
             do i = 1,lsizeF
                if (cosz(i) > solZenMin) then
                   sdat%avs(n)%rAttr(:,i) = sdat%FB_model_lbound(n)%rAttr(:,i)*cosz(i)/tavCosz(i)
                else
                   sdat%avs(n)%rAttr(:,i) =  0._r8
                endif
             enddo
             deallocate(tavCosz,cosz,lonr,latr)
             call t_stopf(trim(lstr)//trim(timname)//'_coszen')

             !--- method: not coszen ---------------------------------------------------
          elseif (trim(sdat%tintalgo(n)) /= trim(shr_strdata_nullstr)) then

             call t_startf(trim(lstr)//trim(timname)//'_tint')
             call shr_tInterp_getFactors(sdat%ymdlb(n),sdat%todlb(n),sdat%ymdub(n),sdat%todub(n), &
                  ymdmod(n),todmod,flb,fub, &
                  calendar=sdat%stream(n)%calendar,algo=trim(sdat%tintalgo(n)))
             if (debug > 0) then
                write(logunit,*) trim(subname),' interp = ',n,flb,fub
             endif
             sdat%avs(n)%rAttr(:,:) = sdat%FB_model_lbound(n)%rAttr(:,:)*flb + sdat%FB_model_ubound(n)%rAttr(:,:)*fub
             call t_stopf(trim(lstr)//trim(timname)//'_tint')

          else
             call t_startf(trim(lstr)//trim(timname)//'_zero')
             call mct_avect_zero(sdat%avs(n))
             call t_stopf(trim(lstr)//trim(timname)//'_zero')
          endif
          if (debug > 0) then
             write(logunit,*) trim(subname),' sdat av = ',n,minval(sdat%avs(n)%rAttr),&
                  maxval(sdat%avs(n)%rAttr),sum(sdat%avs(n)%rAttr)
          endif

       enddo

       deallocate(newData)
       deallocate(ymdmod)

    endif    ! nstreams > 0

    call t_stopf(trim(lstr)//trim(timname)//'_total')
    if (.not.ltimers) call t_adj_detailf(-tadj)

  end subroutine dshr_nuopc_strdata_advance

  !===============================================================================

  subroutine dshr_nuopc_strdata_restWrite(filename,sdat,mpicom,str1,str2)

    character(len=*)      ,intent(in)    :: filename
    type(shr_strdata_type),intent(inout) :: sdat
    integer               ,intent(in)    :: mpicom
    character(len=*)      ,intent(in)    :: str1
    character(len=*)      ,intent(in)    :: str2

    !--- local ----
    integer     :: my_task,ier

    !----- formats -----
    character(len=*),parameter :: subname = "(shr_strdata_restWrite) "
    !-------------------------------------------------------------------------------

    call MPI_COMM_RANK(mpicom,my_task,ier)
    if (my_task == 0) then
       call dshr_nuopc_stream_restWrite(sdat%stream,trim(filename),trim(str1),trim(str2),sdat%nstreams)
    endif

  end subroutine dshr_nuopc_strdata_restWrite

  !===============================================================================

  subroutine dshr_nuopc_strdata_restRead(filename,sdat,mpicom)

    character(len=*)      ,intent(in)    :: filename
    type(shr_strdata_type),intent(inout) :: sdat
    integer               ,intent(in)    :: mpicom

    !--- local ----
    integer     :: my_task,ier

    !----- formats -----
    character(len=*),parameter :: subname = "(shr_strdata_restRead) "
    !-------------------------------------------------------------------------------

    call MPI_COMM_RANK(mpicom,my_task,ier)
    if (my_task == 0) then
       call dshr_nuopc_stream_restRead(sdat%stream,trim(filename),sdat%nstreams)
    endif

  end subroutine dshr_nuopc_strdata_restRead

  !===============================================================================

  subroutine dshr_nuopc_strdata_setOrbs(sdat,eccen,mvelpp,lambm0,obliqr,modeldt)

    type(shr_strdata_type) ,intent(inout) :: sdat
    real(R8)               ,intent(in)    :: eccen
    real(R8)               ,intent(in)    :: mvelpp
    real(R8)               ,intent(in)    :: lambm0
    real(R8)               ,intent(in)    :: obliqr
    integer                ,intent(in)    :: modeldt
    !-------------------------------------------------------------------------------

    sdat%eccen   = eccen
    sdat%mvelpp  = mvelpp
    sdat%lambm0  = lambm0
    sdat%obliqr  = obliqr
    sdat%modeldt = modeldt

  end subroutine dshr_nuopc_strdata_setOrbs

  !===============================================================================

  subroutine dshr_nuopc_strdata_readnml(sdat,file,rc,mpicom)

    ! Reads strdata namelists common to all data models

    ! input/output arguments
    type(shr_strdata_type) ,intent(inout):: sdat   ! strdata data data-type
    character(*) ,optional ,intent(in)   :: file   ! file to read strdata from
    integer      ,optional ,intent(out)  :: rc     ! return code
    integer      ,optional ,intent(in)   :: mpicom ! mpi comm

    ! local variables
    integer        :: rCode         ! return code
    integer        :: nUnit         ! fortran i/o unit number
    integer        :: n             ! generic loop index
    integer        :: my_task       ! my task number, 0 is default
    integer        :: master_task   ! master task number, 0 is default
    integer        :: ntasks        ! total number of tasks

    !----- temporary/local namelist vars to read int -----
    character(CL) :: dataMode          ! flags physics options wrt input data
    character(CL) :: domainFile        ! file   containing domain info
    character(CL) :: streams(nStrMax)  ! stream description file names
    character(CL) :: taxMode(nStrMax)  ! time axis cycling mode
    real(R8)      :: dtlimit(nStrMax)  ! delta time limiter
    character(CL) :: vectors(nVecMax)  ! define vectors to vector map
    character(CL) :: fillalgo(nStrMax) ! fill algorithm
    character(CL) :: fillmask(nStrMax) ! fill mask
    character(CL) :: fillread(nStrMax) ! fill mapping file to read
    character(CL) :: fillwrite(nStrMax)! fill mapping file to write
    character(CL) :: mapalgo(nStrMax)  ! scalar map algorithm
    character(CL) :: mapmask(nStrMax)  ! scalar map mask
    character(CL) :: mapread(nStrMax)  ! regrid mapping file to read
    character(CL) :: mapwrite(nStrMax) ! regrid mapping file to write
    character(CL) :: tintalgo(nStrMax) ! time interpolation algorithm
    character(CL) :: readmode(nStrMax) ! file read mode
    character(CL) :: fileName    ! generic file name
    integer       :: yearFirst   ! first year to use in data stream
    integer       :: yearLast    ! last  year to use in data stream
    integer       :: yearAlign   ! data year that aligns with yearFirst

    !----- define namelist -----
    namelist / shr_strdata_nml / &
         dataMode        &
         , domainFile      &
         , streams         &
         , taxMode         &
         , dtlimit         &
         , vectors         &
         , fillalgo        &
         , fillmask        &
         , fillread        &
         , fillwrite       &
         , mapalgo         &
         , mapmask         &
         , mapread         &
         , mapwrite        &
         , tintalgo        &
         , readmode

    !----- formats -----
    character(*),parameter :: subName = "(shr_strdata_readnml) "
    character(*),parameter ::   F00 = "('(shr_strdata_readnml) ',8a)"
    character(*),parameter ::   F01 = "('(shr_strdata_readnml) ',a,i6,a)"
    character(*),parameter ::   F02 = "('(shr_strdata_readnml) ',a,es13.6)"
    character(*),parameter ::   F03 = "('(shr_strdata_readnml) ',a,l6)"
    character(*),parameter ::   F04 = "('(shr_strdata_readnml) ',a,i2,a,a)"
    character(*),parameter ::   F20 = "('(shr_strdata_readnml) ',a,i6,a)"
    character(*),parameter ::   F90 = "('(shr_strdata_readnml) ',58('-'))"
    !-------------------------------------------------------------------------------

    if (present(rc)) rc = 0

    my_task = 0
    master_task = 0
    ntasks = 1
    if (present(mpicom)) then
       call MPI_COMM_RANK(mpicom,my_task,rCode)
       call MPI_COMM_SIZE(mpicom,ntasks,rCode)
    endif

    !--master--task--
    if (my_task == master_task) then

       !----------------------------------------------------------------------------
       ! set default values for namelist vars
       !----------------------------------------------------------------------------
       dataMode    = 'NULL'
       domainFile  = trim(shr_strdata_nullstr)
       streams(:)  = trim(shr_strdata_nullstr)
       taxMode(:)  = trim(shr_stream_taxis_cycle)
       dtlimit(:)  = dtlimit_default
       vectors(:)  = trim(shr_strdata_nullstr)
       fillalgo(:) = 'nn'
       fillmask(:) = 'nomask'
       fillread(:) = trim(shr_strdata_unset)
       fillwrite(:)= trim(shr_strdata_unset)
       mapalgo(:)  = 'bilinear'
       mapmask(:)  = 'dstmask'
       mapread(:)  = trim(shr_strdata_unset)
       mapwrite(:) = trim(shr_strdata_unset)
       tintalgo(:) = 'linear'
       readmode(:) = 'single'


       !----------------------------------------------------------------------------
       ! read input namelist
       !----------------------------------------------------------------------------
       if (present(file)) then
          write(logunit,F00) 'reading input namelist file: ',trim(file)
          call shr_sys_flush(logunit)
          open (newunit=nUnit,file=trim(file),status="old",action="read")
          call shr_nl_find_group_name(nUnit, 'shr_strdata_nml', status=rCode)
          if (rCode == 0) then
             read (nUnit, nml=shr_strdata_nml, iostat=rCode)
             if (rCode /= 0) then
                write(logunit,F01) 'ERROR: reading input namelist shr_strdata_input from file, &
                     &'//trim(file)//' iostat=',rCode
                call shr_sys_abort(subName//": namelist read error "//trim(file))
             end if
          end if
          close(nUnit)
       endif

       !----------------------------------------------------------------------------
       ! copy temporary/local namelist vars into data structure
       !----------------------------------------------------------------------------
       sdat%nstreams    = 0
       do n=1,nStrMax
          call dshr_nuopc_stream_default(sdat%stream(n))
       enddo
       sdat%dataMode    = dataMode
       sdat%domainFile  = domainFile
       sdat%streams(:)  = streams(:)
       sdat%taxMode(:)  = taxMode(:)
       sdat%dtlimit(:)  = dtlimit(:)
       sdat%vectors(:)  = vectors(:)
       sdat%fillalgo(:) = fillalgo(:)
       sdat%fillmask(:) = fillmask(:)
       sdat%fillread(:) = fillread(:)
       sdat%fillwrit(:) = fillwrite(:)
       sdat%mapalgo(:)  = mapalgo(:)
       sdat%mapmask(:)  = mapmask(:)
       sdat%mapread(:)  = mapread(:)
       sdat%mapwrit(:)  = mapwrite(:)
       sdat%tintalgo(:) = tintalgo(:)
       sdat%readmode(:) = readmode(:)
       do n=1,nStrMax
          if (trim(streams(n)) /= trim(shr_strdata_nullstr)) sdat%nstreams = max(sdat%nstreams,n)
          if (trim(sdat%taxMode(n)) == trim(shr_stream_taxis_extend)) sdat%dtlimit(n) = 1.0e30
       end do
       sdat%nvectors = 0
       do n=1,nVecMax
          if (trim(vectors(n)) /= trim(shr_strdata_nullstr)) sdat%nvectors = n
       end do

       do n = 1,sdat%nstreams
          if (trim(sdat%streams(n)) /= shr_strdata_nullstr) then
             ! extract fileName (stream description text file), yearAlign, yearFirst, yearLast from sdat%streams(n)
             call dshr_nuopc_stream_parseInput(sdat%streams(n), fileName, yearAlign, yearFirst, yearLast)

             ! initialize stream datatype, read description text file
             call dshr_nuopc_stream_init(sdat%stream(n), fileName, yearFirst, yearLast, yearAlign, trim(sdat%taxMode(n)))
          end if
       enddo

       !   call dshr_nuopc_strdata_print(sdat,trim(file)//' NML_ONLY')

    endif   ! master_task
    !--master--task--

    if (present(mpicom)) then
       call shr_mpi_bcast(sdat%dataMode  ,mpicom,'dataMode')
       call shr_mpi_bcast(sdat%domainFile,mpicom,'domainFile')
       call shr_mpi_bcast(sdat%calendar  ,mpicom,'calendar')
       call shr_mpi_bcast(sdat%nstreams  ,mpicom,'nstreams')
       call shr_mpi_bcast(sdat%nvectors  ,mpicom,'nvectors')
       call shr_mpi_bcast(sdat%streams   ,mpicom,'streams')
       call shr_mpi_bcast(sdat%taxMode   ,mpicom,'taxMode')
       call shr_mpi_bcast(sdat%dtlimit   ,mpicom,'dtlimit')
       call shr_mpi_bcast(sdat%vectors   ,mpicom,'vectors')
       call shr_mpi_bcast(sdat%fillalgo  ,mpicom,'fillalgo')
       call shr_mpi_bcast(sdat%fillmask  ,mpicom,'fillmask')
       call shr_mpi_bcast(sdat%fillread  ,mpicom,'fillread')
       call shr_mpi_bcast(sdat%fillwrit  ,mpicom,'fillwrit')
       call shr_mpi_bcast(sdat%mapalgo   ,mpicom,'mapalgo')
       call shr_mpi_bcast(sdat%mapmask   ,mpicom,'mapmask')
       call shr_mpi_bcast(sdat%mapread   ,mpicom,'mapread')
       call shr_mpi_bcast(sdat%mapwrit   ,mpicom,'mapwrit')
       call shr_mpi_bcast(sdat%tintalgo  ,mpicom,'tintalgo')
       call shr_mpi_bcast(sdat%readmode  ,mpicom,'readmode')
    endif

    sdat%ymdLB = -1
    sdat%todLB = -1
    sdat%ymdUB = -1
    sdat%todUB = -1
    sdat%dtmin = 1.0e30
    sdat%dtmax = 0.0
    sdat%nxg   = 0
    sdat%nyg   = 0
    sdat%nzg   = 0
    sdat%eccen  = SHR_ORB_UNDEF_REAL
    sdat%mvelpp = SHR_ORB_UNDEF_REAL
    sdat%lambm0 = SHR_ORB_UNDEF_REAL
    sdat%obliqr = SHR_ORB_UNDEF_REAL
    sdat%modeldt = 0
    sdat%calendar = shr_cal_noleap

  end subroutine dshr_nuopc_strdata_readnml

  !===============================================================================

  subroutine dshr_nuopc_strdata_print(sdat,name)

    ! !DESCRIPTION:
    !  Print strdata common to all data models

    ! !INPUT/OUTPUT PARAMETERS:
    type(shr_strdata_type)  ,intent(in) :: sdat  ! strdata data data-type
    character(len=*),optional,intent(in) :: name  ! just a name for tracking

    integer       :: n
    character(CL) :: lname

    !----- formats -----
    character(*),parameter :: subName = "(shr_strdata_print) "
    character(*),parameter ::   F00 = "('(shr_strdata_print) ',8a)"
    character(*),parameter ::   F01 = "('(shr_strdata_print) ',a,i6,a)"
    character(*),parameter ::   F02 = "('(shr_strdata_print) ',a,es13.6)"
    character(*),parameter ::   F03 = "('(shr_strdata_print) ',a,l6)"
    character(*),parameter ::   F04 = "('(shr_strdata_print) ',a,i2,a,a)"
    character(*),parameter ::   F05 = "('(shr_strdata_print) ',a,i2,a,i6)"
    character(*),parameter ::   F06 = "('(shr_strdata_print) ',a,i2,a,l2)"
    character(*),parameter ::   F07 = "('(shr_strdata_print) ',a,i2,a,es13.6)"
    character(*),parameter ::   F20 = "('(shr_strdata_print) ',a,i6,a)"
    character(*),parameter ::   F90 = "('(shr_strdata_print) ',58('-'))"
    !-------------------------------------------------------------------------------

    lname = 'unknown'
    if (present(name)) then
       lname = trim(name)
    endif

    !----------------------------------------------------------------------------
    ! document datatype settings
    !----------------------------------------------------------------------------
    write(logunit,F90)
    write(logunit,F00) "name        = ",trim(lname)
    write(logunit,F00) "dataMode    = ",trim(sdat%dataMode)
    write(logunit,F00) "domainFile  = ",trim(sdat%domainFile)
    write(logunit,F01) "nxg         = ",sdat%nxg
    write(logunit,F01) "nyg         = ",sdat%nyg
    write(logunit,F01) "nzg         = ",sdat%nzg
    write(logunit,F00) "calendar    = ",trim(sdat%calendar)
    write(logunit,F01) "io_type     = ",sdat%io_type
    write(logunit,F02) "eccen       = ",sdat%eccen
    write(logunit,F02) "mvelpp      = ",sdat%mvelpp
    write(logunit,F02) "lambm0      = ",sdat%lambm0
    write(logunit,F02) "obliqr      = ",sdat%obliqr
    write(logunit,F01) "nstreams    = ",sdat%nstreams
    write(logunit,F01) "pio_iotype  = ",sdat%io_type

    do n=1, sdat%nstreams
       write(logunit,F04) "  streams (",n,") = ",trim(sdat%streams(n))
       write(logunit,F04) "  taxMode (",n,") = ",trim(sdat%taxMode(n))
       write(logunit,F07) "  dtlimit (",n,") = ",sdat%dtlimit(n)
       write(logunit,F05) "  strnxg  (",n,") = ",sdat%strnxg(n)
       write(logunit,F05) "  strnyg  (",n,") = ",sdat%strnyg(n)
       write(logunit,F05) "  strnzg  (",n,") = ",sdat%strnzg(n)
       write(logunit,F06) "  dofill  (",n,") = ",sdat%dofill(n)
       write(logunit,F04) "  fillalgo(",n,") = ",trim(sdat%fillalgo(n))
       write(logunit,F04) "  fillmask(",n,") = ",trim(sdat%fillmask(n))
       write(logunit,F04) "  fillread(",n,") = ",trim(sdat%fillread(n))
       write(logunit,F04) "  fillwrit(",n,") = ",trim(sdat%fillwrit(n))
       write(logunit,F06) "  domaps  (",n,") = ",sdat%domaps(n)
       write(logunit,F04) "  mapalgo (",n,") = ",trim(sdat%mapalgo(n))
       write(logunit,F04) "  mapmask (",n,") = ",trim(sdat%mapmask(n))
       write(logunit,F04) "  mapread (",n,") = ",trim(sdat%mapread(n))
       write(logunit,F04) "  mapwrit (",n,") = ",trim(sdat%mapwrit(n))
       write(logunit,F04) "  tintalgo(",n,") = ",trim(sdat%tintalgo(n))
       write(logunit,F04) "  readmode(",n,") = ",trim(sdat%readmode(n))
       write(logunit,F01) " "
    end do
    write(logunit,F01) "nvectors    = ",sdat%nvectors
    do n=1, sdat%nvectors
       write(logunit,F04) "  vectors (",n,") = ",trim(sdat%vectors(n))
    end do
    write(logunit,F90)
    call shr_sys_flush(logunit)

  end subroutine dshr_nuopc_strdata_print

  !===============================================================================

  subroutine dshr_nuopc_strdata_readLBUB(stream, &
       pio_subsystem, pio_iotype, pio_iodesc, mDate, mSec, mpicom,  &
       avLB, mDateLB, mSecLB, avUB, mDateUB, mSecUB, &
       avFile, readMode, newData, rmOldFile, istr)


    !----- arguments -----
    type(shr_stream_streamType)   ,intent(inout) :: stream
    type(iosystem_desc_t), target ,intent(inout) :: pio_subsystem
    integer                       ,intent(in)    :: pio_iotype
    type(io_desc_t)               ,intent(inout) :: pio_iodesc
    integer                       ,intent(in)    :: mDate  ,mSec
    integer                       ,intent(in)    :: mpicom
    type(ESMF_FieldBundle)        ,intent(inout) :: FB_stream_lbound
    integer                       ,intent(inout) :: mDateLB,mSecLB
    type(ESMF_FieldBundle)        ,intent(inout) :: FB_stream_ubound
    integer                       ,intent(inout) :: mDateUB,mSecUB
    type(ESMF_FieldBundle)        ,intent(inout) :: FB_stream_all(:)
    character(len=*)              ,intent(in)    :: readMode
    logical                       ,intent(out)   :: newData
    logical          ,optional    ,intent(in)    :: rmOldFile
    character(len=*) ,optional    ,intent(in)    :: istr

    ! local variables
    integer           :: my_task, master_task
    integer           :: ierr       ! error code
    integer           :: rCode      ! return code
    logical           :: localCopy,fileexists
    integer           :: ivals(6)   ! bcast buffer
    integer           :: oDateLB,oSecLB,dDateLB
    integer           :: oDateUB,oSecUB,dDateUB
    real(R8)          :: rDateM,rDateLB,rDateUB  ! model,LB,UB dates with fractional days
    integer           :: n_lb, n_ub
    character(CL)     :: fn_lb,fn_ub,fn_next,fn_prev
    character(CL)     :: path
    character(len=32) :: lstr
    real(R8)          :: spd

    character(*), parameter :: subname = '(dshr_nuopc_strdata_readLBUB) '
    character(*), parameter :: F00   = "('(dshr_nuopc_strdata_readLBUB) ',8a)"
    character(*), parameter :: F01   = "('(dshr_nuopc_strdata_readLBUB) ',a,5i8)"

    !-------------------------------------------------------------------------------
    ! PURPOSE:  Read LB and UB stream data
    !----------------------------------------------------------------------------

    lstr = 'dshr_nuopc_strdata_readLBUB'
    if (present(istr)) then
       lstr = trim(istr)
    endif

    call t_startf(trim(lstr)//'_setup')
    call MPI_COMM_RANK(mpicom,my_task,ierr)
    master_task = 0
    spd = shr_const_cday

    newData = .false.
    n_lb = -1
    n_ub = -1
    fn_lb = 'undefinedlb'
    fn_ub = 'undefinedub'

    oDateLB = mDateLB
    oSecLB  = mSecLB
    oDateUB = mDateUB
    oSecUB  = mSecUB

    rDateM  = real(mDate  ,R8) + real(mSec  ,R8)/spd
    rDateLB = real(mDateLB,R8) + real(mSecLB,R8)/spd
    rDateUB = real(mDateUB,R8) + real(mSecUB,R8)/spd
    call t_stopf(trim(lstr)//'_setup')

    if (rDateM < rDateLB .or. rDateM > rDateUB) then
       call t_startf(trim(lstr)//'_fbound')
       if (my_task == master_task) then
          call dshr_nuopc_stream_findBounds(stream,mDate,mSec,                 &
               ivals(1),dDateLB,ivals(2),ivals(5),fn_lb, &
               ivals(3),dDateUB,ivals(4),ivals(6),fn_ub  )
          call dshr_nuopc_stream_getFilePath(stream,path)
       endif
       call t_stopf(trim(lstr)//'_fbound')
       call t_startf(trim(lstr)//'_bcast')
       call shr_mpi_bcast(stream%calendar,mpicom)
       call shr_mpi_bcast(ivals,mpicom)
       mDateLB = ivals(1)
       mSecLB  = ivals(2)
       mDateUB = ivals(3)
       mSecUB  = ivals(4)
       n_lb    = ivals(5)
       n_ub    = ivals(6)
       call t_stopf(trim(lstr)//'_bcast')
    endif

    if (mDateLB /= oDateLB .or. mSecLB /= oSecLB) then
       newdata = .true.

       if (mDateLB == oDateUB .and. mSecLB == oSecUB) then

          ! copy FB_stream_ubound to FB_stream_lbound
          call t_startf(trim(lstr)//'_LB_copy')
          call ESMF_FieldBundleGet(FB_stream_ubound, fieldCount=fieldCount, rc=rc)
          if (chkerr(rc,__LINE__,u_FILE_u)) return
          allocate(lfieldNameList(fieldCount))
          call ESMF_FieldBundleGet(FB_stream_ubound, itemNameList=lfieldNameList, rc=rc)
          if (chkerr(rc,__LINE__,u_FILE_u)) return
.          do n = 1,fieldCount
             fldname = trim(lfieldnamelist(n))
             call ESMF_FieldBundleGet(FB_stream_ubound, fieldName=fldname, field=lfield_ub, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call ESMF_FieldBundleGet(FB_stream_lbound, fieldName=fldname, field=lfield_ub, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call ESMF_FieldGet(lfield_ub, farrayPtr=dataptr_ub, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             call ESMF_FieldGet(lfield_lb, farrayPtr=dataptr_lb, rc=rc)
             if (chkerr(rc,__LINE__,u_FILE_u)) return
             dataptr_lb(:) = dataptr_ub(:)
          end do
          call t_stopf(trim(lstr)//'_LB_copy')

       else

          select case(readMode)
          case ('single')
             call dshr_nuopc_strdata_readstrm(stream, FB_stream, &
                  pio_subsystem, pio_iotype, pio_iodesc, mpicom, path, &
                  fn_lb, n_lb, istr=trim(lstr)//'_UB', boundstr = 'ub')
          case ('full_file')
             ! TODO: implement full file read
          case default
             write(logunit,F00) "ERROR: Unsupported readmode : ", trim(readMode)
             call shr_sys_abort(subName//"ERROR: Unsupported readmode: "//trim(readMode))
          end select
       endif
    endif

    if (mDateUB /= oDateUB .or. mSecUB /= oSecUB) then
       newdata = .true.

       select case(readMode)
       case ('single')
          call dshr_nuopc_strdata_readstrm(stream, pio_subsystem, pio_iotype, pio_iodesc, gsMap, avUB, mpicom, &
               path, fn_ub, n_ub,istr=trim(lstr)//'_UB', boundstr = 'ub')
       case ('full_file')
          call dshr_nuopc_strdata_readstrm_fullfile(stream, pio_subsystem, pio_iotype, &
               gsMap, avUB, avFile, mpicom, &
               path, fn_ub, n_ub,istr=trim(lstr)//'_UB', boundstr = 'ub')
       case default
          write(logunit,F00) "ERROR: Unsupported readmode : ", trim(readMode)
          call shr_sys_abort(subName//"ERROR: Unsupported readmode: "//trim(readMode))
       end select

    endif

    call t_startf(trim(lstr)//'_filemgt')
    !--- determine previous & next data files in list of files ---
    if (my_task == master_task .and. newdata) then
       call dshr_nuopc_stream_getFilePath(stream,path)
    endif
    call t_stopf(trim(lstr)//'_filemgt')

  end subroutine dshr_nuopc_strdata_readLBUB

  !===============================================================================

  subroutine dshr_nuopc_strdata_readstrm(stream, FB_stream, &
       pio_subsystem, pio_iotype, pio_iodesc, mpicom, path, fn, nt, istr, boundstr)

    ! input/output variables
    type(shr_stream_streamType) ,intent(inout)         :: stream
    type(ESMF_FieldBundle)      ,intent(inout)         :: FB_stream
    type(iosystem_desc_t)       ,intent(inout), target :: pio_subsystem
    integer                     ,intent(in)            :: pio_iotype
    type(io_desc_t)             ,intent(inout)         :: pio_iodesc
    integer                     ,intent(in)            :: mpicom
    character(len=*)            ,intent(in)            :: path
    character(len=*)            ,intent(in)            :: fn
    integer                     ,intent(in)            :: nt
    character(len=*),optional   ,intent(in)            :: istr
    character(len=*),optional   ,intent(in)            :: boundstr

    ! local variables
    type(ESMF_Field)              :: lfield
    character(CS)                 :: fldname
    character(CL)                 :: fileName
    character(CL)                 :: currfile
    type(file_desc_t)             :: pioid
    type(var_desc_t)              :: varid
    integer(kind=pio_offset_kind) :: frame
    integer                       :: k, n
    integer                       :: my_task
    integer                       :: master_task
    integer                       :: ierr
    logical                       :: fileexists
    integer                       :: rCode      ! return code
    character(len=32)             :: lstr
    logical                       :: fileopen
    character(ESMF_MAXSTR), allocatable :: lfieldNameList(:)
    character(*), parameter :: subname = '(dshr_nuopc_strdata_readstrm) '
    character(*), parameter :: F00   = "('(dshr_nuopc_strdata_readstrm) ',8a)"
    character(*), parameter :: F02   = "('(dshr_nuopc_strdata_readstrm) ',2a,i8)"
    !-------------------------------------------------------------------------------

    lstr = 'shr_strdata_readstrm'
    if (present(istr)) then
       lstr = trim(istr)
    endif

    bstr = ''
    if (present(boundstr)) then
       bstr = trim(boundstr)
    endif

    call MPI_COMM_RANK(mpicom,my_task,ierr)
    master_task = 0

    ! Set up file to read from
    call t_barrierf(trim(lstr)//'_BARRIER',mpicom)
    call t_startf(trim(lstr)//'_setup')
    if (my_task == master_task) then
       fileName = trim(path)//fn
       inquire(file=trim(fileName),exist=fileExists)
       if (.not. fileExists) then
          write(logunit,F00) "ERROR: file does not exist: ", trim(fileName)
          call shr_sys_abort(subName//"ERROR: file does not exist: "//trim(fileName))
       end if
    endif
    call shr_mpi_bcast(filename,mpicom,'filename')
    call t_stopf(trim(lstr)//'_setup')

    ! Get current file and determine if it is open
    call dshr_nuopc_stream_getCurrFile(stream, fileopen=fileopen, currfile=currfile, currpioid=pioid)
    if (fileopen .and. currfile==filename) then
       ! don't reopen file, all good
    else
       ! otherwise close the old file if open and open new file
       if (fileopen) then
          if (my_task == master_task) then
             write(logunit,F00) 'close  : ',trim(currfile)
             call shr_sys_flush(logunit)
          endif
          call pio_closefile(pioid)
       endif
       if (my_task == master_task) then
          write(logunit,F00) 'open   : ',trim(filename)
          call shr_sys_flush(logunit)
       endif
       rcode = pio_openfile(pio_subsystem, pioid, pio_iotype, trim(filename), pio_nowrite)
       call dshr_nuopc_stream_setCurrFile(stream, fileopen=.true., currfile=trim(filename), currpioid=pioid)
    endif
    if (my_task == master_task) then
       write(logunit,*) 'file '// trim(filename),nt
    endif

    ! Always use pio to read in stream data
    call t_startf(trim(lstr)//'_readpio')
    if (my_task == master_task) then
       write(logunit,F02) 'file ' // trim(bstr) //': ',trim(filename), nt
    endif
    call pio_seterrorhandling(pioid,PIO_INTERNAL_ERROR)

    ! Loop over all stream fields in FB_stream
    call ESMF_FieldBundleGet(FB_stream, fieldCount=fieldCount, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return
    allocate(lfieldNameList(fieldCount))
    call ESMF_FieldBundleGet(FB_stream, itemNameList=lfieldNameList, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return
    do n = 1,fieldCount
       fldname = trim(lfieldnamelist(n))
       ! get varid of field n
       rcode = pio_inq_varid(pioid, fldname, varid)
       ! set frame to time index
       frame = nt
       call pio_setframe(pioid,varid,frame)
       ! set pointer rdata to field data
       call ESMF_FieldBundleGet(FB_stream, fieldName=fldname, field=lfield, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return
       call ESMF_FieldGet(field, farrayPtr=dataptr, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return
       ! read dataptr - which sets FB_stream value for stream field fldname
       call pio_read_darray(pioid, varid, pio_iodesc, dataptr, rcode)
    enddo
    call t_stopf(trim(lstr)//'_readpio')

  end subroutine dshr_nuopc_strdata_readstrm

  !===============================================================================

  logical function dshr_nuopc_strdata_meshCompare(mesh1, mesh2, method, mpicom, eps)

    !  Returns TRUE if two domains are the the same (within tolerance).

    ! !INPUT/OUTPUT PARAMETERS:
    type(ESMF_Mesh)     ,intent(in)  :: mesh1    ! 1st mesh
    type(ESMF_Mesh)     ,intent(in)  :: mesh2    ! 2nd mesh
    integer             ,intent(in)  :: method   ! selects what to compare
    integer             ,intent(in)  :: mpicom   ! mpicom
    real(R8)   ,optional,intent(in)  :: eps      ! epsilon compare value

    !--- local ---
    real(R8)    :: leps         ! local epsilon
    integer     :: n            ! counters
    integer     :: my_task,master_task
    integer     :: gsize
    integer     :: ierr
    integer     :: nlon1, nlon2, nlat1, nlat2, nmask1, nmask2  ! av field indices
    logical     :: compare      ! local compare logical
    real(R8)    :: lon1,lon2    ! longitudes to compare
    real(R8)    :: lat1,lat2    ! latitudes to compare
    real(R8)    :: msk1,msk2    ! masks to compare
    integer     :: nx,ni1,ni2   ! i grid size, i offset for 1 vs 2 and 2 vs 1
    integer     :: n1,n2,i,j    ! local indices
    integer     :: lmethod      ! local method
    logical     :: maskmethod, maskpoint ! masking on method
    character(*),parameter :: subName = '(dshr_nuopc_strdata_gridCompare) '
    character(*),parameter :: F01     = "('(dshr_nuopc_strdata_gridCompare) ',4a)"
    !-------------------------------------------------------------------------------
    !
    !-------------------------------------------------------------------------------

    call MPI_COMM_RANK(mpicom,my_task,ierr)
    master_task = 0

    leps = 1.0e-6_R8
    if (present(eps)) leps = eps

    lmethod = mod(method,100)
    if (method > 100) then
       maskmethod=.true.
    else
       maskmethod=.false.
    endif

    ! Create global owned elements

    call ESMF_MeshGet(mesh1, numOwnedElements=lsize1, rc=rc) 
    call ESMF_MeshGet(mesh2, numOwnedElements=lsize2, rc=rc) 

    call ESMF_MeshGet(mesh1, spatialDim=spatialDim, numOwnedElements=numOwnedElements, rc=rc)
    if (ChkErr(rc,__LINE__,u_FILE_u)) return
    allocate(ownedElemCoords(spatialDim*numOwnedElements))
    allocate(xc1(numOwnedElements), yc1(numOwnedElements))
    do n = 1, numOwnedElements
       xc1(n) = ownedElemCoords(2*n-1)
       yc1(n) = ownedElemCoords(2*n)
    end do

    call ESMF_MeshGet(mesh2, spatialDim=spatialDim, numOwnedElements=numOwnedElements, rc=rc)
    if (ChkErr(rc,__LINE__,u_FILE_u)) return
    allocate(ownedElemCoords(spatialDim*numOwnedElements))
    allocate(xc2(numOwnedElements), yc2(numOwnedElements))
    do n = 1, numOwnedElements
       xc2(n) = ownedElemCoords(2*n-1)
       yc2(n) = ownedElemCoords(2*n)
    end do

    ! determine global size of mesh coordinates

    call ESMF_VMAllReduce(vm, sendData=lsize1, recvData=gsize1, count=1, reduceflag=ESMF_REDUCE_SUM, rc=rc)

    call ESMF_VmGet(VM, petcount=petcount, localpet=mypet, rc=rc)
    allocate(nsizes(petcount))
    ! recvdata are the numownedElements on each pet
    allocate(recvdata(nsizes))
    allocate(senddata(1))
    senddata(1) = numOwnedElements
    call ESMF_VMGather(vm, nsize, senddata, recvdata, 1, 0, rc=rc) 

    call ESMF_VMGatherV(vm, xc1, xc1_global, recvCounts=, recvOffsets, rootPet, rc)

    if (my_task == master_task) then

       compare = .true.
       if (gsize1 /= gsize2) then
          compare = .false.
       end if

       if (.not. compare ) then
          !--- already failed the comparison test, check no futher ---
       else

          ! To compare, want to be able to treat longitude wraparound generally.
          ! So we need to compute i index offset and we need to compute the size of the nx dimension
          ! First adjust the lon so it's in the range [0,360), add 1440 to lon to take into
          ! accounts lons less than 1440.  if any lon is less than -1440, abort.  1440 is arbitrary
          ! Next, comute ni1 and ni2.  These are the offsets of grid1 relative to grid2 and
          ! grid2 relative to grid1.  The sum of those offsets is nx.  Use ni1 to offset grid2
          ! in comparison and compute new grid2 index from ni1 and nx.  If ni1 is zero, then
          ! there is no offset, don't need to compute ni2, and nx can be anything > 0.

          !--- compute offset of grid2 compared to pt 1 of grid 1
          lon1 = minval(xc1_glob)
          lon2 = minval(xc2_glob)
          if ((lon1 < -1440.0_R8) .or. (lon2 < -1440.0_R8)) then
             write(logunit,*) subname,' ERROR: lon1 lon2 lt -1440 ',lon1,lon2
             call shr_sys_abort(subname//' ERROR: lon1 lon2 lt -1440')
          endif

          lon1 = mod(xc1_glob(1) + 1440.0_R8,360.0_R8)
          lat1 = yc1_glob(1)
          ni1 = -1
          do n = 1,gsize
             lon2 = mod(xc2_glob(n) + 1440.0_R8,360.0_R8)
             lat2 = yc2_globn)
             if ((ni1 < 0) .and. abs(lon1-lon2) <= leps .and. abs(lat1-lat2) <= leps) then
                ni1 = n - 1  ! offset, compare to first gridcell in grid 1
             endif
          enddo

          if (ni1 < 0) then        ! no match for grid point 1, so fails without going further
             compare = .false.
          elseif (ni1 == 0) then   ! no offset, set nx to anything > 0
             nx = 1
          else                     ! now compute ni2
             ! compute offset of grid1 compared to pt 1 of grid 2
             lon2 = mod(xc2_glob(1) + 1440.0_R8,360.0_R8)
             lat2 = yc2_glob(1)
             ni2 = -1
             do n = 1,gsize
                lon1 = mod(xc1_glob(n) + 1440.0_R8,360.0_R8)
                lat1 = yc1_glob(n)
                if ((ni2 < 0) .and. abs(lon1-lon2) <= leps .and. abs(lat1-lat2) <= leps) then
                   ni2 = n - 1  ! offset, compare to first gridcell in grid 1
                endif
             enddo
             if (ni2 < 0) then
                write(logunit,*) subname,' ERROR in ni2 ',ni1,ni2
                call shr_sys_abort(subname//' ERROR in ni2')
             endif
             nx = ni1 + ni2
          endif

          if (compare) then
             do n = 1,gsize
                j = ((n-1)/nx) + 1
                i = mod(n-1,nx) + 1
                n1 = (j-1)*nx + mod(n-1,nx) + 1
                n2 = (j-1)*nx + mod(n-1+ni1,nx) + 1
                if (n1 /= n) then    ! sanity check, could be commented out
                   write(logunit,*) subname,' ERROR in n1 n2 ',n,i,j,n1,n2
                   call shr_sys_abort(subname//' ERROR in n1 n2')
                endif
                lon1 = mod(avG1%rAttr(nlon1,n1)+1440.0_R8,360.0_R8)
                lat1 = avG1%rAttr(nlat1,n1)
                lon2 = mod(avG2%rAttr(nlon2,n2)+1440.0_R8,360.0_R8)
                lat2 = avG2%rAttr(nlat2,n2)
                msk1 = avG1%rAttr(nmask1,n1)
                msk2 = avG2%rAttr(nmask2,n2)

                maskpoint = .true.
                if (maskmethod .and. (msk1 == 0 .or. msk2 == 0)) then
                   maskpoint = .false.
                endif

                if (maskpoint) then
                   if (lmethod == dshr_nuopc_strdata_gridCompareXYabs      ) then
                      if (abs(lon1 - lon2) > leps) compare = .false.
                      if (abs(lat1 - lat2) > leps) compare = .false.
                   else if (lmethod == dshr_nuopc_strdata_gridCompareXYrel      ) then
                      if (rdiff(lon1,lon2) > leps) compare = .false.
                      if (rdiff(lat1,lat2) > leps) compare = .false.
                   else if (lmethod == dshr_nuopc_strdata_gridCompareMaskIdent  ) then
                      if (msk1 /= msk2)compare = .false.
                   else if (lmethod == dshr_nuopc_strdata_gridCompareMaskZeros  ) then
                      if (msk1 == 0 .and. msk2 /= 0) compare = .false.
                      if (msk1 /= 0 .and. msk2 == 0) compare = .false.
                   else if (lmethod == dshr_nuopc_strdata_gridCompareMaskSubset ) then
                      if (msk1 /= 0 .and. msk2 == 0) compare = .false.
                   else
                      write(logunit,F01) "ERROR: compare method not recognized, method = ",method
                      call shr_sys_abort(subName//"ERROR: compare method not recognized")
                   endif  ! lmethod
                endif  ! maskpoint
             enddo ! gsize
          endif  ! compare
       endif   ! compare
    endif   ! master_task

    call shr_mpi_bcast(compare,mpicom)
    dshr_nuopc_strdata_gridCompare = compare

    return

    !-------------------------------------------------------------------------------
  contains   ! internal subprogram
    !-------------------------------------------------------------------------------

    real(R8) function rdiff(v1,v2) ! internal function
      !------------------------------------------
      real(R8),intent(in) :: v1,v2                 ! two values to compare
      real(R8),parameter  :: c0           = 0.0_R8 ! zero
      real(R8),parameter  :: large_number = 1.0e20_R8 ! infinity
      !------------------------------------------
      if (v1 == v2) then
         rdiff = c0
      elseif (v1 == c0 .and. v2 /= c0) then
         rdiff = large_number
      elseif (v2 == c0 .and. v1 /= c0) then
         rdiff = large_number
      else
         !        rdiff = abs((v2-v1)/v1)   ! old version, but rdiff(v1,v2) /= vdiff(v2,v1)
         rdiff = abs(2.0_R8*(v2-v1)/(v1+v2))
      endif
      !------------------------------------------
    end function rdiff

  end function dshr_nuopc_strdata_gridCompare

end module dshr_nuopc_strdata_mod
