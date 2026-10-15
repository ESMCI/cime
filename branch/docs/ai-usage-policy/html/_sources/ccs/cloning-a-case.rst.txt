.. _ccs_cloning_a_case:

Cloning a Case
==============

.. contents::
    :local:

If you have access to a run that you want to clone, the
``create_clone`` command will create a new case and run ``case.setup``
while preserving local modifications to the case.

To clone a case, you can use the following command, replacing ``<case>`` with the new case directory and ``<clone>`` with the directory of the case you want to clone.

.. code-block:: bash

    ./scripts/create_clone --case <case> --clone <clone>

Now the new cloned case can be built and submitted.

.. code-block:: bash

    cd <case>
    ./case.build
    ./case.submit

The ``create_clone`` script preserves any local namelist modifications
made in the **user_nl_xxxx** files as well as any source code
modifications in the **SourceMods/** directory tree. Otherwise, your **$CASEROOT** directory
will appear as if ``create_newcase`` had just been run.

.. danger::

    Do not change anything in the ``env_case.xml`` file.

The ``create_clone`` has several useful optional arguments. To point to
the executable of the original case you are cloning from.

::

     ./scripts/create_clone --case <case> --clone <clone> --keepexe
     cd $CASEROOT
     ./case.submit

If the ``--keepexe`` optional argument is used, then no SourceMods
will be permitted in the cloned directory. A link will be made when
the cloned case is created pointing the cloned SourceMods/ directory
to the original case SourceMods directory.

.. warning:: 

    No changes should be made to ``env_build.xml`` or ``env_mach_pes.xml`` in the cloned directory.

The ``create_clone`` also permits you to invoke the ``shell_commands``
and ``user_nl_xxx`` files in a user_mods directory by calling:

::

    ./scripts/create_clone --case <case> --clone <clone> --user-mods-dir USER_MODS_DIR [--keepexe]

Note that an optional ``--keepexe`` flag can also be used in this case.

.. warning:: 

    If there is a ``shell_commands`` file, it should not have any changes to XML variables in either ``env_build.xml`` or ``env_mach_pes.xml``.

Another approach to duplicating a case is to use the information in
the case's **README.case** and **CaseStatus** files to create a new
case and duplicate the relevant ``xmlchange`` commands that were
issued in the original case. This alternative will *not* preserve any
local modifications that were made to the original case, such as
source-code or build-script revisions; you will need to import those
changes manually.
