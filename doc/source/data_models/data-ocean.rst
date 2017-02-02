Data Ocean (DOCN)
=================

---------
Namelists
---------
DOCN namelists can be separated into two groups, `stream-independent namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_ocn.html#nonstream>`_ that are specific to the DATM model and `stream-specific namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_docn.html#stream>`_ that are contained in share code and whose names are common to all the data models.

For stream-independent input, the namelist input filename is hardwired in the data model code to "docn_in" (or docn_in_NNNN for multiple instances) and the namelist group is called "docn_nml". The variable formats are character string (char), integer (int), double precision real (r8), or logical (log) or one dimensional arrays of any of those things (array of ...).

For stream-dependent input, the namelist input file is docn_ocn_in (or docn_ocn_in_NNNN for multiple instances) and the namelist group is "shr_strdata_nml". One of the variables in shr_strdata_nml is the datamode value. The mode is selected by a character string set in the strdata namelist variable dataMode. Each data model has a unique set of datamode values that it supports. Those for DOCN are listed in detail in the `datamode <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_docn.html#stream>`_ definition. As part of the stream independent namelist input, DOCN supports two science modes, "SSTDATA" and "SOM". SOM ("slab ocean model") mode is a prognostic mode. This mode computes a prognostic sea surface temperature and a freeze/melt potential (surface Q-flux) used by the sea ice model. This calculation requires an external SOM forcing data file that includes ocean mixed layer depths and bottom-of-the-slab Q-fluxes. Scientifically appropriate bottom-of-the-slab Q-fluxes are normally ocean resolution dependent and are derived from the ocean model output of a fully coupled CCSM run. Note that this mode no longer runs out of the box, the default testing SOM forcing file is not scientifically appropriate and is provided for testing and development purposes only. Users must create scientifically appropriate data for their particular application or use one of the standard SOM forcing files from the CESM control runs. Some of these are available in the `inputdata repository <https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/ocn/docn7/SOM/>`_. The user then edits the DOCN_SOM_FILENAME variable in env_run.xml to point to the appropriate SOM forcing dataset. A tool is available to derive valid `SOM forcing <http://www.cesm.ucar.edu/models/ccsm1.1/data8/SOM.pdf>`_. More information on creating the SOM forcing is also available.

------
Fields
------
The pre-defined internal field names in the data ocean model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data ocean model.

=========       ==========     =========      ==========     ========       =====
(/ "ifrac       ","pslv        ","duu10n      ","taux        ","tauy        ", &
"swnet          ","lat         ","sen         ","lwup        ","lwdn        ", &
"melth          ","salt        ","prec        ","snow        ","rain        ", &
"evap           ","meltw       ","roff        ","ioff        ",                &
"t              ","u           ","v           ","dhdx        ","dhdy        ", &
"s              ","q           ","h           ","qbot        "                 /)
=========       ==========     =========      ==========     ========       =====
