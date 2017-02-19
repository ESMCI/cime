.. _faq-user-defined-grid:

---------------------------
Adding a user-defined grid
---------------------------

CIME is accompanied by support for numerous out-of-the box model resolutions. To see the supported grids call **manange_case --query-grids**.
In general, CIME model grids are associated with a specific combination of atmosphere, land, land-ice, river-runoff and ocean/ice grids. The naming convention for these grids still only involves atmosphere, land, and ocean/ice grid specifications.

The most common resolutions have the atmosphere and land components on one grid and the ocean and ice on a second grid.
The naming convention looks like *f19_g16*, where the f19 indicates that the atmosphere and land are on the 1.9x2.5 (finite volume dycore) grid while the g16 means the ocean and ice are on the gx1v6 one-degree displaced pole grid. 
While it is not supported, as of CESM1.
.1 does have the ability to run with the atmosphere and land also separated. 
The naming convention for these trigrid cases looks like *ne30_f19_g16*, where the ne30 means that the atmosphere is on the 30-element (spectral-element dycore) grid while the land is still on the finite volume grid and the ocean / ice are still on the gx1v6 grid.
This document will outline how to set up the more complicated trigrid case, but will also highlight what steps can be skipped if the atmosphere and land do not need to be separated.

CIME provides support for you to add your own specific component grid combinations.
To achieve this, CIME has a ``$CIMEROOT/tools/mapping/``. 
A brief list of the steps needed to add a new component grid to the model system follows.
Again, this process can be simplified if the atmosphere and land are running on the same grid.

1. Start with SCRIP grid files for atmosphere, land, and ocean.
   You must first create or obtain SCRIP format grid files for the atmosphere, land and ocean grids. At present there is no supported functionality for creating the SCRIP format file, although that is planned for CESM1.2. (check)

2. Build the ``check_map`` utility.
   When you add new user-defined grid files, you will also need to generate a set of mapping files so the coupler can send data from a component on one grid to a component on another grid. There is an ESMF tool that tests the mapping file by comparing a mapping of a smooth function to its true value on the destination grid. We have tweaked this utility to test a suite of of smooth functions, as well as ensure conservation (when the map is conservative). Before generating mapping functions it is *highly recommended* that you build this utility.

   To build this tool, follow the instructions in ``$CCSMROOT/mapping/check_maps/INSTALL``. As with many of the steps in this document, you will need to have the `ESMF <http://www.cesm.ucar.edu/models2.0/external-link-here>`_ toolkit installed. It is installed by default on most NCAR computers.

3. Generate ``atm<->ocn``, ``atm<->lnd``, ``lnd<->rtm``, and ``ocn->lnd`` mapping files.

Using the SCRIP grid files from step one, you must generate a set of conservative (area-averaged) and non-conservative (patch and bilinear) mapping files.
You can do this by calling **gen_cesm_maps.sh** in ``$CCSMROOT/tools/mapping/gen_mapping_files/``. 
This shell script generates all the mapping files needed except rtm->ocn, which is discussed below.
This script uses the ESMF offline weight generation utility, which you must build *prior* to running **gen_cesm_maps.sh**.

The ``README file`` in the ``gen_mapping_files/`` directory contains details on how to run **gen_cesm_maps.sh**. The basic usage is
::

   > cd $CCSMROOT/mapping/gen_mapping_files
   > ./gen_cesm_maps.sh \
       --fileocn  <input SCRIP ocn_grid full pathname>  \
       --fileatm  <input SCRIP atm grid full pathname>  \
       --filelnd  <input SCRIP lnd grid full pathname>  \
       --filertm  <input SCRIP rtm grid full pathname>  \
       --nameocn  <ocnname in output mapping file> \ 
       --nameatm  <atmname in output mapping file> \ 
       --namelnd  <lndname in output mapping file> \ 
       --namertm  <rtmname in output mapping file> 

This command will generate the following mapping files:
::

   map_atmname_TO_ocnname_aave.yymmdd.nc
   map_atmname_TO_ocnname_blin.yymmdd.nc
   map_atmname_TO_ocnname_patc.yymmdd.nc
   map_ocnname_TO_atmname_aave.yymmdd.nc
   map_ocnname_TO_atmname_blin.yymmdd.nc
   map_atmname_TO_lndname_aave.yymmdd.nc
   map_atmname_TO_lndname_blin.yymmdd.nc
   map_lndname_TO_atmname_aave.yymmdd.nc
   map_ocnname_TO_lndname_aave.yymmdd.nc
   map_lndname_TO_rtmname_aave.yymmdd.nc
   map_rtmname_TO_lndname_aave.yymmdd.nc

