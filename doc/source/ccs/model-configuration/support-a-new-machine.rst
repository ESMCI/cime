.. _ccs-supporting-new-machine:

Support a new machine
==============================================

One of the first steps for many users is getting CIME-based models running on their local machine.
This section describes that process.

Required libraries/packages
---------------------------

The machine needs to have:

- a functioning MPI environment (unless you plan to run on a single core with the CIME mpi-serial library).
- build tools gmake and cmake,
- a netcdf library version 4.3 or newer built with the same compiler you will use for CIME.

A pnetcdf library is optional.

If you are using MPI, make sure you can run a basic MPI parallel program on your machine before you attempt a CIME port. You can use this :ref:`MPI example <mpi-example>` to check.

.. _mpi-example:

An MPI example
---------------

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

As an example, on a MAC with 2 cores that has mpich with gnu fortran you would issue the following two commands:

::

   > mpif90 fhello_world_mpi.F90 -o hello_world
   > mpirun -np 2 ./hello_world

Linux and Mac Support
---------------------------

Your model distribution may include generic machine definitions in the model's ``config_machines.xml`` file.
The location of this file is model-dependent and is set by the ``MACHINES_SPEC_FILE`` entry in the model's ``config_files.xml`` (see :ref:`MACHINES_SPEC_FILE <model_config_machines>`); refer to your model repository for the exact path.
Please see the instructions in the file to create the directory structure and use these generic machine definitions.

.. _config-machines-schema-versions:

About config_machines.xml
---------------------------

The ``config_machines.xml`` file describes the machines on which CIME-driven models can be built and run.
Both its location and the XML schema(s) it must conform to are **model-dependent**.

The schema(s) advertised by a model are declared as ``<schema>`` children of the ``MACHINES_SPEC_FILE`` entry in that model's ``config_files.xml``.
The XSD applied at validation time is then selected from the ``version`` attribute on the root ``<config_machines>`` element of the file being loaded.
The two supported schemas are:

**Version 2.0 (monolithic)** — ``$CIMEROOT/CIME/data/config/xml_schemas/config_machines.xsd``
   A single file contains the full definition for every supported machine.
   Each ``<machine MACH="...">`` block carries its own ``<NODENAME_REGEX>`` (used by CIME to auto-detect the machine), and ``<machine>`` must appear at least once at the top level.

   .. code-block:: xml

      <config_machines version="2.0">
        <machine MACH="mymachine">
          <DESC>...</DESC>
          <NODENAME_REGEX>mymachine.*</NODENAME_REGEX>
          <OS>LINUX</OS>
          ...
        </machine>
        <machine MACH="othermachine">
          ...
        </machine>
      </config_machines>

**Version 3.0 (per-machine directory)** — ``$CIMEROOT/CIME/data/config/xml_schemas/config_machines_version3.xsd``
   The top-level ``config_machines.xml`` only holds a registry that maps each machine to its node-name regex.
   The full definition for each machine lives in its own subdirectory (``<machines_dir>/<MACH>/config_machines.xml``) next to that machine's ``config_batch.xml`` and ``*.cmake`` files.
   Top-level ``<machine>`` blocks are optional, ``<NODENAME_REGEX>`` is removed from individual ``<machine>`` blocks, and the v3 schema additionally accepts a ``<TORCH_DIR>`` element per machine.

   .. code-block:: xml

      <config_machines version="3.0">
        <NODENAME_REGEX>
          <value MACH="mymachine">mymachine.*</value>
          <value MACH="othermachine">other.*</value>
        </NODENAME_REGEX>
      </config_machines>

   Per-machine file (``<machines_dir>/mymachine/config_machines.xml``):

   .. code-block:: xml

      <config_machines version="3.0">
        <machine MACH="mymachine">
          <DESC>...</DESC>
          <OS>LINUX</OS>
          ...
        </machine>
      </config_machines>

Not every model registers both schemas. Refer to the ``MACHINES_SPEC_FILE`` entry in your model's ``config_files.xml`` to see which schema versions are available; if no ``version`` attribute is present on the ``<schema>`` entry, the model accepts a single unversioned schema matching the **2.0** layout.

See :ref:`MACHINES_SPEC_FILE <model_config_machines>` for the full element reference for both schema versions.

Steps for porting
---------------------------

Porting CIME involves several steps. The first step is to define your machine. You can do this in one of two ways:

1. You can edit the model's ``config_machines.xml`` directly (the path is given by ``MACHINES_SPEC_FILE`` in the model's ``config_files.xml``) and add an appropriate section for your machine.
   For a **version 3.0** layout, instead add (or update) a ``<value MACH="...">`` entry under the top-level ``<NODENAME_REGEX>`` and create a ``<machines_dir>/<your_machine>/`` subdirectory containing the per-machine ``config_machines.xml``, ``config_batch.xml`` and ``*.cmake`` files.

