.. _data-seaice:

Data Ice (DICE)
================

---------
Namelists
---------
DICE is a combination of a data model and a prognostic model. 
The data functionality reads in ice coverage. 
The prognostic functionality calculates the ice/atmosphere and ice/ocean fluxes. 
DICE receives the same atmospheric input from the coupler as the active CICE model (i.e., atmospheric  states, shortwave fluxes, and ocean ice melt flux) and acts very similarly to CICE running in prescribed mode. 
Currently, this component is only used to drive POP in "C" compsets.

The namelist file for DICE is ``dice_in`` (or ``dice_in_NNN`` for multiple instances).

As is the case for all data models, DICE namelists can be separated into two groups, stream-independent and stream-dependent. 

The stream dependent group is :ref:`shr_strdata_nml<input-streams>`. 

The stream-independent group is ``dice_nml`` and the DICE stream-independent namelist variables are:

=====================  ======================================================
decomp                 decomposition strategy (1d, root)
    
                       1d => vector decomposition, root => run on master task
flux_qacc              activates water accumulation/melt wrt Q
flux_qacc0             initial water accumulation value
flux_qmin              bound on melt rate
flux_swpf              short-wave penetration factor
restfilm               master restart filename 
restfils               stream restart filename 
force_prognostic_true  TRUE => force prognostic behavior
=====================  ======================================================

To change the namelist settings in ``dice_in``, edit the file ``user_nl_dice``. 

---------------
XML variables
---------------
The following are xml variables that CIME supports for DICE.  These variables will appear in ``env_run.xml`` and are used by the DICE ``cime_config/buildnml`` script to generate the DICE namelist file ``dice_in`` and the required associated stream files for the case.

===================== =============================================================================== 
DLND_MODE             Data mode
===================== =============================================================================== 

If DICE_MODE is set to ``SSMI`` or ``SSMI_IAF``, it is a prognostic mode.
It requires data be sent to the ice model.
Ice fraction (extent) data is read from an input stream, atmosphere state variables are received from the coupler, and then an atmosphere-ice surface flux is computed and sent to the coupler. 
Normally the ice fraction data is found in the same data files that provide SST data to the data ocean model. 
They are normally found in the same file because the SST and ice fraction data are derived from the same observational data sets and are consistent with each other.

------
Fields
------
The pre-defined internal field names in the data ice model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data ocean model.

=========          ==========         =========          ==========         ======== 
(/"to              ","s               ","uo              ","vo              ", &
"dhdx              ","dhdy            ","q               ","z               ", &
"ua                ","va              ","ptem            ","tbot            ", &
"shum              ","dens            ","swndr           ","swvdr           ", &
"swndf             ","swvdf           ","lwdn            ","rain            ", &
"snow              ","t               ","tref            ","qref            ", &
"ifrac             ","avsdr           ","anidr           ","avsdf           ", &
"anidf             ","tauxa           ","tauya           ","lat             ", &
"sen               ","lwup            ","evap            ","swnet           ", &
"swpen             ","melth           ","meltw           ","salt            ", &
"tauxo             ","tauyo           " /)
=========          ==========         =========          ==========         ========