Notes:
- You do not need to specify all four grids. For example, if you are running with the atmosphere and land on the same grid, then you do not need to specify the land grid (and atm<->rtm maps will be generated). If you also omit the runoff grid, then only the 5 atm<->ocn maps will be generated.
- ESMF_RegridWeightGen runs in parallel, and the ``gen_cesm_maps.sh`` script has been written to run on yellowstone. To run on any other machine, you may need to add some environment variables to ``$CCSMROOT/mapping/gen_mapping_files/gen_ESMF_mapping_file/create_ESMF_map.sh`` -- search for hostname to see where to edit the file.

Example (run on Nov 5, 2012):
::

   > ./gen_cesm_maps.sh \
        -focn /CESM/cseg/mapping/grids/gx3v7_120309.nc -nocn g37 \
        -fatm /CESM/cseg/mapping/grids/ne16np4_110512_pentagons.nc -natm ne16np4 \
        -frtm /CESM/cseg/mapping/grids/r05_nomask_070925.nc -nrtm r05

Results in the following files
::

   > ls -1 map*
   map_g37_TO_ne16np4_aave.121105.nc
   map_g37_TO_ne16np4_blin.121105.nc
   map_ne16np4_TO_g37_aave.121105.nc
   map_ne16np4_TO_g37_blin.121105.nc
   map_ne16np4_TO_g37_patc.121105.nc
   map_ne16np4_TO_r05_aave.121105.nc
   map_r05_TO_ne16np4_aave.121105.nc

4. Generate atmosphere, land and ocean / ice domain files.

Using the conservative ocean to land and ocean to atmosphere mapping files created in the previous step, you can create domain files for the atmosphere, land, and ocean; these are basically grid files with consistent masks and fractions. You make these files by calling **gen_domain** in ``$CCSMROOT/mapping/gen_domain_files``.
The ``INSTALL`` file in the ``gen_domain_files/`` directory contains details on how to build the **gen_domain** executable. After you have built it, the README in the same directory contains details on how to use the tool. The basic usage is:
::

   > ./gen_domain -m ../gen_mapping_files/map_ocnname_TO_lndname_aave.yymmdd.nc -o ocnname -l lndname
   > ./gen_domain -m ../gen_mapping_files/map_ocnname_TO_atmname_aave.yymmdd.nc -o ocnname -l atmname

These commands will generate the following domain files:
::

   domain.lnd.lndname_ocnname.yymmdd.nc
   domain.ocn.lndname_ocnname.yymmdd.nc
   domain.lnd.atmname_ocnname.yymmdd.nc
   domain.ocn.atmname_ocnname.yymmdd.nc
   domain.ocn.ocnname.yymmdd.nc

Notes:
- If you are running with the atmosphere and land components on the same grid, you only need to execute **gen_domain** once.
- The input atmosphere grid is assumed to be unmasked (global). Land cells whose fraction is zero will have land mask = 0.
- If the ocean and land grids *are identical* then the mapping file will simply be unity and the land fraction will be one minus the ocean fraction.

5. If you are adding a new ocn or rtm grid, create a new rtm->ocn mapping file. (Otherwise you can skip this step.)
The process for mapping from the runoff grid to the ocean grid is currently undergoing many changes. At this time, if you are running with a new ocean or runoff grid, please contact Michael Levy (mlevy_AT_ucar_DOT_edu) for assistance. If you are running with standard ocean and runoff grids, the mapping file should already exist and you do not need to generate it.


6. If you are adding a new new lnd grid, create a new CLM surface dataset. (Otherwise you can skip this step.)
- Generate mapping files for CLM surface dataset (since this is a non-standard grid).

::

   > cd $CCSMROOT/models/lnd/clm/tools/mkmapdata
   > ./mkmapdata.sh --gridfile <lnd SCRIP grid file> --res <atm resolution name> --gridtype global

- Generate CLM surface dataset. Below is an example for a current day surface dataset (model year 2000).

::
   > cd  $CCSMROOT/models/lnd/clm/tools/mksurfdata_map
   > ./mksurfdata.pl -res usrspec -usr_gname <atm resolution name> -usr_gdate yymmdd -y 2000

