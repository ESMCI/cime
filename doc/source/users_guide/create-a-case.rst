.. _creating-a-case:

*********************************
Creating a Case
*********************************

===================================
Calling **create_newcase**
===================================

The first step in creating a CIME based experiment is to use **create_newcase**.

If you are not on an out-of-the box CIME supported platform, you will need to first :ref:`port <porting>` CIME to your system.

You should first use the --help option in calling **create_newcase** to document its input options.  The only required arguments to **create_newcase** are:
::

   create_newcase --case [CASE] --compset [COMPSET] --res [GRID]

CIME supports out of the box ``component sets``, ``model grids`` and ``hardware platforms``.

- Component sets (usually referred to as compsets) define both the specific model components that will be used in a given CIME configuration, *and* any component-specific namelist or configuration settings that are specific to this configuration.  

- Model grids specify the grid for each component making up the model. 

- At a minimum creating a CIME experiment requires specifying a component set and a model grid.

- Out of the box compsets and models grids are associated with two names: a longname and an alias name.  

- Aliases are required by the CIME regression test system but can also be used for user convenience. Compset aliases are unique - each compset alias is associated with one and only one compset. Grid aliases, on the other hand, are overloaded and the same grid alias may result in a different grid based depending on the compset the alias is associated with. We recommend that the user always confirm that the compset longname and grid longname are the expected result when using aliases to create a case. 

--------------------------------
Component Set Naming Convention
--------------------------------

The component set (compset) longname has the form::

  TIME_ATM[%phys]_LND[%phys]_ICE[%phys]_OCN[%phys]_ROF[%phys]_GLC[%phys]_WAV[%phys]_ESP[_BGC%phys]

  TIME = model time period (e.g. 2000, 20TR, RCP8...) 

  CIME supports the following values for ATM,LND,ICE,OCN,ROF,GLC,WAV and ESP
  ATM  = [DATM, SATM, XATM]	   
  LND  = [DLND, SLND, XLND]	   
  ICE  = [DICE, SICE, SICE]		   
  OCN  = [DOCN, SOCN, XOCN]	   
  ROF  = [DROF, SROF, XROF]		   
  GLC  = [SGLC, XGLC]			   
  WAV  = [SWAV, XWAV]
  ESP  = [SESP]				   
  
  If CIME is run with CESM prognostic components, the following additional values are permitted:
  ATM  = [CAM40, CAM50, CAM55, CAM60]	   
  LND  = [CLM45, CLM50]	   
  ICE  = [CICE]		   
  OCN  = [POP2, AQUAP]	   
  ROF  = [RTM, MOSART]		   
  GLC  = [CISM1, CISM2]			   
  WAV  = [WW]			   
  BGC  = optional BGC scenario                    
  
  If CIME is run with ACME prognostic components, the following additional values are permitted:
  ATM  = []	   
  LND  = []	   
  ICE  = []		   
  OCN  = []	   
  ROF  = []		   
  GLC  = []			   
  WAV  = []			   
  BGC  = optional BGC scenario                    

  The OPTIONAL %phys attributes specify sub-modes of the given system
  For example DOCN%DOM is the DOCN data ocean (rather than slab-ocean) mode.
  ALL the possible %phys choices for each component are listed by
  the calling **manage_case** with the **-list** compsets argument. 
  ALL data models now have a %phys option that corresponds to the data model mode.

As an example, the CESM compset longname::

   1850_CAM60_CLM50%BGC_CICE_POP2%ECO_MOSART_CISM2%NOEVOLVE_WW3_BGC%BDRD

refers to running a pre-industrial control with prognostic CESM components CAM, CLM, CICE, POP2, MOSART, CISM2 and WW3 a BDRD BGC coupling scenario. 
The alias for this compset is B1850. Either a compset longname or a compset alias can be used as input to **create_newcase**. 
It is also possible to create your own custom compset (see `How do I create my own compset? in the FAQ`)

--------------------------------
Model Grid Naming Convention
--------------------------------

The model grid longname has the form::

  a%name_l%name_oi%name_r%name_m%mask_g%name_w%name

  a%  = atmosphere grid 
  l%  = land grid 
  oi% = ocean/sea-ice grid (must be the same) 
  r%  = river grid 
  m%  = ocean mask grid 
  g%  = internal land-ice (CISM) grid
  w%  = wave component grid 

  The ocean mask grid determines land/ocean boundaries in the model. 
  It is assumed that on the ocean grid, a gridcell is either all ocean or all land. 
  The land mask on the land grid is then obtained by mapping the ocean mask 
  (using first order conservative mapping) from the ocean grid to the land grid.
  
  From the point of view of model coupling - the glc (CISM) grid is assumed to
  be identical to the land grid. However, the internal CISM grid can be different, 
  and is specified by the g% value.

As an example, the longname:: 

   a%ne30np4_l%ne30np4_oi%gx1v6_r%r05_m%gx1v6_g%null_w%null

refers to a model grid with a ne30np4 spectral element 1-degree atmosphere and land grids, gx1v6 Greenland pole 1-degree ocean and sea-ice grids, a 1/2 degree river routing grid, null wave and internal cism grids and an gx1v6 ocean mask. 
The alias for this grid is ne30_g16. Either the grid longname or alias can be used as input to **create_newcase**. 

CIME also permits users to introduce their own :ref:`<user defined grids <faq-user-defined-grid>`.

