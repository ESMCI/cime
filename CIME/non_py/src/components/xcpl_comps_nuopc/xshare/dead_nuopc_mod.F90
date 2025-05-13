module dead_nuopc_mod

  use ESMF              , only : ESMF_Gridcomp, ESMF_State, ESMF_StateGet
  use ESMF              , only : ESMF_Clock, ESMF_Time, ESMF_TimeInterval, ESMF_Alarm
  use ESMF              , only : ESMF_GridCompGet, ESMF_ClockGet, ESMF_ClockSet, ESMF_ClockAdvance, ESMF_AlarmSet
  use ESMF              , only : ESMF_SUCCESS, ESMF_LogWrite, ESMF_LOGMSG_INFO, ESMF_METHOD_INITIALIZE
  use ESMF              , only : ESMF_FAILURE, ESMF_LOGMSG_ERROR
  use ESMF              , only : ESMF_VMGetCurrent, ESMF_VM, ESMF_VMBroadcast, ESMF_VMGet
  use ESMF              , only : ESMF_VM, ESMF_VMGetCurrent, ESMF_VmGet
  use ESMF              , only : operator(/=), operator(==), operator(+)
  use shr_kind_mod      , only : r8=>shr_kind_r8, i8=>shr_kind_i8, cl=>shr_kind_cl, cs=>shr_kind_cs
  use shr_sys_mod       , only : shr_sys_abort
  use dead_methods_mod  , only : chkerr, alarmInit

  implicit none
  private

  public :: dead_read_inparms
  public :: ModelInitPhase
  public :: ModelSetRunClock
  public :: fld_list_add
  public :: fld_list_realize

  ! !PUBLIC DATA MEMBERS:
  type fld_list_type
    character(len=128) :: stdname
     integer :: ungridded_lbound = 0
     integer :: ungridded_ubound = 0
  end type fld_list_type
  public :: fld_list_type

  integer, parameter, public :: fldsMax = 100
  integer                    :: dbug_flag = 0
  character(*), parameter    :: u_FILE_u = &
       __FILE__

