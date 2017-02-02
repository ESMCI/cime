Creating and Setting up a Case
===================================

How to create a new case
-----------------------------------

The first step in creating a CIME based experiment is to use **create_newcase**.

CIME supports out of the box `component sets <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, `model grids <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `hardware platforms <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.  

- Component sets (usually referred to as compsets) define both the specific model components that will be used in a given CIME configuration, *and* any component-specific namelist or configuration settings that are specific to this configuration.  

- Model grids specify the grid for each component making up the model. 

- At a minimum creating a CIME experiment requires specifying a component set and a model grid.

- Out of the box compsets and models grids are associated with two names: a longname, and an alias name.  

- Aliases are required by the CIME regression test system but can also be used for user convenience. Compset aliases are unique - each compset alias is associated with one and only one compset. Grid aliases, on the other hand, are overloaded and the same grid alias may result in a different grid based depending on the compset the alias is associated with. We recommend that the user always confirm that the compset longname and grid longname are the expected result when using aliases to create a case. 

Component Set Naming Convention
-----------------------------------

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
  For example DOCN%DOM is the  DOCN data ocean (rather than slab-ocean) 
  mode. ALL the possible %phys choices for each component are listed by
  the calling **create_newcase** with the -list compsets argument. ALL 
  data models now have a %phys option that corresponds to the data model mode 

As an example, the CESM compset longname::

   1850_CAM60_CLM50%BGC_CICE_POP2%ECO_MOSART_CISM2%NOEVOLVE_WW3_BGC%BDRD

refers to running a pre-industrial control with prognostic CESM components CAM, CLM, CICE, POP2, MOSART, CISM2 and WW3 a BDRD BGC coupling scenario. The alias for this compset is B1850. Either a compset longname or a compset alias can be used as input to **create_newcase**. It is also possible to create your own custom compset (see `How do I create my own compset? <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_). 

All the out-of-the-box CESM2.0 release series compsets are listed in `component sets <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. Upon clicking on any of the long names a pop up box will appear that provides more details of the component configuration.

Model Grid Naming Convention
----------------------------------------

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

refers to a model grid with a ne30np4 spectral element 1-degree atmosphere and land grids, gx1v6 Greenland pole 1-degree ocean and sea-ice grids, a 1/2 degree river routing grid, null wave and internal cism grids and an gx1v6 ocean mask. The alias for this grid is ne30_g16. Either the grid longname or alias can be used as input to **create_newcase**. 

CIME also permits users to introduce their own user defined grids (see `Adding a new user-defined grid <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_). 

All the out-of-the-box CIME5 release series model grids are listed in `grids <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. Upon clicking on any of the long names a pop up box will appear that provides more details of the model grid.  

Component grids (such as the atmosphere grid or ocean grid above) are denoted by the following naming convention:

- "[dlat]x[dlon]" are regular lon/lat finite volume grids where dlat and dlon are the approximate grid spacing. The shorthand convention is "fnn" where nn is generally a pair of numbers indicating the resolution. An example is 1.9x2.5 or f19 for the approximately "2-degree" finite volume grid. Note that CAM uses an [nlat]x[nlon] naming convention internally for this grid.

- "Tnn" are spectral lon/lat grids where nn is the spectral truncation value for the resolution. The shorthand name is identical. An example is T85.

- "ne[X]np[Y]" are cubed sphere resolutions where X and Y are integers. The short name is generally ne[X]. An example is ne30np4 or ne30.

- "pt1" is a single grid point.

- "gx[D]v[n]" is a displaced pole grid where D is the approximate resolution in degrees and n is the grid version. The short name is generally g[D][n]. An example is gx1v6 or g16 for a grid of approximately 1-degree resolution.

- "tx[D]v[n]" is a tripole grid where D is the approximate resolution in degrees and n is the grid version.

Using create_newcase
--------------------

You should first use the --help option in calling **create_newcase** to document its input options.  On CIME supported out of the box machines, the only required arguments to **create_newcase** are:
::

   create_newcase --case [CASE] --compset [COMPSET] --res [GRID]

for non-supported machines, users will need to also add the following two arguments
::

   create_newcase --case [CASE] --compset [COMPSET] --res [GRID] --machine [MACH] --compiler [compiler]

Following is a simple example of using **create_newcase**  using aliases for both compset and grid names. In what follows, ``$CIMEROOT`` is the full pathname of the root directory of the CIME distribution. 
::
 
   > cd $CIMEROOT/scripts 
   > create_newcase --case ~/cime/example1 --compset A --res f09_g16_rx1

This example creates a ``$CASEROOT`` directory ``~/cime/example1`` where ``$CASE`` is ``"example1"``. 
The model resolution is ``a%0.9x1.25_l%0.9x1.25_oi%gx1v6_r%r05_m%gx1v6_g%null_w%null`` and the compset is ``2000_DATM%NYF_SLND_DICE%SSMI_DOCN%DOM_DROF%NYF_SGLC_SWAV``.
The complete example appears in the `basic example <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. ``$CASE`` can include letters, numbers, ".", and "_". 
Note that **create_newcase** creates the ``$CASEROOT`` directory. If the directory already exists, it prints a warning and aborts.
As a more general description, **create_newcase** creates the directory ``$CASEROOT``, which is specified by the --case option. 
In ``$CASEROOT``, **create_newcase** installs files to build and run the model and optionally perform archiving of the case on the target platform. **create_newcase** also creates the directory ``$CASEROOT/Buildconf/``, that in turn contains scripts to generate component namelist and build component libraries. The table below outlines the files and directories created by **create_newcase**:

