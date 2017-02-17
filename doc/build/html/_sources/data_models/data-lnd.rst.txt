.. _data-lnd:

Data Land (DLND)
================

---------
Namelists
---------
The land model is unique because it supports land data and snow data (*lnd and sno*) almost as if they were two separate components, but they are in fact running in one component model through one interface. 
The lnd (land) data consist of fields sent to the atmosphere. 
This set of data is used when running dlnd with an active atmosphere. 
In general this is not a mode that is used or supported.
The sno (snow) data consist of fields sent to the glacier model. This set of data is used when running dlnd with an active glacier model (TG compsets). Both sets of data are assumed to be on the same grid.

The namelist file for DLND is ``dlnd_in`` (or ``dlnd_in_NNN`` for multiple instances).

As is the case for all data models, DLND namelists can be separated into two groups, stream-independent and stream-dependent. 

The stream dependent group is :ref:`shr_strdata_nml<input-streams>`. 

The stream-independent group is ``dlnd_nml`` and the DLND stream-independent namelist variables are:

=====================  ======================================================
decomp                 decomposition strategy (1d, root)
    
                       1d => vector decomposition, root => run on master task
restfilm               master restart filename 
restfils               stream restart filename 
force_prognostic_true  TRUE => force prognostic behavior
=====================  ======================================================
   
To change the namelist settings in dlnd_in, edit the file user_nl_dlnd. 

---------------
XML variables
---------------
The following are xml variables that CIME supports for DLND.  These variables will appear in ``env_run.xml`` and are used by the DLND ``cime_config/buildnml`` script to generate the DLND namelist file ``dlnd_in`` and the required associated stream files for the case.

===================== =============================================================================== 
DLND_MODE             Data mode
DLND_CPLHIST_CASE     Coupler history data mode case name 
DLND_CPLHIST_DIR      Coupler history data mode directory containing coupler history data 
DLND_CPLHIST_YR_ALIGN Coupler history data model simulation year corresponding to data starting year 
DLND_CPLHIST_YR_START Coupler history data model starting year to loop data over
DLND_CPLHIST_YR_END   Coupler history data model ending year to loop data over
===================== =============================================================================== 

------
Fields
------
The pre-defined internal field names in the data land model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data land model.

============    ==========     ==========     ==========     =========      =====
(/ "t           ","tref        ","qref        ","avsdr       ","anidr       ", &
   "avsdf       ","anidf       ","snowh       ","taux        ","tauy        ", &
   "lat         ","sen         ","lwup        ","evap        ","swnet       ", &
   "lfrac       ","fv          ","ram1        ",                               &
   "flddst1     ","flxdst2     ","flxdst3     ","flxdst4     "               , &
   "tsrfNN      ","topoNN      ","qiceNN      "                                /)
============    ==========     ==========     ==========     =========      =====

where NN = (01,02,...,``nflds_snow * glc_nec)``, and ``nflds_snow`` is the number of snow fields in 
each elevation class and ``glc_nec`` is the number of elevation classes. 

