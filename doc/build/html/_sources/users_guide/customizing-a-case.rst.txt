.. _customizing-a-case:

**************************************************
Customizing a case
**************************************************

All CIME_compliant components generate their namelist settings using the ``cime_config/buildnml`` file located in the component's directory tree.
As an example, the CIME data atmosphere model (DATM), generates namelists using the script ``$CIMEROOT/components/data_comps/datm/cime_config/buildnml``.

User specific component namelist changes should only be made only by:
-  editing the ``$CASEROOT/user_nl_xxx`` files 
-  using :ref:`**xmlchange**<modifying-an-xml-file>` to modify xml variables in ``env_run.xml``, ``env_build.xml`` or ``env_mach_pes.xml`` 

You can preview the component namelists by running **preview_namelists** from ``$CASEROOT``. 
Calling **preview_namelists** results in the creation of component namelists (e.g. atm_in, lnd_in, .etc) in ``$CASEROOT/CaseDocs/``. 
The namelist files created in the ``CaseDocs/`` are there only for user reference and SHOULD NOT BE EDITED since they are overwritten every time ``preview_namelists``  and  ``case.submit`` are called. 

The following sections are a summary of how to modify CIME, CESM and ACME components following represents a summary of controlling and modifying component-specific run-time settings:

.. _modifying-an-xml-file:

=================================================
Modifying an xml file
=================================================

Modification of ``$CASEROOT`` xml variables the ``$CASEROOT`` script **xmlchange**, which performs variable error checking as part of changing values in the xml files. 

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

.. _changing-the-pe-layout:

=================================================
Customizing the PE layout 
=================================================

``env_mach_pes.xml`` determines:

- the number of processors and OpenMP threads for each component
- the number of instances of each component
-  the layout of the components across the hardware processors 

Optimizing the throughput and efficiency of a CIME experiment often involves customizing the processor (PE) layout for (see :ref:`load balancing <optimizing-processor-layout>`).
CIME provides significant flexibility with respect to the layout of components across different hardware processors. 
In general, the CIME components -- atm, lnd, ocn, ice, glc, rof, wav, and cpl -- can run on overlapping or mutually unique processors. 
Whereas each component is associated with a unique MPI communicator, the CIME driver runs on the union of all processors and controls the sequencing and hardware partitioning. 
The component processor layout is via three settings: the number of MPI tasks, the number of OpenMP threads per task, and the root MPI processor number from the global set.

The entries in ``env_mach_pes.xml`` have the following meanings:

   ========  ====================================================================================
   NTASKS    the total number of MPI tasks, a negative value indicates nodes rather than tasks
   NTHRDS    the number of OpenMP threads per MPI task
   ROOTPE    the global mpi task of the component root task, if negative, indicates nodes rather than tasks
   PSTRID    the stride of MPI tasks across the global set of pes (for now set to 1)
   NINST     the number of component instances (will be spread evenly across NTASKS)
   ========  ====================================================================================

For example, if a component has ``NTASKS=16``, ``NTHRDS=4`` and ``ROOTPE=32``, then it will run on 64 hardware processors using 16 MPI tasks and 4 threads per task starting at global MPI task 32. 
Each CIME component has corresponding entries for ``NTASKS``, ``NTHRDS``, ``ROOTPE`` and ``NINST`` in ``env_mach_pes.xml``. 

There are some important things to note.

- NTASKS must be greater or equal to 1 even for inactive (stub) components.
- NTHRDS must be greater or equal to 1. 
- If NTHRDS = 1, this generally means threading parallelization will be off for that component. 
- NTHRDS should never be set to zero.
- The total number of hardware processors allocated to a component is NTASKS * NTHRDS.
- The coupler processor inputs specify the pes used by coupler computation such as mapping, merging, diagnostics, and flux calculation. 
  This is distinct from the driver which always automatically runs on the union of all processors to manage model concurrency and sequencing.