7. Create grid file needed for create_newcase.
The next step is to create a file - call it ``mygrid.xml`` - with all the grid and domain information. Assuming the domain files that were generated earlier are in ``$DOMAIN_FILE_LOC``, the contents of this file should be
::

   <?xml version="1.0"?>
   <config_horiz_grid>
   <horiz_grid GLOB_GRID="atmgrid" nx="[size of atmgrid]" ny="[size of atmgrid]" />
   <horiz_grid GLOB_GRID="lndgrid" nx="[size of lndgrid]" ny="[size of lndgrid]" />
   <horiz_grid GLOB_GRID="ocngrid" nx="[size of ocngrid]" ny="[size of ocngrid]" />
   <horiz_grid GRID="atmgrid_lndgrid_ocngrid" SHORTNAME="atm_lnd_ocn"
               ATM_GRID="atmgrid" LND_GRID="lndgrid" OCN_GRID="ocngrid" ICE_GRID="ocngrid" 
               ATM_NCPL="48" OCN_NCPL="1"
               ATM_DOMAIN_FILE="domain.lnd.atmgrid_ocngrid.$YYYYMMDD.nc"
               LND_DOMAIN_FILE="domain.lnd.lndgrid_ocngrid.$YYYYMMDD.nc"
               ICE_DOMAIN_FILE="domain.ocn.ocngrid.$YYYYMMDD.nc"
               OCN_DOMAIN_FILE="domain.ocn.ocngrid.$YYYYMMDD.nc"
               ATM_DOMAIN_PATH="$DOMAIN_FILE_LOC"
               LND_DOMAIN_PATH="$DOMAIN_FILE_LOC"
               ICE_DOMAIN_PATH="$DOMAIN_FILE_LOC"
               OCN_DOMAIN_PATH="$DOMAIN_FILE_LOC"
               DESC="Some new trigrid setup" />
   </config_horiz_grid>

Where you only need the GLOB_GRID information for grids that are not already included in the model. For unstructured grids, nx should be the number of grid cells and ny should be 1; for structured grids, they should be the dimensions of the grid.

8. Create user_nl_cpl contents for new mapping files.

One of the many input files generated for the coupler is ``$RUNDIR/seq_maps.rc``, which contains a list of mapping files. Using an f09_g16 run on yellowstone as an example, the file will contain the following (for brevity, some lines have been cut):
::

   atm2ocnFmapname: '/glade/proj3/cseg/inputdata/cpl/cpl6/map_fv0.9x1.25_to_gx1v6_aave_da_090309.nc'
   atm2ocnSmapname: '/glade/proj3/cseg/inputdata/cpl/cpl6/map_fv0.9x1.25_to_gx1v6_bilin_da_090309.nc'
   atm2ocnVmapname: '/glade/proj3/cseg/inputdata/cpl/cpl6/map_fv0.9x1.25_to_gx1v6_bilin_da_090309.nc'
   lnd2atmFmapname: 'idmap'
   lnd2atmSmapname: 'idmap'
   lnd2rofFmapname: '/glade/proj3/cseg/inputdata/lnd/clm2/mappingdata/maps/0.9x1.25/map_0.9x1.25_nomask_to_0.5x0.5_nomask_aave_da_c120522.nc'
   lnd2rofFmaptype: 'X'
   ocn2atmFmapname: '/glade/proj3/cseg/inputdata/cpl/cpl6/map_gx1v6_to_fv0.9x1.25_aave_da_090309.nc'
   ocn2atmSmapname: '/glade/proj3/cseg/inputdata/cpl/cpl6/map_gx1v6_to_fv0.9x1.25_aave_da_090309.nc'


This file is created when you build the model namelists, and the default values are based on the grids specified when you created the case.
The model only knows what default values to use for the out-of-the-box resolutions, so you must specify what maps you have created by appending them to ``$CASE/user_nl_cpl``. 
If, for example, we've introduced a new atmosphere / land grid with a shortname newatm and created all the necessary mapping files in ``$MAPPING_FILE_LOC``, then to create a newatm_g16 run we would need to add the following to ``$CASE/user_nl_cpl``:
::

   atm2ocnFmapname='$MAPPING_FILE_LOC/map_newatm_TO_gx1v6_aave.21105.nc'
   atm2ocnSmapname='$MAPPING_FILE_LOC/map_newatm_TO_gx1v6_blin.121105.nc'
   atm2ocnVmapname='$MAPPING_FILE_LOC/map_newatm_TO_gx1v6_patc.121105.nc'
   ocn2atmFmapname='$MAPPING_FILE_LOC/map_gx1v6_TO_newatm_aave.121105.nc'
   ocn2atmSmapname='$MAPPING_FILE_LOC/map_gx1v6_TO_newatm_aave.121105.nc'
   lnd2rofFmapname='$MAPPING_FILE_LOC/map_newatm_TO_r05_aave.121105.nc'
   rof2lndFmapname='$MAPPING_FILE_LOC/map_r05_TO_newatm_aave.121105.nc'

After running ``$CASE/preview_namelists`` these changes will be reflected in ``$RUNDIR/seq_maps.rc``.

9. Test new grid.

Below assume that the new grid is an atmosphere grid.
::

   Test the new grid with all data components.
   (write an example)
   Test the new grid with CAM(newgrid), CLM(newgrid), DOCN(gx1v6), DICE(gx1v6)
   (write an example)

