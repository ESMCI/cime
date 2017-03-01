.. _porting:

*********************************************
Porting and Validating CIME on a new Platform
*********************************************

===================
Porting Overview 
===================

One of the first steps many users will have to address is getting CIME based models running on their local machine. 
This section will describe that process. 
It is usually very helpful to assure that you can run a basic mpi parallel program on your machine prior to attempting a CIME port. 
Understanding how to compile and run the program fhello_world_mpi.F90 shown here could potentially save many hours of frustration.
::

   program fhello_world_mpi.F90
     use mpi
     implicit none
     integer ( kind = 4 ) error
     integer ( kind = 4 ) id
     integer p
     character(len=MPI_MAX_PROCESSOR_NAME) :: name
     integer clen
     integer, allocatable :: mype(:)
     real ( kind = 8 ) wtime

     call MPI_Init ( error )
     call MPI_Comm_size ( MPI_COMM_WORLD, p, error )
     call MPI_Comm_rank ( MPI_COMM_WORLD, id, error )
     if ( id == 0 ) then
        wtime = MPI_Wtime ( )
     
	write ( *, '(a)' ) ' '
	write ( *, '(a)' ) 'HELLO_MPI - Master process:'
	write ( *, '(a)' ) '  FORTRAN90/MPI version'
	write ( *, '(a)' ) ' '
        write ( *, '(a)' ) '  An MPI test program.'
        write ( *, '(a)' ) ' '
        write ( *, '(a,i8)' ) '  The number of processes is ', p
        write ( *, '(a)' ) ' '
     end if
     call MPI_GET_PROCESSOR_NAME(NAME, CLEN, ERROR)
     write ( *, '(a)' ) ' '
     write ( *, '(a,i8,a,a)' ) '  Process ', id, ' says "Hello, world!" ',name(1:clen)

     call MPI_Finalize ( error )
   end program

Once you are assured that you have a basic functional MPI environment you will need to provide a few prerequisite tools for building and running CIME. 
  
- A python interpreter version 2.7 or newer
- Build tools gmake and cmake 
- A netcdf library version 4.3 or newer built with the same compiler you will use for CIME
- Optionally a pnetcdf library.

The following steps should be followed:

1. Create a ``$HOME/.cime`` directory

2. Copy the template file ``$CIME/config/xml_schemas/config_machines_template.xml`` to ``$HOME/.cime/config_machines.xml``

3. Fill in the contents of ``$HOME/.cime/config_machines.xml`` that specific to your machine. 
   This file contains all the information that a user needs to set to configure a new machine to be CIME complaint. 
   For more details see :ref:`customize the config_machines.xml file <customizing-machine-file>`. 
   The completed file should conform to the schema definition provided, check it using: 
   ::

      xmllint --noout --schema $CIME/config/xml_schemas/config_machines.xsd $HOME/.cime/config_machines.xml

4. The files ``config_batch.xml`` and ``config_compilers.xml`` may also need specific adjustments for your batch system and compiler. 
   You can edit these files in place to add your machine configuration or you can place your custom configuration files in the directory ``$HOME/.cime/``.  
   We recommend the latter approach. All files in ``$HOME/.cime/`` are appended to the xml objects read into memory.

5. Once you have a basic configuration for your machine defined in your new ``$HOME/.cime`` XML files, you should try the ``scripts_regression_test`` in directory ``$CIME/scripts/tests``. 
   This script will run a number of basic unit tests starting from the simplest issues and working toward more complicated ones.

6. Finally when all the previous steps have run correctly, you are ready to try a case at your target compset and resolution.
   Once you have successfully created the required xml files in your .cime directory and are satisfied with the results you can merge them into the default files in the ``config/$CIME_MODEL/machines`` directory.   
   If you would like to make this machine definition available generally you may then issue a pull request to add your changes to the git repository.  
   
===================================================
Enabling out-of-the-box capability for your machine
===================================================

.. _customizing-machine-file:

