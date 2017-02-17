.. _data-atm:

Data Atmosphere (DATM)
======================

---------
Namelists
---------

The DATM namelist file is ``datm_in`` (or ``datm_in_NNN`` for multiple instances). DATM namelists can be separated into two groups: *stream-independent* namelist variables that are specific to the DATM model and *stream-specific* namelist variables whose names are common to all the data models. 

Stream independent input is in the namelist group ``datm_nml``. 

Stream dependent input is in the namelist group ``"shr_strdata_nml`` which is discussed in :ref:`input streams <input-streams>` and is the same for all data models.

One of the variables in shr_strdata_nml is the ``datamode``, whose value is a character string. 
Each data model has a unique set of ``datamode`` values that it supports. 
The valid values for ``datamode`` are set by the xml variable ``DATM_MODE`` in the ``config_component.xml`` file for DATM. 
CIME will generate a value ``datamode`` that is compset dependent. 
As examples, CORE2_NYF (CORE2 normal year forcing) is the DATM mode used in C and G compsets. 
CLM_QIAN, CLMCRUNCEP, CLMGSWP3 and CLM1PT are DATM modes using observational data for forcing CLM in I compsets.

---------------
XML variables
---------------
The following are xml variables that CIME supports for DATM.  These variables will appear in ``env_run.xml`` and the resulting values are compset dependent.

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



