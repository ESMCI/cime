.. _data-river:

Data River (DROF)
=================

---------
Namelists
---------
The data river runoff model (DROF) provides data river input to prognostic components such as the ocean.

The namelist file for DROF is ``drof_in``.

As is the case for all data models, DROF namelists can be separated into two groups, stream-independent and stream-dependent. 

The stream dependent group is :ref:`shr_strdata_nml<input-streams>`. 

The stream-independent group is ``drof_nml`` and the DROF stream-independent namelist variables are:

=====================  ======================================================
decomp                 decomposition strategy (1d, root)
    
                       1d => vector decomposition, root => run on master task
restfilm               master restart filename 
restfils               stream restart filename 
force_prognostic_true  TRUE => force prognostic behavior
=====================  ======================================================

To change the namelist settings in drof_in, edit the file user_nl_drof. 

---------------
XML variables
---------------
The following are xml variables that CIME supports for DROF.  These variables will appear in ``env_run.xml`` and are used by the DROF ``cime_config/buildnml`` script to generate the DROF namelist file ``drof_in`` and the required associated stream files for the case.

===================== =============================================================================== 
DROF_MODE             Data mode
DROF_CPLHIST_CASE     Coupler history data mode case name 
DROF_CPLHIST_DIR      Coupler history data mode directory containing coupler history data 
DROF_CPLHIST_YR_ALIGN Coupler history data model simulation year corresponding to data starting year 
DROF_CPLHIST_YR_START Coupler history data model starting year to loop data over
DROF_CPLHIST_YR_END   Coupler history data model ending year to loop data over
===================== =============================================================================== 

------
Fields
------
The pre-defined internal field names in the data river runoff model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data river runoff model.

=========       ========       =====
(/ "roff        ","ioff        "/)
=========       ========       =====