Customizing the machines file for your machine
----------------------------------------------

Machine specific files are defined in the model-specific :ref:`config_machines.xml <defining-machines>`.

The first step a user must take to make their machine CIME-compatible is to add the appropriate entries for their machine in ``config_machines.xml``.

Each ``<machine>`` tag requires the following input: 

- ``DESC``: a text description of the machine, this field is current not used
- ``NODENAME_REGEX``: a regular expression used to identify this machine it must work on compute nodes as well as login nodes, use machine option to create_test or create_newcase if this flag is not available 
- ``OS``: the operating system of this machine. 
- ``PROXY``: optional http proxy for access to the internet
- ``COMPILERS``: compilers supported on this machine, comma seperated list, first is default 
- ``MPILIBS``: mpilibs supported on this machine, comma seperated list, first is default 
- ``PROJECT``: A project or account number used for batch jobs can be overridden in environment or $HOME/.cime/config 
- ``SAVE_TIMING_DIR``: (Acme only) directory to write timing output to 
- ``CIME_OUTPUT_ROOT``: Base directory for case output, the bld and run directories are written below here 
- ``DIN_LOC_ROOT``: location of the inputdata directory 
- ``DIN_LOC_ROOT_CLMFORC``: optional input location for clm forcing data  
- ``DOUT_S_ROOT``: root directory of short term archive files 
- ``DOUT_L_MSROOT``: root directory on mass store system of long term archive files
- ``BASELINE_ROOT``:  Root directory for system test baseline files 
- ``CCSM_CPRNC``: location of the cprnc tool, compares model output in testing
- ``GMAKE``: gnu compatible make tool, default is 'gmake' 
- ``GMAKE_J``: optional number of threads to pass to the gmake flag 
- ``TESTS``: (acme only) list of tests to run on this machine 
- ``BATCH_SYSTEM``: batch system used on this machine (none is okay) 
- ``SUPPORTED_BY``: contact information for support for this system 
- ``MAX_TASKS_PER_NODE``: maximum number of threads*tasks per shared memory node on this machine
- ``PES_PER_NODE``: number of physical PES per shared node on this machine, in practice the MPI tasks per node will not exceed this value 
- ``PROJECT_REQUIRED``: Does this machine require a project to be specified to the batch system? 
- ``mpirun``: The mpi exec to start a job on this machine. 
  This is itself an element that has sub elements that must be filled:

  * Must have a required ``<executable>`` element 
  * May have optional attributes of ``compiler``, ``mpilib`` and/or ``threaded``
  * May have an optional ``<arguments>`` element which in turn contain one or more ``<arg>`` elements. 
    These specify the arguments to the mpi executable and as a result are dependent on your mpi library implementation.


- ``module_system``: How and what modules to load on this system. Module systems allow you to easily load multiple compiler environments on a given machine. CIME provides support for two types of module tools: `module <http://www.tacc.utexas.edu/tacc-projects/mclay/lmod>`_ and `soft  <http://www.mcs.anl.gov/hs/software/systems/softenv/softenv-intro.html>`_.   If neither of these are available on your machine, the simply set ``<module_system type="none"\>``.
   
- ``environment_variables``: environment_variables to set on this system. 
   This contains sub elements, ``<env>`` with the ``name`` attribute specifying the environment variable name, and the element value specifying the corresponding environment variable value. If the element value is not set, then the corresponding environment variable will be unset in your shell. 

   As an example, the following sets the environment variable ``OMP_STACKSIZE`` to 256M.
   ::

      <env name="OMP_STACKSIZE">256M</env>

   and the following unsets this environment variable in the shell:
   ::

      <env name="OMP_STACKSIZE"></env>

   .. note:: These changes are **ONLY** activated for the CIME build and run environment, **BUT NOT** for your login shell. To activate them for your login shell, you would source either ``$CASEROOT/.env_mach_specific.sh`` or ``$CASEROOT/.env_mach_specific.csh``, depending on your shell.

.. _customizing-batch-file:

