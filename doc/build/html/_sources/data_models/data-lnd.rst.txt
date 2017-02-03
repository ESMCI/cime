Data Land (DLND)
================

---------
Namelists
---------
The land model is unique because it supports land data and snow data (*lnd and sno*) almost as if they were two separate components, but they are in fact running in one component model through one interface. The lnd (land) data consist of fields sent to the atmosphere. This set of data is used when running dlnd with an active atmosphere. In general this is not a mode that is used or supported in CESM1.1. The sno (snow) data consist of fields sent to the glacier model. This set of data is used when running dlnd with an active glacier model (TG compsets). Both sets of data are assumed to be on the same grid.

DLND namelists can be separated into two groups, `stream-independent namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_dlnd.html#nonstream>`_ that are specific to the DLND model and `stream-specific namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_dlnd.html#stream>`_ that are contained in share code and whose names are common to all the data models.

For stream-independent input, the namelist input filename is hardwired in the data model code to "dlnd_in" (or dlnd_in_NNNN for multiple instances) and the namelist group is called "dlnd_nml". The variable formats are character string (char), integer (int), double precision real (r8), or logical (log) or one dimensional arrays of any of those things (array of ...).

For stream-dependent input, the namelist input file is dlnd_lnd_in and dlnd_sno_in (or dlnd_lnd_in_NNNN and dlnd_sno_in_NNNN for NNNN multiple instances) and the namelist group is "shr_strdata_nml". One of the variables in shr_strdata_nml is the datamode value. The mode is selected by a character string set in the strdata namelist variable dataMode. Each data model has a unique set of datamode values that it supports. Those for DLND are listed in detail in the `datamode <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_dlnd.html#stream>`_ definition.

If you want to change the namelist settings in dlnd_lnd_in or dlnd_in you should edit the file user_nl_dlnd. If you want to change the namelist settings in dsno_lnd_in or dsno_in you should edit the file user_nl_dsno.

------
Fields
------
The pre-defined internal field names in the data land model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data land model.

==========      ==========     ==========     ==========     =========      =====
(/ "t           ","tref        ","qref        ","avsdr       ","anidr       ", &
"avsdf          ","anidf       ","snowh       ","taux        ","tauy        ", &
"lat            ","sen         ","lwup        ","evap        ","swnet       ", &
"lfrac          ","fv          ","ram1        ",                               &
"flddst1        ","flxdst2     ","flxdst3     ","flxdst4     ",                & 
"tsrf01         ","topo01      ","tsrf02      ","topo02      ","tsrf03      ", &
"topo03         ","tsrf04      ","topo04      ","tsrf05      ","topo05      ", &
"tsrf06         ","topo06      ","tsrf07      ","topo07      ","tsrf08      ", &
"topo08         ","tsrf09      ","topo09      ","tsrf10      ","topo10      ", &
"qice01         ","qice02      ","qice03      ","qice04      ","qice05      ", &
"qice06         ","qice07      ","qice08      ","qice09      ","qice10      "  /)
==========      ==========     ==========     ==========     =========      =====