.. csv-table:: Result of invoking create_newcase
   :header: "Directory or Filename", "Description"
   :widths: 100, 600

   "README.case", "File detailing your **create_newcase** usage. This is a good place for you to keep track of runtime problems and changes."
   "CaseStatus", "File containing a list of operations done in the current case."
   "env_mach_specific.xml", "File used to set a number of machine-specific environment variables for building and/or running. Although you can edit this at any time, build environment variables should not be edited after a build is invoked."
   "env_case.xml", "Sets case specific variables (e.g. model components, model and case root directories) and cannot be modified after a case has been created. To make changes, your should re-run **create_newcase** with different options."
   "env_build.xml", "Sets model build settings, including component resolutions and component configuration options (e.g. CAM_CONFIG_OTPS) where applicable (see `env_build.xml variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_)."
   "env_mach_pes.xml", "Sets component machine-specific processor layout (see the `Section called *Changing the PE layout* <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_). The settings in this are critical to a well-load-balanced simulation (see `loadbalancing a run <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_)."
   "env_run.xml", "Sets run-time settings such as length of run, frequency of restarts, output of coupler diagnostics, and short-term and long-term archiving. See `run initialization variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, `run stop variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, `run restart control variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, for a more complete discussion of general run control settings."
   "case.setup", "Script used to set up the case (create the case.run script, the Macros file and user_nl_xxx files)"
   "case.build", "Script to build component and utility libraries and model executable."
   "case.st_archive", "Script to perform short-term archiving of output data (see `archiving <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_). "
   "case.lt_archive", "Script to perform long-term archiving of output data (see `archiving <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_). "
   "xmlchange",	"Utility for modifying values in the xml files."
   "preview_namelists",	"Utility to enable users to see their component namelists in ``$CASEROOT/CaseDocs`` before running the model. NOTE: the namelists generated in ``$CASEROOT/CaseDocs`` should not be edited by the user - they are only there to document model behavior."
   "check_input_data", "Utility that checks for various input datasets and moves them into place."
   "Buildconf/", "Work directory containing scripts to generate component namelists and component and utility libraries (e.g., PIO, MCT). You should never have to edit the contents of this directory"
   "SourceMods/", "Directory where you can place modified source code."
   "LockedFiles/", "Directory that holds copies of files that should not be changed. Certain xml files are *locked* after their variables have been used by other parts of the system and cannot be changed. The scripts do this by *locking* a file and not permitting you to modify that file unless a 'clean' operation is performed. **TODO - put a link in for the section - Why is there file locking and how does it work?**"
   "Tools/", "Directory containing support utility scripts. You should never need to edit the contents of this directory."
 