Component grids (such as the atmosphere grid or ocean grid above) are denoted by the following naming convention:

- "[dlat]x[dlon]" are regular lon/lat finite volume grids where dlat and dlon are the approximate grid spacing. The shorthand convention is "fnn" where nn is generally a pair of numbers indicating the resolution. An example is 1.9x2.5 or f19 for the approximately "2-degree" finite volume grid. Note that CAM uses an [nlat]x[nlon] naming convention internally for this grid.

- "Tnn" are spectral lon/lat grids where nn is the spectral truncation value for the resolution. The shorthand name is identical. An example is T85.

- "ne[X]np[Y]" are cubed sphere resolutions where X and Y are integers. The short name is generally ne[X]. An example is ne30np4 or ne30.

- "pt1" is a single grid point.

- "gx[D]v[n]" is a displaced pole grid where D is the approximate resolution in degrees and n is the grid version. The short name is generally g[D][n]. An example is gx1v6 or g16 for a grid of approximately 1-degree resolution.

- "tx[D]v[n]" is a tripole grid where D is the approximate resolution in degrees and n is the grid version.

---------------------------------
Result of calling create_newcase
---------------------------------

Following is a simple example of using **create_newcase**  using aliases for both compset and grid names. 
The complete example appears in the :ref:`basic example <faq-basic-example>`. 
In what follows, ``$CIMEROOT`` is the full pathname of the root directory of the CIME distribution. 
::
 
   > cd $CIMEROOT/scripts 
   > create_newcase --case ~/cime/example1 --compset A --res f09_g16_rx1

This example 

- creates the ``$CASEROOT`` directory ``~/cime/example1`` (if the directory already exists, a warning is printed and ``create_newcase`` aborts)

- ``$CASE`` is ``"example1"`` (``$CASE`` can include letters, numbers, ".", and "_")  

- the model resolution is ``a%0.9x1.25_l%0.9x1.25_oi%gx1v6_r%r05_m%gx1v6_g%null_w%null`` 

- the compset is ``2000_DATM%NYF_SLND_DICE%SSMI_DOCN%DOM_DROF%NYF_SGLC_SWAV``.

- in ``$CASEROOT``, **create_newcase** installs files to build and run the model and optionally perform archiving of the case on the target platform. 

Various scripts, files and directories are created in ``$CASEROOT`` by **create_newcase**:

- ``user scripts``

   =================     =====================================================================================================
   case.setup"           Script used to set up the case (create the case.run script, the Macros file and user_nl_xxx files)
   case.build"           Script to build component and utility libraries and model executable."
   case.st_archive       Script to perform short-term archiving of output data
   case.lt_archive       Script to perform long-term archiving of output data 
   case.setup            Script used to set up the case (create the case.run script, the Macros file and user_nl_xxx files)"
   case.build            Script to build component and utility libraries and model executable."
   xmlchange 	         Script for modifying values in the xml files
   xmlquery 	         Script for query values in the xml files
   preview_namelists	 Script for users to see their component namelists in ``$CASEROOT/CaseDocs`` before running the model

                         **NOTE**: the namelists generated in ``$CASEROOT/CaseDocs`` should not be edited by the user 

                         they are only there to document model behavior."
   check_input_data      Script for checking  for various input datasets and moves them into place."
   =================     =====================================================================================================

- ``XML files``

   =====================  ===============================================================================================================================
   env_mach_specific.xml  Sets a number of machine-specific environment variables for building and/or running. 

                          Although you can edit this at any time, env_build.xml variables should not be edited 

                          after a **case.build** is invoked
   env_case.xml           Sets case specific variables (e.g. model components, model and case root directories). 

                          Cannot be modified after a case has been created. 

			  To make changes, your should re-run **create_newcase** with different options.
   env_build.xml          Sets model build settings.

                          This includes component resolutions and component compile-time configuration options
   env_mach_pes.xml       Sets component machine-specific processor layout (see :ref:`changing pe layout<changing-the-pe-layout>` ). 

                          The settings in this are critical to a well-load-balanced simulation (see :ref:`load balancing <optimizing-processor-layout>`)."
   env_run.xml            Sets run-time settings such as length of run, frequency of restarts, output of coupler diagnostics, 

                          and short-term and long-term archiving.
   =====================  ===============================================================================================================================

- ``User Source Mods Directory``

   =====================  ===============================================================================================================================
   SourceMods             Top-level directory containing sub-directories for each compset component where 
                          you can place modified source code for that component."
   =====================  ===============================================================================================================================

- ``Provenance``

   =====================  ===============================================================================================================================
   README.case            File detailing **create_newcase** usage. This is a good place to keep track of runtime problems and changes.
   CaseStatus             File containing a list of operations done in the current case.
   =====================  ===============================================================================================================================

- ``non-modifiable work directories``

   =====================  ===============================================================================================================================
   Buildconf/             Work directory containing scripts to generate component namelists and component and utility libraries (e.g., PIO, MCT)

                          You should never have to edit the contents of this directory.
   LockedFiles/           Work directory that holds copies of files that should not be changed. 

                          Certain xml files are *locked* after their variables have been used by should no longer be changed. 

			  CIME does this by *locking* a file and not permitting you to modify that file unless, depending on the file,

			  **case.setup --clean** or  **case.build --clean** are called.
   Tools/                 Work directory containing support utility scripts. You should never need to edit the contents of this directory.
   =====================  ===============================================================================================================================
 

