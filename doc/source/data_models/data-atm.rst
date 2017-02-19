.. _data-atm:

Data Atmosphere (DATM)
======================

DATM is normally used to provide observational forcing data (or forcing data produced by a previous run using active components) to drive prognostic components.
In the case of CESM, these would be: CLM (I compset), POP2 (C compset), and POP2/CICE (G compset). 
As a result, DATM variable settings are specific to the compset that will be targeted.
As examples, CORE2_NYF (CORE2 normal year forcing) is the DATM mode used in C and G compsets. 
CLM_QIAN, CLMCRUNCEP, CLMGSWP3 and CLM1PT are DATM modes using observational data for forcing CLM in I compsets.

---------
Namelists
---------

The DATM namelist file is ``datm_in`` (or ``datm_in_NNN`` for multiple instances). DATM namelists can be separated into two groups: *stream-independent* namelist variables that are specific to the DATM model and *stream-specific* namelist variables whose names are common to all the data models. 

Stream dependent input is in the namelist group ``"shr_strdata_nml`` which is discussed in :ref:`input streams <input-streams>` and is the same for all data models.

.. _datm-stream-independent-namelists:

The stream-independent group is ``datm_nml`` and the DATM stream-independent namelist variables are:

=====================  =============================================================================================
datm_nml vars          description
=====================  =============================================================================================
decomp                 decomposition strategy (1d, root)
    
                       1d => vector decomposition, root => run on master task
restfilm               master restart filename 
restfils               stream restart filename 
force_prognostic_true  TRUE => force prognostic behavior
bias_correct           if set, include bias correction streams in namelist
anomaly_forcing        if set, includ anomaly forcing streams in namelist
factorfn               filename containing correction factors for use in CORE2 modes (CORE2_IAF and CORE2_NYF) 
presaero               if true, prescribed aerosols are sent from datm 
iradsw                 frequency to update radiation in number of time steps (of hours if negative)
wiso_datm              if true, turn on water isotopes   
=====================  =============================================================================================

.. _datm-xml-vars:

---------------
XML variables
---------------
The following are ``$CASEROOT`` xml variables that CIME supports for DATM.  These variables will appear in ``env_run.xml`` and the resulting values are compset dependent.

.. note:: These xml variables are used by the the datm's **cime_config/buildnml** script in conjunction with datm's **cime_config/namelist_definition_datm.xml** file to generate the namelist file ``datm_in``.

===================== =============================================================================== 
XML variable          Description
===================== =============================================================================== 
DATM_MODE             Mode for atmospheric component 
DATM_PRESAERO         Prescribed aerosol forcing, if any
DATM_TOPO             Surface topography
DATM_CO2_TSERIES      CO2 time series type
DATM_CPLHIST_CASE     Coupler history data mode case name 
DATM_CPLHIST_DIR      Coupler history data mode directory containing coupler history data 
DATM_CPLHIST_YR_ALIGN Coupler history data model simulation year corresponding to data starting year 
DATM_CPLHIST_YR_START Coupler history data model starting year to loop data over
DATM_CPLHIST_YR_END   Coupler history data model ending year to loop data over
DATM_CLMNCEP_YR_ALIGN I compsets only - simulation year corresponding to data starting year 
DATM_CPLHIST_YR_START I compsets only - data model starting year to loop data over
DATM_CPLHIST_YR_END   I compsets only - data model ending year to loop data over
===================== =============================================================================== 

In the above table, ``$DATM_MODE`` has the following supported settings:

============================ ==========================================================================================================================
DATM_MODE value              Description 
============================ ==========================================================================================================================
NULL                         null mode
CORE2_NYF                    CORE2 normal year forcing (C ang G compsets)
CORE2_IAF                    CORE2 interannual year forcing (C ang G compsets)
WW3                          WW3 wave watch data from a short period of hi WW3 wave watch data from a short period of hi temporal frequency COREv2 data
CLM_QIAN_WISO                QIAN atm input data with water isotopes (I compsets)
CLM_QIAN                     QIAN atm input data (I compsets)
CLMCRUNCEP                   CRUNCEP atm input data (I compsets) 
CLMGSWP3                     GSWP3 atm input data (I compsets)
CLM1PT                       single point tower site atm input data
COPYALL_NPS_v1               copy mode
COPYALL_NPS_CORE2_v1         copy mode for CORE2 forcing
CPLHIST3HrWx                 user generated forcing data to spinup I compsets 
CPLHISTForcingForOcnIce      user generated forcing data to spinup G compsets
============================ ==========================================================================================================================

.. _datm-datamodes:

-------------------
Datamode values
-------------------

One of the variables in ``shr_strdata_nml`` is the ``datamode``, whose value is a character string. 
Each data model has a unique set of ``datamode`` values that it supports. 