!===============================================================================
contains
!===============================================================================

  subroutine dead_read_inparms(model, inst_suffix, logunit, nxg, nyg)

    ! input/output variables
    character(len=*) , intent(in)    :: model
    character(len=*) , intent(in)    :: inst_suffix ! char string associated with instance
    integer          , intent(in)    :: logunit     ! logging unit number
    integer          , intent(out)   :: nxg         ! global dim i-direction
    integer          , intent(out)   :: nyg         ! global dim j-direction

    ! local variables
    type(ESMF_VM)           :: vm
    character(CL)           :: fileName ! generic file name
    integer                 :: nunit    ! unit number
    integer                 :: unitn    ! Unit for namelist file
    integer                 :: tmp(2)   ! array for broadcast
    integer                 :: localPet ! mpi id of current task in current context
    integer                 :: rc       ! return code
    character(*), parameter :: F00   = "('(dead_read_inparms) ',8a)"
    character(*), parameter :: F01   = "('(dead_read_inparms) ',a,a,4i8)"
    character(*), parameter :: F03   = "('(dead_read_inparms) ',a,a,i8,a)"
    character(*), parameter :: subName = "(dead_read_inpamrs) "
    !-------------------------------------------------------------------------------

    ! read the input parms (used to configure model)
    call ESMF_VMGetCurrent(vm, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return
    call ESMF_VMGet(vm, localPet=localPet, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

    nxg = -9999
    nyg = -9999

    if (localPet==0) then
       open(newunit=unitn, file='x'//model//'_in'//trim(inst_suffix), status='old' )
       read(unitn,*) nxg
       read(unitn,*) nyg
       close (unitn)
    endif

    tmp(1) = nxg
    tmp(2) = nyg
    call ESMF_VMBroadcast(vm, tmp, 3, 0, rc=rc)
    nxg = tmp(1)
    nyg = tmp(2)

    if (localPet==0) then
       write(logunit,*)' Read in X'//model//' input from file= x'//model//'_in'
       write(logunit,F00) model
       write(logunit,F00) model,'         Model  :  ',model
       write(logunit,F01) model,'           NGX  :  ',nxg
       write(logunit,F01) model,'           NGY  :  ',nyg
       write(logunit,F00) model,'    inst_suffix :  ',trim(inst_suffix)
       write(logunit,F00) model
    end if

  end subroutine dead_read_inparms

  !===============================================================================
  subroutine fld_list_add(num, fldlist, stdname, ungridded_lbound, ungridded_ubound)

    ! input/output variables
    integer                    , intent(inout) :: num
    type(fld_list_type)        , intent(inout) :: fldlist(:)
    character(len=*)           , intent(in)    :: stdname
    integer,          optional , intent(in)    :: ungridded_lbound
    integer,          optional , intent(in)    :: ungridded_ubound

    ! local variables
    character(len=*), parameter :: subname='(dead_nuopc_mod:fld_list_add)'
    !-------------------------------------------------------------------------------

    ! Set up a list of field information
    num = num + 1
    if (num > fldsMax) then
       call ESMF_LogWrite(trim(subname)//": ERROR num > fldsMax "//trim(stdname), &
            ESMF_LOGMSG_ERROR, line=__LINE__, file=__FILE__)
       return
    endif
    fldlist(num)%stdname = trim(stdname)

    if (present(ungridded_lbound) .and. present(ungridded_ubound)) then
       fldlist(num)%ungridded_lbound = ungridded_lbound
       fldlist(num)%ungridded_ubound = ungridded_ubound
    end if

  end subroutine fld_list_add

  !===============================================================================
  subroutine fld_list_realize(state, fldList, numflds, flds_scalar_name, flds_scalar_num, mesh, tag, rc)

    use NUOPC , only : NUOPC_IsConnected, NUOPC_Realize
    use ESMF  , only : ESMF_MeshLoc_Element, ESMF_FieldCreate, ESMF_TYPEKIND_R8
    use ESMF  , only : ESMF_MAXSTR, ESMF_Field, ESMF_State, ESMF_Mesh, ESMF_StateRemove
    use ESMF  , only : ESMF_LogFoundError, ESMF_LOGMSG_INFO, ESMF_SUCCESS
    use ESMF  , only : ESMF_LogWrite, ESMF_LOGMSG_ERROR, ESMF_LOGERR_PASSTHRU

    type(ESMF_State)    , intent(inout) :: state
    type(fld_list_type) , intent(in)    :: fldList(:)
    integer             , intent(in)    :: numflds
    character(len=*)    , intent(in)    :: flds_scalar_name
    integer             , intent(in)    :: flds_scalar_num
    character(len=*)    , intent(in)    :: tag
    type(ESMF_Mesh)     , intent(in)    :: mesh
    integer             , intent(inout) :: rc

    ! local variables
    integer           :: n
    type(ESMF_Field)  :: field
    character(len=80) :: stdname
    integer           :: gridtoFieldMap=2
    character(len=*),parameter  :: subname='(dead_nuopc_mod:fld_list_realize)'
    ! ----------------------------------------------

    rc = ESMF_SUCCESS

    do n = 1, numflds
       stdname = fldList(n)%stdname
       if (NUOPC_IsConnected(state, fieldName=stdname)) then
          if (stdname == trim(flds_scalar_name)) then
             call ESMF_LogWrite(trim(subname)//trim(tag)//" Field = "//trim(stdname)//" is connected on root pe", &
                  ESMF_LOGMSG_INFO)
             ! Create the scalar field
             call SetScalarField(field, flds_scalar_name, flds_scalar_num, rc=rc)
             if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, line=__LINE__, file=u_FILE_u)) return
          else
             call ESMF_LogWrite(trim(subname)//trim(tag)//" Field = "//trim(stdname)//" is connected using mesh", &
                  ESMF_LOGMSG_INFO)
             ! Create the field
             if (fldlist(n)%ungridded_lbound > 0 .and. fldlist(n)%ungridded_ubound > 0) then
                field = ESMF_FieldCreate(mesh, ESMF_TYPEKIND_R8, name=stdname, meshloc=ESMF_MESHLOC_ELEMENT, &
                     ungriddedLbound=(/fldlist(n)%ungridded_lbound/), &
                     ungriddedUbound=(/fldlist(n)%ungridded_ubound/), &
                     gridToFieldMap=(/gridToFieldMap/), rc=rc)
                if (chkerr(rc,__LINE__,u_FILE_u)) return
             else
                field = ESMF_FieldCreate(mesh, ESMF_TYPEKIND_R8, name=stdname, meshloc=ESMF_MESHLOC_ELEMENT, rc=rc)
                if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, line=__LINE__, file=u_FILE_u)) return
             end if
          endif

          ! NOW call NUOPC_Realize
          call NUOPC_Realize(state, field=field, rc=rc)
          if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, line=__LINE__, file=u_FILE_u)) return
       else
          if (stdname /= trim(flds_scalar_name)) then
             call ESMF_LogWrite(subname // trim(tag) // " Field = "// trim(stdname) // " is not connected.", &
                  ESMF_LOGMSG_INFO)
             call ESMF_StateRemove(state, (/stdname/), rc=rc)
             if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, line=__LINE__, file=u_FILE_u)) return
          end if
       end if
    end do

  contains  !- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    subroutine SetScalarField(field, flds_scalar_name, flds_scalar_num, rc)
      ! ----------------------------------------------
      ! create a field with scalar data on the root pe
      ! ----------------------------------------------

      use ESMF, only : ESMF_Field, ESMF_DistGrid, ESMF_Grid
      use ESMF, only : ESMF_DistGridCreate, ESMF_GridCreate, ESMF_LogFoundError, ESMF_LOGERR_PASSTHRU
      use ESMF, only : ESMF_FieldCreate, ESMF_GridCreate, ESMF_TYPEKIND_R8

      type(ESMF_Field) , intent(inout) :: field
      character(len=*) , intent(in)    :: flds_scalar_name
      integer          , intent(in)    :: flds_scalar_num
      integer          , intent(inout) :: rc

      ! local variables
      type(ESMF_Distgrid) :: distgrid
      type(ESMF_Grid)     :: grid
      character(len=*), parameter :: subname='(dead_nuopc_mod:SetScalarField)'
      ! ----------------------------------------------

      rc = ESMF_SUCCESS

      ! create a DistGrid with a single index space element, which gets mapped onto DE 0.
      distgrid = ESMF_DistGridCreate(minIndex=(/1/), maxIndex=(/1/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, line=__LINE__, file=u_FILE_u)) return

      grid = ESMF_GridCreate(distgrid, rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, line=__LINE__, file=u_FILE_u)) return

      field = ESMF_FieldCreate(name=trim(flds_scalar_name), grid=grid, typekind=ESMF_TYPEKIND_R8, &
           ungriddedLBound=(/1/), ungriddedUBound=(/flds_scalar_num/), gridToFieldMap=(/2/), rc=rc)
      if (ESMF_LogFoundError(rcToCheck=rc, msg=ESMF_LOGERR_PASSTHRU, line=__LINE__, file=u_FILE_u)) return

    end subroutine SetScalarField

  end subroutine fld_list_realize

  !===============================================================================
  subroutine ModelInitPhase(gcomp, importState, exportState, clock, rc)

    use NUOPC, only : NUOPC_CompFilterPhaseMap

    type(ESMF_GridComp)   :: gcomp
    type(ESMF_State)      :: importState, exportState
    type(ESMF_Clock)      :: clock
    integer, intent(out)  :: rc
    !-------------------------------------------------------------------------------

    rc = ESMF_SUCCESS

    ! Switch to IPDv01 by filtering all other phaseMap entries
    call NUOPC_CompFilterPhaseMap(gcomp, ESMF_METHOD_INITIALIZE, acceptStringList=(/"IPDv01p"/), rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

  end subroutine ModelInitPhase

  !===============================================================================
  subroutine ModelSetRunClock(gcomp, rc)

    use ESMF        , only : ESMF_ClockGetAlarmList, ESMF_ALARMLIST_ALL
    use NUOPC_Model , only : NUOPC_ModelGet
    use NUOPC       , only : NUOPC_CompAttributeGet

    ! input/output variables
    type(ESMF_GridComp)  :: gcomp
    integer, intent(out) :: rc

    ! local variables
    type(ESMF_Clock)         :: mclock, dclock
    type(ESMF_Time)          :: mcurrtime, dcurrtime
    type(ESMF_Time)          :: mstoptime
    type(ESMF_TimeInterval)  :: mtimestep, dtimestep
    character(len=256)       :: cvalue
    character(len=256)       :: restart_option       ! Restart option units
    integer                  :: restart_n            ! Number until restart interval
    integer                  :: restart_ymd          ! Restart date (YYYYMMDD)
    type(ESMF_ALARM)         :: restart_alarm
    character(len=128)       :: name
    integer                  :: alarmcount
    character(len=*),parameter :: subname='dead_nuopc_mod:(ModelSetRunClock) '
    !-------------------------------------------------------------------------------

    rc = ESMF_SUCCESS

    ! query the Component for its clocks
    call NUOPC_ModelGet(gcomp, driverClock=dclock, modelClock=mclock, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

    call ESMF_ClockGet(dclock, currTime=dcurrtime, timeStep=dtimestep, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

    call ESMF_ClockGet(mclock, currTime=mcurrtime, timeStep=mtimestep, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

    !--------------------------------
    ! force model clock currtime and timestep to match driver and set stoptime
    !--------------------------------

    mstoptime = mcurrtime + dtimestep
    call ESMF_ClockSet(mclock, currTime=dcurrtime, timeStep=dtimestep, stopTime=mstoptime, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

    !--------------------------------
    ! set restart alarm
    !--------------------------------

    call ESMF_ClockGetAlarmList(mclock, alarmlistflag=ESMF_ALARMLIST_ALL, alarmCount=alarmCount, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

    if (alarmCount == 0) then

       call ESMF_GridCompGet(gcomp, name=name, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return
       call ESMF_LogWrite(subname//'setting alarms for' // trim(name), ESMF_LOGMSG_INFO)

       call NUOPC_CompAttributeGet(gcomp, name="restart_option", value=restart_option, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return

       call NUOPC_CompAttributeGet(gcomp, name="restart_n", value=cvalue, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return
       read(cvalue,*) restart_n

       call NUOPC_CompAttributeGet(gcomp, name="restart_ymd", value=cvalue, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return
       read(cvalue,*) restart_ymd

       call alarmInit(mclock, restart_alarm, restart_option, &
            opt_n   = restart_n,           &
            opt_ymd = restart_ymd,         &
            RefTime = mcurrTime,           &
            alarmname = 'alarm_restart', rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return

       call ESMF_AlarmSet(restart_alarm, clock=mclock, rc=rc)
       if (chkerr(rc,__LINE__,u_FILE_u)) return

    end if

    !--------------------------------
    ! Advance model clock to trigger alarms then reset model clock back to currtime
    !--------------------------------

    call ESMF_ClockAdvance(mclock,rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

    call ESMF_ClockSet(mclock, currTime=dcurrtime, timeStep=dtimestep, stopTime=mstoptime, rc=rc)
    if (chkerr(rc,__LINE__,u_FILE_u)) return

  end subroutine ModelSetRunClock

end module dead_nuopc_mod
