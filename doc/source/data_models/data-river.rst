Data River (DROF)
=================

---------
Namelists
---------
The data river runoff model is new and is effectively the runoff part of the dlnd model in CESM1.0 that has been made its own top level component.

DROF namelists can be separated into two groups, `stream-independent namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_drof.html#nonstream>`_ that are specific to the DROF model and `stream-specific namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_drof.html#stream>`_ that are contained in share code and whose names are common to all the data models.

For stream-independent input, the namelist input filename is hardwired in the data model code to "drof_in" (or drof_in_NNNN for multiple instances) and the namelist group is called "drof_nml". The variable formats are character string (char), integer (int), double precision real (r8), or logical (log) or one dimensional arrays of any of those things (array of ...).

For stream-dependent input, the namelist input file is "drof_lnd_in" (or drof_rof_in_NNNN for NNNN multiple instances) and the namelist group is "shr_strdata_nml". One of the variables in shr_strdata_nml is the datamode value. The mode is selected by a character string set in the strdata namelist variable dataMode. Each data model has a unique set of datamode values that it supports. Those for DROF are listed in detail in the `datamode <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_drof.html#stream>`_ definition.

------
Fields
------
The pre-defined internal field names in the data river runoff model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data river runoff model.

=========       ========       =====
(/ "roff        ","ioff        "/)
=========       ========       =====