The valid values for ``datamode`` are set by the xml variable ``DATM_MODE`` in the ``config_component.xml`` file for DATM. 
CIME will generate a value ``datamode`` that is compset dependent. 

The following are the supported DATM datamode values and their relationship to the ``$DATM_MODE`` xml variable value.

===================    =============================================================================================================================
datamode value         XML variable value
===================    =============================================================================================================================
NULL                   NULL

                       This mode turns off the data model as a provider of data to the coupler. 
                       The ``atm_present`` flag will be set to ``false`` and the coupler assumes no exchange of data to or from the data model.

CLMNCEP                CLM_QIAN_WISO, CLM_QIAN, CLMCRUNCEP, CLMGSWP3, CLM1PT, NLDAS  
CORE2_NYF              CORE2_NYF
CORE2_IAF              CORE2_IAF
COPYALL                COPYALL_NPS_v1, COPYALL_NPS_CORE2_v1, WW3

                       Examines the fields found in all input data streams and if any input field names match the field names used internally, 
  		       they  are copied into the export array and passed directly to the coupler  without any special user code.  
   		       Any required fields not found on an input stream will be set to zero except for aerosol deposition fields which will be 
		       set to a special value.  

CPLHIST                CPLHIST3HrWx, CPLHISTForcingForOcnIce

                       Utilize user-generated coupler history data to spin up prognostic component
===================    =============================================================================================================================

.. _datm-mode-independent-streams:

---------------------------------
Datamode independent streams
---------------------------------

In general, each DATM datamode is identified with a unique set of streams. 
However, there are several mode-independent streams in DATM that can accompany any target datamode setting.
Currently, these are streams associated with prescribed aerosols, co2 time series, topography, anomoly forcing and bias correction.
These mode-independent streams are activated different, depending on the stream.

- ``prescribed aerosol stream:``
  To add this stream, set ``$DATM_PRESAERO`` to a supported value other than ``none``. 

- ``co2 time series stream``:
  To add this stream, set ``$DATM_CO2_TSERIES`` to a supported value other than ``none``.
  
- ``topo stream``:
  To add this stream, set ``$DATM_TOPO`` to a supported value other than ``none``.

- ``anomaly forcing stream:``
  To add this stream, you need to add any of the following keywword/value pair to the end of ``user_nl_datm``:
  ::  

    Anomaly.Forcing.Precip = <filename>
    Anomaly.Forcing.Temperature = <filename>
    Anomaly.Forcing.Pressure = <filename>
    Anomaly.Forcing.Humidity = <filename>
    Anomaly.Forcing.Uwind = <filename>
    Anomaly.Forcing.Vwind = <filename>
    Anomaly.Forcing.Shortwave = <filename>
    Anomaly.Forcing.Longwave = <filename>

- ``bias_correct stream:``
  To add this stream, you need to add any of the following keywword/value pair to the end of ``user_nl_datm``:
  ::  

   BC.QIAN.CMAP.Precip = <filename>
   BC.QIAN.GPCP.Precip = <filename>
   BC.CRUNCEP.CMAP.Precip = <filename>
   BC.CRUNCEP.GPCP.Precip = <filename>


.. _datm-fields:

------
Fields
------
The pre-defined internal field names in the data atmosphere model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data atmosphere model.

===========      ==============     ==============     ==============     =====
"z               ","topo            ", &
"u               ","v               ","tbot            ", &
"ptem            ","shum            ","dens            ","pbot            ", &
"pslv            ","lwdn            ","rainc           ","rainl           ", &
"snowc           ","snowl           ","swndr           ","swvdr           ", &
"swndf           ","swvdf           ","swnet           ","co2prog         ", &
"co2diag         ","bcphidry        ","bcphodry        ","bcphiwet        ", &
"ocphidry        ","ocphodry        ","ocphiwet        ","dstwet1         ", &
"dstwet2         ","dstwet3         ","dstwet4         ","dstdry1         ", &
"dstdry2         ","dstdry3         ","dstdry4         ",                    &
"tref            ","qref            ","avsdr           ","anidr           ", &
"avsdf           ","anidf           ","ts              ","to              ", &
"snowhl          ","lfrac           ","ifrac           ","ofrac           ", &
"taux            ","tauy            ","lat             ","sen             ", &
"lwup            ","evap            ","co2lnd          ","co2ocn          ", &
"dms             ","precsf          ", &
"prec_af         ","u_af            ","v_af            ","tbot_af         ", &
"pbot_af         ","shum_af         ","swdn_af         ","lwdn_af         ", &
"rainc_18O       ","rainc_HDO       ","rainl_18O       ","rainl_HDO       ", &
"snowc_18O       ","snowc_HDO       ","snowl_18O       ","snowl_HDO       ", &
"shum_16O        ","shum_18O        ","shum_HDO        "/)
===========      ==============     ==============     ==============     =====



