.. _case-basics:

*********************************
The basics of CIME cases 
*********************************

Two neccessary concepts to understand before working with CIME are component sets and model grids.

- Component sets (usually referred to as *compsets*) define both the specific model components that will be used in a CIME case, *and* any component-specific namelist or configuration settings that are specific to this case.

- Model grids specify the grid for each component making up the model.

- At a minimum creating a CIME experiment - referred to normally as a case - requires specifying a component set and a model grid.

- Out of the box compsets and models grids are associated with two names: a longname and an alias name.

- Aliases are required by the CIME regression test system but can also be used for user convenience. Compset aliases are unique - each compset alias is associated with one and only one compset. Grid aliases, on the other hand, are overloaded and the same grid alias may result in a different grid depending on the compset the alias is associated with. We recommend that the user always confirm that the compset longname and grid longname are the expected result when using aliases to create a case.

================
 Component Sets
================

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

  If CIME is run with CESM active components, the following additional values are permitted:
  ATM  = [CAM40, CAM50, CAM55, CAM60]
  LND  = [CLM45, CLM50]
  ICE  = [CICE]
  OCN  = [POP2, AQUAP]
  ROF  = [RTM, MOSART]
  GLC  = [CISM1, CISM2]
  WAV  = [WW]
  BGC  = optional BGC scenario

  If CIME is run with ACME active components, the following additional values are permitted:
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
  calling **manage_case** with the **-list** compsets argument.
  ALL data models have a %phys option that corresponds to the data model mode.

As an example, the CESM compset longname::

   1850_CAM60_CLM50%BGC_CICE_POP2%ECO_MOSART_CISM2%NOEVOLVE_WW3_BGC%BDRD

refers to running a pre-industrial control with active CESM components CAM, CLM, CICE, POP2, MOSART, CISM2 and WW3 in a BDRD BGC coupling scenario.
The alias for this compset is B1850. Either a compset longname or a compset alias can be used as input to **create_newcase**.
It is also possible to create your own custom compset (see `How do I create my own compset? in the FAQ`)

===============================
 Model Grids
===============================

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

CIME also permits users to introduce their own :ref:`<user defined grids <adding-a-grid>`.

Component grids (such as the atmosphere grid or ocean grid above) are denoted by the following naming convention:

- "[dlat]x[dlon]" are regular lon/lat finite volume grids where dlat and dlon are the approximate grid spacing. The shorthand convention is "fnn" where nn is generally a pair of numbers indicating the resolution. An example is 1.9x2.5 or f19 for the approximately "2-degree" finite volume grid. Note that CAM uses an [nlat]x[nlon] naming convention internally for this grid.

- "Tnn" are spectral lon/lat grids where nn is the spectral truncation value for the resolution. The shorthand name is identical. An example is T85.

- "ne[X]np[Y]" are cubed sphere resolutions where X and Y are integers. The short name is generally ne[X]. An example is ne30np4 or ne30.

- "pt1" is a single grid point.

- "gx[D]v[n]" is a displaced pole grid where D is the approximate resolution in degrees and n is the grid version. The short name is generally g[D][n]. An example is gx1v7 or g17 for a grid of approximately 1-degree resolution.

- "tx[D]v[n]" is a tripole grid where D is the approximate resolution in degrees and n is the grid version.


==============================================
Querying CIME - calling **manage_case**
==============================================

The utility **$CIMEROOT/scripts/manage_case** permits you to query the out-of-the-box compsets, grids and machines that are available for either CESM or ACME.
If CIME is downloaded in a stand-alone mode, then this will only permit you to query the stand-alone CIME compsets. 
However, if CIME is part of a larger checkout that includes the prognostic components of either CESM or ACME, then **manage_case** will allow you to query all prognostic component compsets as well.

