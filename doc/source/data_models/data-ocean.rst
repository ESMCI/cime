.. _data-ocean:

===================
Data Ocean (DOCN)
===================

Data ocean can be run both as a prescribed component, simply reading in SST data from a stream, or as a prognostic slab ocean model component.

The data ocean component (DOCN) always returns SSTs to the driver. 
The atmosphere/ocean fluxes are computed in the coupler. 
Therefore, the data ocean model does not compute fluxes like the data ice (DICE) model. 
DOCN has two distinct modes of operation. 
DOCN can run as a pure data model, reading in ocean SSTs (normally climatological) from input datasets, performing time/spatial  interpolations, and passing these to the coupler. 
Alternatively, DOCN can compute updated SSTs by running as a slab ocean model where bottom ocean heat flux convergence and boundary layer depths are read in and used with the atmosphere/ocean and ice/ocean fluxes obtained from the driver.

DOCN running in prescribed mode assumes that the only field in the input stream is SST and also that SST is in Celsius and must be converted to Kelvin. 
All other fields are set to zero except for ocean salinity, which is set to a constant reference salinity value. 
Normally the ice fraction data (used for prescribed CICE) is found in the same data files that provide SST data to the data ocean model since SST and ice fraction data are derived from the same observational data sets and are consistent with each other. 
For DOCN prescribed mode, default yearly climatological datasets are provided for various model resolutions.

DOCN running as a slab ocean model is used in conjunction with active ice mode running in full prognostic mode (e.g. CICE for CESM).
This mode computes a prognostic sea surface temperature and a freeze/melt potential (surface Q-flux) used by the sea ice model. 
This calculation requires an external SOM forcing data file that includes ocean mixed layer depths and bottom-of-the-slab Q-fluxes. 
Scientifically appropriate bottom-of-the-slab Q-fluxes are normally ocean resolution dependent and are derived from the ocean model output of a fully coupled CCSM run. 
Note that this mode no longer runs out of the box, the default testing SOM forcing file is not scientifically appropriate and is provided for testing and development purposes only. 
Users must create scientifically appropriate data for their particular application or use one of the standard SOM forcing files from the full prognostic control runs. 
For CESM, some of these are available in the `inputdata repository <https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/ocn/docn7/SOM/>`_. 
The user then modifies the ``$DOCN_SOM_FILENAME`` variable in env_run.xml to point to the appropriate SOM forcing dataset. 

.. note:: A tool is available to derive valid `SOM forcing <http://www.cesm.ucar.edu/models/ccsm1.1/data8/SOM.pdf>`_ and more information on creating the SOM forcing is also available.

---------
Namelists
---------

As is the case for all data models, DOCN namelists can be separated into two groups, stream-independent and stream-dependent. 

The namelist file for DOCN is ``docn_in`` (or ``docn_in_NNN`` for multiple instances).

The stream dependent group is :ref:`shr_strdata_nml<input-streams>` .

As part of the stream dependent namelist input, DOCN supports two science modes, ``SSTDATA`` (prescribed mode) and ``SOM`` (slab ocean mode). 

.. _docn-stream-independent-namelists:

The stream-independent group is ``docn_nml`` and the DOCN stream-independent namelist variables are:

=====================  ======================================================
decomp                 decomposition strategy (1d, root)
    
                       1d => vector decomposition, root => run on master task
restfilm               master restart filename 
restfils               stream restart filename 
force_prognostic_true  TRUE => force prognostic behavior
=====================  ======================================================

To change the namelist settings in docn_in, edit the file user_nl_docn. 

.. _docn-xml-vars:

---------------
XML variables
---------------

The following are xml variables that CIME supports for DOCN.  These variables will appear in ``env_run.xml`` and are used by the DOCN ``cime_config/buildnml`` script to generate the DOCN namelist file ``docn_in`` and the required associated stream files for the case.

.. note:: These xml variables are used by the the docn's **cime_config/buildnml** script in conjunction with docn's **cime_config/namelist_definition_docn.xml** file to generate the namelist file ``docn_in``.

