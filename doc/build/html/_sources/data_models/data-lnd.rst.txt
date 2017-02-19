.. _data-lnd:

Data Land (DLND)
================

The land model is unique because it supports land data and snow data (*lnd and sno*) almost as if they were two separate components, but they are in fact running in one component model through one interface. 
The lnd (land) data consist of fields sent to the atmosphere. 
This set of data is used when running DLND with an active atmosphere. 
In general this is not a mode that is used or supported.
The sno (snow) data consist of fields sent to the glacier model. This set of data is used when running dlnd with an active glacier model (TG compsets). Both sets of data are assumed to be on the same grid.

---------
Namelists
---------

The namelist file for DLND is ``dlnd_in`` (or ``dlnd_in_NNN`` for multiple instances).

As is the case for all data models, DLND namelists can be separated into two groups, stream-independent and stream-dependent. 

The stream dependent group is :ref:`shr_strdata_nml<input-streams>`. 

.. _dlnd-stream-independent-namelists:

The stream-independent group is ``dlnd_nml`` and the DLND stream-independent namelist variables are:

=====================  ======================================================
decomp                 decomposition strategy (1d, root)
    
                       1d => vector decomposition, root => run on master task
restfilm               master restart filename 
restfils               stream restart filename 
force_prognostic_true  TRUE => force prognostic behavior
=====================  ======================================================
   
To change the namelist settings in dlnd_in, edit the file user_nl_dlnd. 

.. _dlnd-xml-vars:

---------------
XML variables
---------------
The following are xml variables that CIME supports for DLND.  These variables will appear in ``env_run.xml`` and are used by the DLND ``cime_config/buildnml`` script to generate the DLND namelist file ``dlnd_in`` and the required associated stream files for the case.

.. note:: These xml variables are used by the the dlnd's **cime_config/buildnml** script in conjunction with dlnd's **cime_config/namelist_definition_dlnd.xml** file to generate the namelist file ``dlnd_in``.

===================== =============================================================================== 
XML variable          Description
===================== =============================================================================== 
DLND_MODE             Data mode
DLND_CPLHIST_CASE     Coupler history data mode case name 
DLND_CPLHIST_DIR      Coupler history data mode directory containing coupler history data 
DLND_CPLHIST_YR_ALIGN Coupler history data model simulation year corresponding to data starting year 
DLND_CPLHIST_YR_START Coupler history data model starting year to loop data over
DLND_CPLHIST_YR_END   Coupler history data model ending year to loop data over
===================== =============================================================================== 

In the above table, ``$DLND_MODE`` has the following supported settings:

.. _dlnd-datamodes:

============================ ==========================================================================================================================
DLND_MODE value              Description 
============================ ==========================================================================================================================
NULL                         null mode

CPLHIST                      coupler history mode for land

                             Land forcing data (e.g. produced by CESM/CLM) from a previous
			     model run is output in coupler history files and read in by the data land model. 

GLC_CPLHIST                  coupler history mode for snow

                             glc coupling fields (e.g. produced by CESM/CLM) from a previous model run are read in 
			     from a coupler history file.  
============================ ==========================================================================================================================

-------------------
Datamode values
-------------------

One of the variables in ``shr_strdata_nml`` is the ``datamode``, whose value is a character string. 
Each data model has a unique set of ``datamode`` values that it supports. 

The valid values for ``datamode`` are set by the xml variable ``DLND_MODE`` in the ``config_component.xml`` file for DLND. 
CIME will generate a value ``datamode`` that is compset dependent. 

The following are the supported DLND datamode values and their relationship to the ``$DLND_MODE`` xml variable value.

===================    =========================================================================
datamode value         XML variable value
===================    =========================================================================
NULL                   NULL 
COPYALL                CPLHIST, GLC_CPLHIST

                       copies all fields directly from the input data streams Any required
		       fields not found on an input stream will be set to zero.
===================    =========================================================================

.. _dlnd-mode-independent-streams:

---------------------------------
Datamode independent streams
---------------------------------

There are no datamode independent streams for DLND.

.. _dlnd-fields:

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

where NN = (01,02,...,``nflds_snow * glc_nec)``, and ``nflds_snow`` is the number of snow fields in each elevation class and ``glc_nec`` is the number of elevation classes. 

