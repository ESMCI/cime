Data Atmosphere (DATM)
======================

---------
Namelists
---------
DATM namelists can be separated into two groups, `stream-independent namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_datm.html#nonstream>`_ that are specific to the DATM model and `stream-specific namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_datm.html#stream>`_ that are contained in share code and whose names are common to all the data models.

For stream-independent input, the namelist input filename is hardwired in the data model code to "datm_in" (or datm_in_NNNN for multiple instances) and the namelist group is called "datm_nml". The variable formats are character string (char), integer (int), double precision real (r8), or logical (log) or one dimensional arrays of any of those things (array of ...).

For stream-dependent input, the namelist input file is datm_atm_in (or datm_atm_in_NNNN for multiple instances) and the namelist group is "shr_strdata_nml". One of the variables in shr_strdata_nml is the datamode value. The mode is selected by a character string set in the strdata namelist variable dataMode. Each data model has a unique set of datamode values that it supports. Those for DATM are listed in detail in the `datamode <http://www.cesm.ucar.edu/models/cesm2.0/cesm/doc/modelnl/nl_datm.html#stream>`_ definition.

------
Fields
------
The pre-defined internal field names in the data atmosphere model are as follows. In general, the stream input file should translate the input variable names into these names for use within the data atmosphere model.

=========          ===========        ===========        ===========        =====
(/"z               ","u               ","v               ","tbot            ", &
"ptem              ","shum            ","dens            ","pbot            ", &
"pslv              ","lwdn            ","rainc           ","rainl           ", &
"snowc             ","snowl           ","swndr           ","swvdr           ", &
"swndf             ","swvdf           ","swnet           ","co2prog         ", &
"co2diag           ","bcphidry        ","bcphodry        ","bcphiwet        ", &
"ocphidry          ","ocphodry        ","ocphiwet        ","dstwet1         ", &
"dstwet2           ","dstwet3         ","dstwet4         ","dstdry1         ", &
"dstdry2           ","dstdry3         ","dstdry4         ",                    &
"tref              ","qref            ","avsdr           ","anidr           ", &
"avsdf             ","anidf           ","ts              ","to              ", &
"snowhl            ","lfrac           ","ifrac           ","ofrac           ", &
"taux              ","tauy            ","lat             ","sen             ", &
"lwup              ","evap            ","co2lnd          ","co2ocn          ", &
"dms               "                                                          /)
=========          ===========        ===========        ===========        =====