For more complete information about the files in the case directory, see the `Section called *BASICS: What are the directories and files in my case directory?* in Chapter 6 <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.


How to set up a case and customize the PE layout
------------------------------------------------

Calling case.setup
^^^^^^^^^^^^^^^^^^

After creating a case using **create_newcase**, you need to call the **case.setup** command from ``$CASEROOT``. 
To see the options to **case.setup** use the ``--help`` option. 
Calling ``case.setup`` creates the following **additional** files and directories in ``$CASEROOT``: (**TODO: which files are modifiable below?)

.. csv-table:: **Result of calling case.setup**
   :header: "File or Directory", "Description"
   :widths: 100, 600

   "Macros.make", "File containing machine-specific makefile directives for your target platform/compiler. 
   This is only created the *first* time that **case.setup** is called. Calling **case.setup -clean** will not remove the Macros file once it has been created."
   "user_nl_xxx[_NNNN] files", "Files where all user modifications to component namelists are made. 
   xxx denotes any one of the set of components targeted for the specific case. 
   NNNN goes from 0001 to the number of instances of that component (see the `multiple instance <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ discussion below). 
   For example, for a full active CESM compset, xxx would denote [cam,clm,rtm,cice,pop2,cism2,ww3,cpl]. 
   For a case where there is only 1 instance of each component (default) NNNN will not appear in the user_nl file names. 
   A user_nl file of a given name will only be created once. 
   Calling **case.setup -clean** will not remove any user_nl files. Changing the number of instances in the ``env_mach_pes.xml`` will only cause new user_nl files to be added to ``$CASEROOT``."
   "$CASE.run", "This is the case run script and contains the necessary batch directives to run the model on the required machine for the requested PE layout. 
   Additionally, this script also optionally performs short-term and long-term archiving of output data (see `running CESM <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_).
   This script is removed when **case.setup --clean** is called."
   "CaseDocs/", "Directory that contains all the component namelists for the run. 
   This is for reference only and files in this directory SHOULD NOT BE EDITED since they will be overwritten at build time and run time." 
   ".env_mach_specific.[csh,sh]", "Files summarizing the module load commands and environment variables that are set when the scripts in ``$CASEROOT`` are called. 
   **TODO:** can or should users invoke this?"
   "software_environment.txt", "**TODO:** FILL THIS IN."

**case.setup -clean** removes ``$CASEROOT/$CASE.run`` and must be run if modifications are made to ``env_mach_pes.xml``. 
**case.setup** must then be rerun before you can build and run the model. 
If ``env_mach_pes.xml`` variables need to be changed after **case.setup** has been called, then **case.setup -clean** must be run first, followed by **case.setup**.

(Also see the `Section called *BASICS: What are the directories and files in my case directory?* in Chapter 6 <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.)

Changing the PE layout
^^^^^^^^^^^^^^^^^^^^^^

The file, ``env_mach_pes.xml``, determines the number of processors and OpenMP threads for each component, the number of instances of each component and the layout of the components across the hardware processors. 
Optimizing the throughput and efficiency of a CIME experiment often involves customizing the processor (PE) layout for `load balancing <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.  
CIME provides significant flexibility with respect to the layout of components across different hardware processors. In general, the CIME components -- atm, lnd, ocn, ice, glc, rof, wav, and cpl -- can run on overlapping or mutually unique processors. 
Whereas Each component is associated with a unique MPI communicator, the CIME driver runs on the union of all processors and controls the sequencing and hardware partitioning. 
The component processor layout is via three settings: the number of MPI tasks, the number of OpenMP threads per task, and the root MPI processor number from the global set.

The entries in ``env_mach_pes.xml`` have the following meanings:

.. csv-table:: **Table 2-3. env_mach_pes.xml entries**
   :header: "XML entry", "Description"
   :widths: 100, 600

   "NTASKS", "the total number of MPI tasks, a negative value indicates nodes rather than tasks."
   "NTHRDS", "the number of OpenMP threads per MPI task."
   "ROOTPE", "the global mpi task of the component root task, if negative, indicates nodes rather than tasks."
   "PSTRID", "the stride of MPI tasks across the global set of pes (for now set to 1)"
   "NINST",  "the number of component instances (will be spread evenly across NTASKS)"

For example, if a component has ``NTASKS=16``, ``NTHRDS=4`` and ``ROOTPE=32``, then it will run on 64 hardware processors using 16 MPI tasks and 4 threads per task starting at global MPI task 32. 
Each CIME component has corresponding entries for ``NTASKS``, ``NTHRDS``, ``ROOTPE`` and ``NINST`` in ``env_mach_pes.xml``. 
There are some important things to note.

- NTASKS must be greater or equal to 1 (one) even for inactive (stub) components.
- NTHRDS must be greater or equal to 1 (one). 
  If NTHRDS is set to 1, this generally means threading parallelization will be off for that component. 
  NTHRDS should never be set to zero.
- The total number of hardware processors allocated to a component is NTASKS * NTHRDS.
- The coupler processor inputs specify the pes used by coupler computation such as mapping, merging, diagnostics, and flux calculation. 
  This is distinct from the driver which always automatically runs on the union of all processors to manage model concurrency and sequencing.
- The root processor is set relative to the MPI global communicator, not the hardware processors counts. 
  An example of this is below.
- The layout of components on processors has no impact on the science. 
  The scientific sequencing is hardwired into the driver. 
  Changing processor layouts does not change intrinsic coupling lags or coupling sequencing. 
  ONE IMPORTANT POINT is that for a fully active configuration, the atmosphere component is hardwired in the driver to never run concurrently with the land or ice component. 
  Performance improvements associated with processor layout concurrency is therefore constrained in this case such that there is never a performance reason not to overlap the atmosphere component with the land and ice components. 
  Beyond that constraint, the land, ice, coupler and ocean models can run concurrently, and the ocean model can also run concurrently with the atmosphere model.

- If all components have identical NTASKS, NTHRDS, and ROOTPE set, all components will run sequentially on the same hardware processors.

An important, but often misunderstood point, is that the root processor for any given component, is set relative to the MPI global communicator, not the hardware processor counts. 
For instance, in the following example:
::

   NTASKS(ATM)=6  NTHRRDS(ATM)=4  ROOTPE(ATM)=0  
   NTASKS(OCN)=64 NTHRDS(OCN)=1   ROOTPE(OCN)=16

The atmosphere and ocean will run concurrently, each on 64 processors with the atmosphere running on MPI tasks 0-15 and the ocean running on MPI tasks 16-79. 
The first 16 tasks are each threaded 4 ways for the atmosphere. 
CIME ensures that the batch submission script ($CASE.run) automatically request 128 hardware processors, and the first 16 MPI tasks will be laid out on the first 64 hardware processors with a stride of 4. 
The next 64 MPI tasks will be laid out on the second set of 64 hardware processors. 
If you had set ROOTPE_OCN=64 in this example, then a total of 176 processors would have been requested and the atmosphere would have been laid out on the first 64 hardware processors in 16x4 fashion, and the ocean model would have been laid out on hardware processors 113-176. 
Hardware processors 65-112 would have been allocated but completely idle.

| 

**Note**: ``env_mach_pes.xml`` *cannot* be modified after "./case.setup" has been invoked without first invoking "case.setup -clean". 
For an example of changing pes, see the `Section called *BASICS: How do I change processor counts and component layouts on processors?* in Chapter 6 <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