**manage_case** usage is summarized below:

  .. code-block:: python

     usage: manage_case [-h] [-d] [-v] [-s]
			[--query-compsets-setby QUERY_COMPSETS_SETBY]
			[--query-component-name QUERY_COMPONENT_NAME]
			[--query-machines] [--long]

     optional arguments:
       -h, --help            show this help message and exit
       -d, --debug           Print debug information (very verbose) to file /glade/
			     p/work/mvertens/cime.data_model_fields/scripts/manage_
			     case.log
       -v, --verbose         Add additional context (time and file) to log messages
       -s, --silent          Print only warnings and error messages
       --query-compsets-setby QUERY_COMPSETS_SETBY
			     Query compsets that are set by the target component
			     for cesm model
       --query-component-name QUERY_COMPONENT_NAME
			     Query component settings that are set by the target
			     component for cesm model
       --query-grids         Query supported model grids for cesm model
       --query-machines      Query supported machines for cesm model
       --long                Provide long output for queries


To query **manage-case** for compset information, use the ``--query-compsets-setby`` option. For CESM, the value of ``QUERY_COMPSETS_SETBY`` can be one of the following:
  ::

     allactive, drv, cam, cism, clm, cice, pop

  As an example, If you want to see what the compsets are for stand-alone CIME, issue the command 
  ::

     manage_case --query-compsets-setby drv

  And the output will be
  ::

     --------------------------------------
     Compset Short Name: Compset Long Name 
     --------------------------------------
              A : 2000_DATM%NYF_SLND_DICE%SSMI_DOCN%DOM_DROF%NYF_SGLC_SWAV
           AWAV : 2000_DATM%WW3_SLND_DICE%COPY_DOCN%COPY_SROF_SGLC_WW3
              S : 2000_SATM_SLND_SICE_SOCN_SROF_SGLC_SWAV_SESP
     ADESP_TEST : 2000_DATM%NYF_SLND_DICE%SSMI_DOCN%DOM_DROF%NYF_SGLC_SWAV_DESP%TEST
              X : 2000_XATM_XLND_XICE_XOCN_XROF_XGLC_XWAV
          ADESP : 2000_DATM%NYF_SLND_DICE%SSMI_DOCN%DOM_DROF%NYF_SGLC_SWAV_DESP
           AIAF : 2000_DATM%IAF_SLND_DICE%IAF_DOCN%IAF_DROF%IAF_SGLC_SWAV

  CIME only sets compsets associated with stand-alone CIME - i.e. primarily compsets associated only with data models. 
  Each prognostic component that is CIME compliant is responsible for setting those compsets that have the appropriate target feedbacks turned off. 
  As an example, in CESM, CAM is responsible for setting all compsets that have CAM, CLM, CICE (in prescribed ice mode) and DOCN as the components.


To query **manage_case** for component-specific compsets settings, use the ``--query-component-name`` option.  
  Every model component specifies its own definitions of what can appear after its ``%`` modifier in the compset longname, (e.g. ``DOM`` in ``DOCN%DOM``). 

  For CESM, the value of ``QUERY_COMPONENT_NAME`` can be one of the following:
  ::

     cam, datm, clm, dlnd, cice, dice, pop, aquap, docn, socn, rtm, mosart, drof, cism, ww3, dwav

  If you want to see what supported modifiers are for ``DOCN``, issue the command
  ::

     manage_case --query-compsets_setby docn

  and the output will be
  ::

     =========================================
     DOCN naming conventions
     =========================================

     _DOCN%NULL : docn null mode:
     _DOCN%COPY : docn copy mode:
     _DOCN%US20 : docn us20 mode:
     _DOCN%DOM  : docn data mode:
     _DOCN%SOM  : docn slab ocean mode:
     _DOCN%IAF  : docn interannual mode:

To query **manage_case** for the out-of-the box model grids that are supported, use the ``query-grids`` option.

To query **manage_case** for the out-of-the box machines that are supported, use the ``query-machines`` option.

For more details of how CIME determines the output for **manage_case** see :ref:`cime-internals`.