2. You can use your **$HOME/.cime** directory (see :ref:`customizing-cime`).
   In particular, you can create a **$HOME/.cime/config_machines.xml** file with the definition for your machine.
   A template to create this definition is provided in **$CIMEROOT/CIME/data/config/xml_schemas/config_machines_template.xml**. More details are provided in the template file.
   In addition, if you have a batch system, you will also need to add a **config_batch.xml** file to your **$HOME/.cime** directory.
   All files in **$HOME/.cime/** are appended to the xml objects that are read into memory from the directory containing the model's ``MACHINES_SPEC_FILE``.

   .. note:: When the model uses the **version 3.0** schema, the per-machine override is read from **$HOME/.cime/<your_machine>/config_machines.xml** (and a top-level **$HOME/.cime/config_machines.xml** may be used to register the ``NODENAME_REGEX``).

   .. note:: If you use method (2), you can download CIME updates without affecting your machine definitions in **$HOME/.cime**.

   .. note:: If you will be supporting many users on your new machine, then we recommend using method (1) and issuing a GitHub pull request with your machine updates.

In what follows we outline the process for method (2) above:

-  Create a **$HOME/.cime** directory and create a **config_machines.xml** file in that directory.

   This file contains all the information you must set in order to configure a new machine to be CIME-compliant.

   Fill in the contents of **$HOME/.cime/config_machines.xml** that are specific to your machine. For more details see :ref:`MACHINES_SPEC_FILE <model_config_machines>` and :ref:`the schema overview above <config-machines-schema-versions>`.

   Check to ensure that your **config_machines.xml** file conforms to the CIME schema definition by validating it against the XSD that matches the ``version`` declared on its root element:
   ::

      # version 2.0 (also used when the model registers only an unversioned schema)
      xmllint --noout --schema $CIMEROOT/CIME/data/config/xml_schemas/config_machines.xsd $HOME/.cime/config_machines.xml

      # version 3.0
      xmllint --noout --schema $CIMEROOT/CIME/data/config/xml_schemas/config_machines_version3.xsd $HOME/.cime/config_machines.xml

-  If you find that you need to introduce compiler settings specific to your machine, create a **$HOME/.cime/*.cmake** file.
   The default compiler settings are defined in the ``cmake_macros/`` directory that lives alongside the model's ``MACHINES_SPEC_FILE``.

-  If you have a batch system, you may also need to create a **$HOME/.cime/config_batch.xml** file.
   Out-of-the-box batch settings are set in the ``config_batch.xml`` file that lives alongside the model's ``MACHINES_SPEC_FILE`` (its path is given by ``BATCH_SPEC_FILE`` in the model's ``config_files.xml``).

-  Once you have defined a basic configuration for your machine in your **$HOME/.cime** xml files, run the :ref:`unittest <contributing-guide-running-tests>`.

After running those steps correctly, you are ready to try a case at your target compset and resolution.

Validating a port with prognostic components
-------------------------------------------------

.. note::

   This section is specific to CESM (and NorESM). Consult your model's documentation for the equivalent procedure.

The following port validation is recommended for any new machine.
Carrying out these steps does not guarantee the model is running
properly in all cases nor that the model is scientifically valid on
the new machine.

In addition to these tests, detailed validation should be carried out
for any new production run.  That means verifying that model restarts
are bit-for-bit identical with a baseline run, that the model is
bit-for-bit reproducible when identical cases are run for several
months, and that production cases are monitored carefully as they
integrate forward to identify any potential problems as early as
possible.

Users are responsible for their own validation process,
especially with respect to science validation.

These are the recommended steps for validating a port:

1. Verify basic functionality of your port by performing the "prealpha" tests on your machine. This can be done by issuing the following command:

   ::

      ./create_test --xml-category prealpha --xml-machine <reference_machine> --xml-compiler <reference_compiler> --machine <your_machine_name> --compiler <your_compiler_name>

   This command will run the prealpha tests *defined* for the reference machine with the reference compiler, but will run them on *your* machine with *your* compiler.
   These tests will be run in the **$CIME_OUTPUT_ROOT**. To see the results of tests, you need to do the following:

   ::

      > $CIME_OUTPUT_ROOT/cs.status.[testid]

   where testid was indicated in the output when calling `create_test <../Tools_user/create_test.html>`_

2. Carry out ensemble consistency tests:

   This is described in ``$CIMEROOT/tools/statistical_ensemble_test/README``.
   The Ensemble Consistency Test (ECT) determines whether a new simulation set up (new machine, compiler, etc.) is statistically distinguishable from an accepted ensemble.
   The ECT process involves comparing several runs (3) generated with the new scenario to an ensemble built on a trusted machine.
   The python ECT tools are located in the pyCECT subdirectory ``$CIMEROOT/tools/statistical_ensemble_test/pyCECT``.

   The verification tools in the ECT suite are:

   ``CAM-ECT``: detects issues in CAM and CLM (12 month runs)

   ``UF-CAM-ECT``: detects issues in CAM and CLM (9 time step runs)

   ``POP-ECT``: detects issues in POP and CICE (12 month runs)

   Follow the instructions in the **README** file to generate three ensemble runs for any of the above tests that are most relevant to your port.

Performance tuning of a port
-------------------------------------------------

Once you have performed the verification that your port is successful,
you will want to determine the optimal pe-layout for your target
configurations (i.e. compset/resolution combinations).  See the file
**$CIMEROOT/tools/load_balancing_tools/README** to understand how to
utilize the load balancing utilty. This utility finds reasonable PE
layouts for CIME-driven models. It will find these from timing files
you provide or from runs done by the tool.

Once you are happy with the PE-layout for your target configuration,
you can it to the relevant **config_pes.xml** file for the component
that is responsible for generating the PE-layout for the target
configuration (this is normally referred to as the "primary"
component).

Timing summaries for every successful case run, are located in the
case subdirectory **$CASEROOT/timing**. In addition, every
**cpl.log.timestamp** output file contains diagnostic timing
information. Search for ``tStamp`` in this file to see this
information. The timing information is useful for tracking down
temporal variability in model cost due to either inherent model
variability cost (I/O, spin-up, seasonal, and so on) or hardware.  The
model daily cost generally is pretty constant unless I/O is written
intermittently, such as at the end of the month.