Modifying an xml file
---------------------

You can edit the xml files directly to change the variable values. 
However, modification of the xml variables is best done using **xmlchange** in the ``$CASEROOT`` directory since it performs variable error checking as part of changing values in the xml files. 
To invoke **xmlchange**:
::

   xmlchange <entry id>=<value>
   -- OR --
   xmlchange -id <entry id> -val <name> -file <filename>  
             [-help] [-silent] [-verbose] [-warn] [-append] [-file]

-id

  The xml variable name to be changed. (required)

-val

  The intended value of the variable associated with the -id argument. (required)

  **Note**: If you want a single quotation mark ("'", also called an apostrophe) to appear in the string provided by the -val option, you must specify it as "&apos;".

-file

  The xml file to be edited. (optional)

-silent

  Turns on silent mode. Only fatal messages will be issued. (optional)

-verbose

  Echoes all settings made by **create_newcase** and **case.setup**. (optional)

-help

  Print usage info to STDOUT. (optional)

Multi-instance component functionality
--------------------------------------

The CIME coupling infrastructure has the capability to run multiple component instances under one model executable. 
The only caveat to this usage is that if N multiple instances of any one active component is used, then N multiple instances of ALL active components are required. 
More details are discussed below. 
The primary motivation for this development was to be able to run an ensemble Kalman-Filter for data assimilation and parameter estimation (e.g. UQ). 
However, it also provides you with the ability to run a set of experiments within a single model executable where each instance can have a different namelist, and have all the output go to one directory. 

In the following an F compset will be used as an illustration. Utilizing the multiple instance code involves the following steps:

1. create the case
::

   > create_newcase -case Fmulti -compset F -res ne30_g16 
   > cd Fmulti

2. Lets assume the following out of the box pe-layout 
::

   NTASKS(ATM)=128, NTHRDS(ATM)=1, ROOTPE(ATM)=0, NINST(ATM)=1
   NTASKS(LND)=128, NTHRDS(LND)=1, ROOTPE(LND)=0, NINST(LND)=1
   NTASKS(ICE)=128, NTHRDS(ICE)=1, ROOTPE(ICE)=0, NINST(ICE)=1
   NTASKS(OCN)=128, NTHRDS(OCN)=1, ROOTPE(OCN)=0, NINST(OCN)=1
   NTASKS(GLC)=128, NTHRDS(GLC)=1, ROOTPE(GLC)=0, NINST(GLC)=1
   NTASKS(WAV)=128, NTHRDS(WAV)=1, ROOTPE(WAV)=0, NINST(WAV)=1
   NTASKS(CPL)=128, NTHRDS(CPL)=1, ROOTPE(CPL)=0

