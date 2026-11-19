.. _ccs-examples-multi-instance:

Multi-instance
==============
The CIME coupling infrastructure is capable of running multiple
component instances (ensembles) under one model executable.  There are
two modes of ensemble capability, single driver in which all component
instances are handled by a single driver/coupler component or
multi-driver in which each instance includes a separate driver/coupler
component. In the multi-driver mode the entire model is duplicated
for each instance while in the single driver mode only active
components need be duplicated. In most cases the multi-driver mode
will give better performance and should be used.

The primary motivation for this development was to be able to run an
ensemble Kalman-Filter for data assimilation and parameter estimation
(UQ, for example). However, it also provides the ability to run a set
of experiments within a single model executable where each instance
can have a different namelist, and to have all the output go to one
directory.


1. Create the case.

   .. code-block:: bash

      ./scripts/create_newcase --case ~/MULTI_EXAMPLE --compset F2000_DEV --res f19_f19_mg17
      cd ~/MULTI_EXAMPLE

2. Assume this is the out-of-the-box pe-layout:

   .. code-block:: bash

      Comp  NTASKS  NTHRDS  ROOTPE
      CPL :    144/     1;      0
      ATM :    144/     1;      0
      LND :    144/     1;      0
      ICE :    144/     1;      0
      OCN :    144/     1;      0
      ROF :    144/     1;      0
      GLC :    144/     1;      0
      WAV :    144/     1;      0
      ESP :      1/     1;      0

   Lets assume that the atm, lnd, rof, and glc components are activate in this compset.
   The ocn is a prescribed data component, cice is a mixed prescribed/active
   component (ice-coverage is prescribed), and wav and esp are stub
   components.

   In this example each each non-stub component will run two instances.

3. Using ``xmlchange`` the ``NINST`` can be modified for each of these components.

   .. code-block:: bash

      ./xmlchange NINST_ATM=2
      ./xmlchange NINST_LND=2
      ./xmlchange NINST_ICE=2
      ./xmlchange NINST_ROF=2
      ./xmlchange NINST_GLC=2
      ./xmlchange NINST_OCN=2

   Each of these components will have each instance run on 72 MPI tasks (NTASKS/NINST) and all using the same driver/coupler component.

   .. note::

      If a separate driver/coupler component per instance is desired, the
      ``MULTI_DRIVER`` option can be used.

      .. code-block:: bash

         ./xmlchange MULTI_DRIVER=TRUE

      This configuration will run each component instance on the original 144 tasks but will generate two copies of the model (in the same executable) for a total of 288 tasks.

4. Set up the case.

   .. code-block:: bash

      ./case.setup

   A new **user_nl_xxx_NNNN** file is generated for each component instance when ``case.setup`` is called (where xxx is the component type and NNNN is the number of the component instance).

   For example if the ``ICE`` component is ``cice`` then the following files are created in ``$CASEROOT`` after calling ``./xmlchange NINST_ICE=2`` and ``./case.setup``:
   
   .. code-block:: bash

      user_nl_cice_0001
      user_nl_cice_0002

   The namelist for each component instance can be modified by changing the corresponding **user_nl_xxx_NNNN** file.

   The components steam files can also be modified per instance. To change the DOCN stream txt file instance 0002, copy **docn.streams.txt.prescribed_0002** to your **$CASEROOT** directory with the name **user_docn.streams.txt.prescribed_0002** and modify it accordlingly.

   .. note::
      
      - These changes can be made when ``create_newcase`` is called using ``--ninst #`` where # is a positive integer, and ``--multi-driver`` to invoke the multi-driver mode.
      - Multiple component instances can differ ONLY in namelist settings; they ALL use the same model executable.
      - Calling ``case.setup`` with ``--clean`` *DOES NOT* remove the **user_nl_xxx_NN** (where xxx is the component name) files created by ``case.setup``.
      - A special variable NINST_LAYOUT is provided for some experimental compsets, its value should be 'concurrent' for all but a few special cases and it cannot be used if MULTI_DRIVER=TRUE.
      - Using ``create_test`` these options can be invoked with testname modifiers ``_N#`` for the single driver mode and ``_C#`` for the multi-driver mode.  These are mutually exclusive options.
      - In multi-driver mode you will always get 1 instance of each component for each driver/coupler, if you change a case using ``./xmlchange MULTI_COUPLER=TRUE`` you will get a number of driver/couplers equal to the maximum NINST value over all components.