- The root processor is set relative to the MPI global communicator, not the hardware processors counts. An example of this is below.
- The layout of components on processors has no impact on the science. 
- If all components have identical NTASKS, NTHRDS, and ROOTPE set, all components will run sequentially on the same hardware processors.

The scientific sequencing is hardwired into the driver. 
Changing processor layouts does not change intrinsic coupling lags or coupling sequencing. 
ONE IMPORTANT POINT is that for a fully active configuration, the atmosphere component is hardwired in the driver to never run concurrently with the land or ice component. 
Performance improvements associated with processor layout concurrency is therefore constrained in this case such that there is never a performance reason not to overlap the atmosphere component with the land and ice components. 
Beyond that constraint, the land, ice, coupler and ocean models can run concurrently, and the ocean model can also run concurrently with the atmosphere model.

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

**Note**: ``env_mach_pes.xml`` *cannot* be modified after "./case.setup" has been invoked without first invoking **case.setup -clean**. 

.. _changing-driver-namelists:

===================================================
Customizing driver namelists
===================================================

Driver namelist variables belong in two groups - those that are set directly from ``$CASEROOT` xml variables and those that are set by the driver utility ``$CIMEROOT/driver_cpl/cime_config/buildnml``.
All driver namelist variables are defined in ``$CIMEROOT/driver_cpl/cime_config/namelist_definition_drv.xml``. 
Those variables that can only be changed by modifying xml variables appear with the ``entry`` attribute ``modify_via_xml="xml_variable_name"``.
All other variables that appear ``$CIMEROOT/driver_cpl/cime_config/namelist_definition_drv.xml`` can be modified by adding a key-word value pair at the end of ``user_nl_cpl``.
For example, to change the driver namelist value of ``eps_frac`` to ``1.0e-15``, you should add the following line to the end of the ``user_nl_cpl``
::

   eps_frac = 1.0e-15

To see the result of this modification to ``user_nl_cpl`` call ``preview_namelists`` and verify that this new value appears in ``CaseDocs/drv_in``.

.. _changing-data-model-namelists:

===================================================
Customizing data model namelists and stream files
===================================================
------------------------
Data Atmosphere (DATM)
------------------------

DATM is discussed in detail in :ref:`data atmosphere overview <data-atm>`.
DATM can be user-customized in by either changing its namelist input or its stream files.
The namelist file for DATM is ``datm_in`` (or ``datm_in_NNN`` for multiple instances). 

- To modify ``datm_in``, add the appropriate keyword/value pair(s) for the namelist changes you want at the end of the ``$CASEROOT`` file ``user_nl_datm`` (or ``user_nl_datm_NNN`` for multiple instances).

- To modify the contents of a DATM stream file, first use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``. Then:

  1. place a *copy* of this file in ``$CASEROOT`` with the string *"user_"* prepended
  2. **Make sure you change the permissions of the file to be writeable** (chmod 644)
  3. modify the ``user_datm.streams.txt.*`` file.

As an example, if the stream txt file in ``CaseDocs/`` is datm.streams.txt.CORE2_NYF.GISS, the modified copy in ``$CASEROOT`` should be ``user_datm.streams.txt.CORE2_NYF.GISS``. 
After calling **preview_namelists** again, you should see your new modifications appear in ``CaseDocs/datm.streams.txt.CORE2_NYF.GISS``.

------------------------
Data Ocean (DOCN)
------------------------

DOCN is discussed in detail in :ref:`data ocean overview <data-ocean>`.
DOCN can be user-customized in by either changing its namelist input or its stream files.
The namelist file for DOCN is ``docn_in`` (or ``docn_in_NNN`` for multiple instances) and its values can be changed by editing the ``$CASEROOT`` file ``user_nl_docn`` (or ``user_nl_docn_NNN`` for multiple instances).

- To modify ``docn_in``, add the appropriate keyword/value pair(s) for the namelist changes you want at the end of the ``$CASEROOT`` file ``user_nl_docn`` (or ``user_nl_docn_NNN`` for multiple instances).

- To modify the contents of a DOCN stream file, first use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``. Then:

  1. place a *copy* of this file in ``$CASEROOT`` with the string *"user_"* prepended
  2. **Make sure you change the permissions of the file to be writeable** (chmod 644)
  3. modify the ``user_docn.streams.txt.*`` file.

As an example, if the stream text file in ``CaseDocs/`` is ``docn.stream.txt.prescribed``, the modified copy in ``$CASEROOT`` should be ``user_docn.streams.txt.prescribed``. 
After changing this file and calling **preview_namelists** again, you should see your new modifications appear in ``CaseDocs/docn.streams.txt.prescribed``.

------------------------
Data Sea-ice (DICE)
------------------------

DICE is discussed in detail in :ref:`data sea-ice overview <data-seaice>`.
DICE can be user-customized in by either changing its namelist input or its stream files.
The namelist file for DICE is ``dice_in`` (or ``dice_in_NNN`` for multiple instances) and its values can be changed by editing the ``$CASEROOT`` file ``user_nl_dice`` (or ``user_nl_dice_NNN`` for multiple instances).

- To modify ``dice_in``, add the appropriate keyword/value pair(s) for the namelist changes you want at the end of the ``$CASEROOT`` file ``user_nl_dice`` (or ``user_nl_dice_NNN`` for multiple instances).

- To modify the contents of a DICE stream file, first use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``. Then:

  1. place a *copy* of this file in ``$CASEROOT`` with the string *"user_"* prepended
  2. **Make sure you change the permissions of the file to be writeable** (chmod 644)
  3. modify the ``user_dice.streams.txt.*`` file.

------------------
Data Land (DLND)
------------------

DLND is discussed in detail in :ref:`data land overview <data-lnd>`.
DLND can be user-customized in by either changing its namelist input or its stream files.
The namelist file for DLND is ``dlnd_in`` (or ``dlnd_in_NNN`` for multiple instances) and its values can be changed by editing the ``$CASEROOT`` file ``user_nl_dlnd`` (or ``user_nl_dlnd_NNN`` for multiple instances).

- To modify ``dlnd_in``, add the appropriate keyword/value pair(s) for the namelist changes you want at the end of the ``$CASEROOT`` file ``user_nl_dlnd`` (or ``user_nl_dlnd_NNN`` for multiple instances).

- To modify the contents of a DLND stream file, first use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``. Then:

  1. place a *copy* of this file in ``$CASEROOT`` with the string *"user_"* prepended
  2. **Make sure you change the permissions of the file to be writeable** (chmod 644)
  3. modify the ``user_dlnd.streams.txt.*`` file.

------------------
Data River (DROF)
------------------

DROF is discussed in detail in :ref:`data river overview <data-river>`.
DROF can be user-customized in by either changing its namelist input or its stream files.
The namelist file for DROF is ``drof_in`` (or ``drof_in_NNN`` for multiple instances) and its values can be changed by editing the ``$CASEROOT`` file ``user_nl_drof`` (or ``user_nl_drof_NNN`` for multiple instances).

- To modify ``drof_in``, add the appropriate keyword/value pair(s) for the namelist changes you want at the end of the ``$CASEROOT`` file ``user_nl_drof`` (or ``user_nl_drof_NNN`` for multiple instances).

- To modify the contents of a DROF stream file, first use **preview_namelists** to obtain the contents of the stream txt files in ``CaseDocs/``. Then:

  1. place a *copy* of this file in ``$CASEROOT`` with the string *"user_"* prepended
  2. **Make sure you change the permissions of the file to be writeable** (chmod 644)
  3. modify the ``user_drof.streams.txt.*`` file.

=================================================================
Customizing CESM active component-specific namelist settings
=================================================================

---
CAM
---

CAM's `configure <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `build-namelist <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ utilities are called by ``Buildconf/cam.buildnml.csh``. 
`CAM_CONFIG_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, `CAM_NAMELIST_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `CAM_NML_USECASE <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ are used to set compset variables (e.g., "-phys cam5" for CAM_CONFIG_OPTS) and in general should not be modified for supported compsets. 
For a complete documentation of namelist settings, see `CAM namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. 
To modify CAM namelist settings, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_cam`` file (see the documentation for each file at the top of that file). 
For example, to change the solar constant to 1363.27, modify the ``user_nl_cam`` file to contain the following line at the end "solar_const=1363.27". 
To see the result of adding this, call **preview_namelists** and verify that this new value appears in ``CaseDocs/atm_in``.

---
CLM
---

CIME generates the CLM namelist variables by calling ``$SRCROOT/components/clm/cime_config/buildnml``.
CLM-specific CIME xml variables are set in ``$SRCROOT/components/clm/cime_config/config_component.xml`` and are used by CLM's ``buildnml`` script to generate the namelist.
For a complete documentation of namelist settings, see `CLM namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. 
To modify CLM namelist settings, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_clm`` file 
To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/lnd_in``.