In this F compset, the atm, lnd, rof are full prognostic components, the ocn is a prescribed data component, cice is a mixed prescribed/prognostic component (ice-coverage is prescribed) and glc and wav are stub components. 
Lets say we want to run 2 instances of CAM in this experiment. 
The current implementation of multi-instances will also require you to run 2 instances of CLM, CICE and RTM. 
However, you have the flexibility to run either 1 or 2 instances of DOCN (we can ignore glc and wav since they do not do anything in this compset). 
To run 2 instances of CAM, CLM, CICE, RTM and DOCN, all you need to do is to invoke the following command in your ``$CASEROOT``:
::

   ./xmlchange NINST_ATM=2
   ./xmlchange NINST_LND=2
   ./xmlchange NINST_ICE=2
   ./xmlchange NINST_ROF=2
   ./xmlchange NINST_OCN=2

As a result of this, you will have 2 instances of CAM, CLM and CICE (prescribed), RTM, and DOCN,  each running concurrently on 64 MPI tasks  **TODO: put in reference to xmlchange".**

3. Setup the case
::

   > ./case.setup

New user_nl_xxx_NNNN file (where NNNN is the number of the component instances) will be generated when **case.setup** is called. 
In particular, calling **case.setup** with the above ``env_mach_pes.xml`` file will result in the following ``user_nl_*`` files in ``$CASEROOT``
::

   user_nl_cam_0001,  user_nl_cam_0002
   user_nl_cice_0001, user_nl_cice_0002
   user_nl_clm_0001,  user_nl_clm_0002
   user_nl_rtm_0001,  user_nl_rtm_0002
   user_nl_docn_0001, user_nl_docn_0002
   user_nl_cpl

and the following ``*_in_*`` files and ``*txt*`` files in $CASEROOT/CaseDocs:
::

   atm_in_0001, atm_in_0002
   docn.streams.txt.prescribed_0001, docn.streams.txt.prescribed_0002
   docn_in_0001, docn_in_0002
   docn_ocn_in_0001, docn_ocn_in_0002
   drv_flds_in, drv_in
   ice_in_0001, ice_in_0002
   lnd_in_0001, lnd_in_0002
   rof_in_0001, rof_in_0002

The namelist for each component instance can be modified by changing the corresponding user_nl_xxx_NNNN file for that component instance. 
Modifying the user_nl_cam_0002 will result in the namelist changes you put in to be active ONLY for instance 2 of CAM. 
To change the DOCN stream txt file instance 0002, you should place a copy of ``docn.streams.txt.prescribed_0002`` in ``$CASEROOT`` with the name ``user_docn.streams.txt.prescribed_0002`` and modify it accordlingly.

It is also important to stress the following points:

1. **Different component instances can ONLY differ by differences in namelist settings - they are ALL using the same model executable.**

2. Only 1 coupler component is supported currently in multiple instance implementation.

3. ``user_nl_*`` files once they are created by **case.setup** *ARE NOT* removed by calling **caes.setup -clean**. 

4. In general, you should run multiple instances concurrently (the default setting in ``env_mach_pes.xml``). 
   The serial setting is only for EXPERT USERS in upcoming development code implementations.



Cloning a case
---------------------
This is an advanced feature provided for expert users. If you are a new user, skip this section.

If you have access to the run you want to clone, the **create_clone** command will create a new case while also preserving local modifications to the case that you want to clone. 
You can run the utility **create_clone** either from ``$CCSMROOT`` or from the directory where you want the new case to be created. 
It has the following arguments:

-case

  The name or path of the new case.

-clone

  The full pathname of the case to be cloned.

-silent

  Enables silent mode. Only fatal messages will be issued.

-verbose

  Echoes all settings.

-help

  Prints usage instructions.

Here is the simplest example of using **create_clone**:
::

   > cd $CCSMROOT/scripts
   > create_clone -case $CASEROOT -clone $CLONEROOT 

**create_clone** will preserve any local namelist modifications made in the user_nl_xxxx files as well as any source code modifications in the SourceMods tree. 

**Important**:: Do not change anything in the ``env_case.xml`` file. 
The ``$CASEROOT/`` directory will now appear as if **create_newcase** had just been run -- with the exception that local modifications to the env_* files are preserved.

Another approach to duplicating a case is to use the information in that case's ``README.case`` and ``CaseStatus`` files to create a new case and duplicate the relevant ``xlmchange`` commands that were issued in the original case. 
Note that this approach will *not* preserve any local modifications that were made to the original case, such as source-code or build-script modifications; you will need to import those changes manually.