Customizing the batch directives for your machine
--------------------------------------------------

The **config_batch.xml** schema is defined in ``$CIMEROOT/config/xml_schemas/config_batch.xml``
config batch currently supports batch systems: pbs, cobalt, lsf and slurm.
General configurations for each system are provided at the top of the file and specific modifications for a
given machine are provided below.  In particular each machine should define its own queues.   Following
machine specific queue details is a batch_jobs section, this section of the file describes each job that will
be submitted to the queue for a CIME workflow, the template file that will be used to generate that job and
the prerequisets that must be met before the job is submitted and dependancies that must be satisfied
before that job is run.   By default the CIME workflow consists of three jobs (case.run, case.st_archive, and
case.lt_archive) there is also a case.test file that is used by the CIME system test workflow. 

.. _customizing-compiler-file:

Customize the compiler options for your machine
------------------------------------------------

.. todo:: Jim Edwards add the contents of this section 

====================================================
Validating your port
====================================================

The following port validation is recommended for any new machine. 
Carrying out these steps does not guarantee the model is running properly in all cases nor that the model is scientifically valid on the new machine. 
In addition to these tests, detailed validation should be carried out for any new production run. 
That means verifying that model restarts are bit-for-bit identical with a baseline run, that the model is bit-for-bit reproducible when identical cases are run for several months, and that production cases are monitored very carefully as they integrate forward to identify any potential problems as early as possible. 
These are recommended steps for validating a port and are largely functional tests. 
Users are responsible for their own validation process, especially with respect to science validation.

1. Verify functionality by performing these `functionality tests <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.
::

   ERS_D.f19_g16.X
   ERS_D.T31_g37.A
   ERS_D.f19_g16.B1850CN
   ERI.ne30_g16.X
   ERI.T31_g37.A
   ERI.f19_g16.B1850CN
   ERS.ne30_ne30.F
   ERS.f19_g16.I
   ERS.T62_g16.C
   ERS.T62_g16.DTEST
   ERT.ne30_g16.B1850CN

2. Verify performance and scaling analysis.

   a. Create one or two `load-balanced <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ configurations to check into ``Machines/config_pes.xml`` for the new machine.

   b. Verify that performance and scaling are reasonable.

   c. Review timing summaries in ``$CASEROOT`` for load balance and throughput.

   d. Review coupler "daily" timing output for timing inconsistencies. 
      As has been mentioned in the section on `load balancing a case <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_, useful timing information is contained in cpl.log.$date file that is produced for every run. 
      The cpl.log file contains the run time for each model day during the model run. 
      This diagnostic is output as the model runs. 
      You can search for tStamp in this file to see this information. 
      This timing information is useful for tracking down temporal variability in model cost either due to inherent model variability cost (I/O, spin-up, seasonal, etc) or possibly due to variability due to hardware. 
      The model daily cost is generally pretty constant unless I/O is written intermittently such as at the end of the month.

3. Perform validation (both functional and scientific):

   a. Perform a new CIME validation test (**TODO: fill this in**)

   b. Follow the `CCSM4.0 CICE port-validation procedure <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

   c. Follow the `CCSM4.0 POP2 port-validation procedure <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_.

4. Perform two, one-year runs (using the expected load-balanced configuration) as separate job submissions and verify that atmosphere history files are bfb for the last month. 
   Do this after some performance testing is complete; you may also combine this with the production test by running the first year as a single run and the second year as a multi-submission production run. 
   This will test reproducibility, exact restart over the one-year timescale, and production capability all in one test.

5. Carry out a 20-30 year 1.9x2.5_gx1v6 resolution, B_1850_CN compset simulation and compare the results with the diagnostics plots for the 1.9x2.5_gx1v6 Pre-Industrial Control (see the `CCSM4.0 diagnostics <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_). 
   Model output data for these runs will be available on the `Earth System Grid (ESG) <http://www.cesm.ucar.edu/models/cesm2.0/external-link-here>`_ as well.