---
RTM
---

CIME generates the RTM namelist variables by calling ``$SRCROOT/components/rtm/cime_config/buildnml``. 
For a complete documentation of namelist settings, see RTM namelist variables. 
To modify RTM namelist settings you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_rtm`` file.
To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/rof_in``.

---
CICE
---

CICE's `configure <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ and `build-namelist <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ utilities are now called by ``Buildconf/cice.buildnml.csh``. Note that `CICE_CONFIG_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, and `CICE_NAMELIST_OPTS <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ are used to set compset specific variables and in general should not be modified for supported compsets. For a complete documentation of namelist settings, see `CICE namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. To modify CICE namelist settings, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_cice`` file (see the documentation for each file at the top of that file). To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/ice_in``.

In addition, **case.setup** creates CICE's compile time `block decomposition variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ in ``env_build.xml`` as follows:
::

   ./case.setup
     ⇓
   Buildconf/cice.buildnml.csh and $NTASKS_ICE and $NTHRDS_ICE
     ⇓
   env_build.xml variables CICE_BLCKX, CICE_BLCKY, CICE_MXBLCKS, CICE_DECOMPTYPE 
   CPP variables in cice.buildexe.csh
   

----
POP2
----
See `POP2 namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for a complete description of the POP2 run-time namelist variables. Note that `OCN_COUPLING, OCN_ICE_FORCING, OCN_TRANSIENT <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ are normally utilized ONLY to set compset specific variables and should not be edited. For a complete documentation of namelist settings, see `CICE namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_. To modify POP2 namelist settings, you should add the appropriate keyword/value pair at the end of the ``$CASEROOT/user_nl_pop2`` file (see the documentation for each file at the top of that file). To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/ocn_in``.

In addition, **cesm_setup** also generates POP2's compile time compile time `block decomposition variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ in ``env_build.xml`` as follows:
::

   ./cesm_setup  
       ⇓
   Buildconf/pop2.buildnml.csh and $NTASKS_OCN and $NTHRDS_OCN
       ⇓
   env_build.xml variables POP2_BLCKX, POP2_BLCKY, POP2_MXBLCKS, POP2_DECOMPTYPE 
   CPP variables in pop2.buildexe.csh

CISM
----
See `CISM namelist variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ for a complete description of the CISM run-time namelist variables. This includes variables that appear both in ``cism_in`` and in ``cism.config``. To modify any of these settings, you should add the appropriate keyword/value pair at the end of the ``user_nl_cism`` file (see the documentation for each file at the top of that file). To see the result of your change, call **preview_namelists** and verify that the changes appear correctly in ``CaseDocs/cism_in`` and ``CaseDocs/cism.config``.

There are also some run-time settings set via ``env_run.xml``, as documented in `CISM run time variables <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ - in particular, the model resolution, set via ``CISM_GRID``. The value of ``CISM_GRID`` determines the default value of a number of other namelist parameters.

================================================================
Customizing ACME active component-specific namelist settings
================================================================