===================== ==================================================================================== 
DOCN_MODE value       Description
===================== ==================================================================================== 
DOCN_MODE             Data mode

DOCN_SOM_FILENAME     Sets SOM forcing data filename for pres runs, only used in D and E compset

SSTICE_STREAM         Prescribed SST and ice coverage stream name.

                      Sets SST and ice coverage stream name for prescribed runs.

SSTICE_DATA_FILENAME  Prescribed SST and ice coverage data file name.

                      Sets SST and ice coverage data file name for DOCN prescribed runs.

SSTICE_YEAR_ALIGN     The model year that corresponds to SSTICE_YEAR_START on the data file.

                      Prescribed SST and ice coverage data will be aligned so that the first year of
                      data corresponds to SSTICE_YEAR_ALIGN in the model. For instance, if the first
                      year of prescribed data is the same as the first year of the model run, this
                      should be set to the year given in RUN_STARTDATE.
                      If SSTICE_YEAR_ALIGN is later than the model's starting year, or if the model is
                      run after the prescribed data ends (as determined by SSTICE_YEAR_END), the
                      default behavior is to assume that the data from SSTICE_YEAR_START to
                      SSTICE_YEAR_END cyclically repeats. This behavior is controlled by the
                      *taxmode* stream option

SSTICE_YEAR_START     The first year of data to use from SSTICE_DATA_FILENAME.

                      This is the first year of prescribed SST and ice coverage data to use. For
                      example, if a data file has data for years 0-99, and SSTICE_YEAR_START is 10,
                      years 0-9 in the file will not be used.</desc>

SSTICE_YEAR_END       The last year of data to use from SSTICE_DATA_FILENAME.

                      This is the last year of prescribed SST and ice coverage data to use. For
                      example, if a data file has data for years 0-99, and value is 49,
                      years 50-99 in the file will not be used.</desc>
===================== ==================================================================================== 

.. note:: For multi-year runs requiring AMIP datasets of sst/ice_cov fields, you need to set the xml variables for ``DOCN_SSTDATA_FILENAME``, ``DOCN_SSTDATA_YEAR_START``, and ``DOCN_SSTDATA_YEAR_END``. CICE in prescribed mode also uses these values.

===================== =============================================================================== 
DOCN_MODE value       Description
===================== =============================================================================== 
null                  null mode
prescribed            prescribed climatological mode
interannual           prescribed interannual mode 
som                   som mode
copyall               copy mode
===================== =============================================================================== 

.. _docn-datamodes:

-------------------
Datamode values
-------------------

One of the variables in ``shr_strdata_nml`` is the ``datamode``, whose value is a character string. 
Each data model has a unique set of ``datamode`` values that it supports. 

The valid values for ``datamode`` are set by the xml variable ``DOCN_MODE`` in the ``config_component.xml`` file for DOCN. 
CIME will generate a value ``datamode`` that is compset dependent. 

The following are the supported DOCN datamode values and their relationship to the ``$DOCN_MODE`` xml variable value.

===================    =========================================================================
datamode value         XML variable value
===================    =========================================================================
NULL                   NULL
SSTDATA                prescribed
IAF                    interannual
                       IAF is the interannually varying version of SSTDATA
SOM                    som
COPYALL                COPYALL        
===================    =========================================================================

.. _docn-mode-independent-streams:

---------------------------------
Datamode independent streams
---------------------------------

There are no datamode independent streams for DOCN.

.. _docn-fields:

------
Fields
------

The pre-defined internal field names in the data ocean model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data ocean model.

=========       ==========     =========      ==========     ===========    =====
(/ "ifrac       ","pslv        ","duu10n      ","taux        ","tauy        ", &
"swnet          ","lat         ","sen         ","lwup        ","lwdn        ", &
"melth          ","salt        ","prec        ","snow        ","rain        ", &
"evap           ","meltw       ","rofl        ","rofi        ",                &
"t              ","u           ","v           ","dhdx        ","dhdy        ", &
"s              ","q           ","h           ","qbot        ","fswpen      "  /)
=========       ==========     =========      ==========     ===========    =====
