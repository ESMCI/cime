Data Ice (DICE)
================

---------
Namelists
---------
DICE namelists can be separated into two groups, `stream-independent namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_ice.html#nonstream>`_ that are specific to the DATM model and `stream-specific namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_dice.html#stream>`_ that are contained in share code and whose names are common to all the data models.

For stream-independent input, the namelist input filename is hardwired in the data model code to "dice_in" (or dice_in_NNNN for multiple instances) and the namelist group is called "dice_nml".

Its important to point out that the only currently supported datamode that is not "NULL" or "COPYALL" is "SSTDATA", which is a prognostic mode and therefore requires data be sent to the ice model. Ice fraction (extent) data is read from an input stream, atmosphere state variables are received from the coupler, and then an atmosphere-ice surface flux is computed and sent to the coupler. It is called "SSTDATA" mode because normally the ice fraction data is found in the same data files that provide SST data to the data ocean model. They are normally found in the same file because the SST and ice fraction data are derived from the same observational data sets and are consistent with each other.

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
