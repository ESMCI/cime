.. _model_config_compilers:

Compilers
===================

.. contents::
    :local:

.. warning::

    This has been deprecated in favor of :ref:`cmake macros<model_config_cmake_macros_dir>`.

Entry
-----

This is an example entry for ``config_files.xml``.

.. code-block:: xml

    <entry id="COMPILERS_SPEC_FILE">
        <type>char</type>
        <default_value>$SRCROOT/cime_config/machines/config_compilers.xml</default_value>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing compiler specifications for target model primary component (for documentation only - DO NOT EDIT)</desc>
        <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_compilers_v2.xsd</schema>
    </entry>

.. _compilerfile:

Configuration
-------------------------------------------------
The **config_compilers.xml** file defines compiler flags for building CIME (and also CESM and E3SM prognostic CIME-driven components).

#. General compiler flags (e.g., for the gnu compiler) that are machine- and componen-independent are listed first.

#. Compiler flags specific to a particular operating system are listed next.

#. Compiler flags that are specific to particular machines are listed next.

#. Compiler flags that are specific to particular CIME-driven components are listed last.

The order of listing is a convention and not a requirement.

The possible elements and attributes that can exist in the file are documented in **$CIME/config/xml_schemas/config_compilers_v2.xsd**.

To clarify several conventions:

- The ``<append>`` element implies that any previous definition of that element's parent will be appended with the new element value.
  As an example, the following entry in **config_compilers.xml** would append the value of ``CPPDEFS`` with ``-D $OS`` where ``$OS`` is the environment value of ``OS``.

  ::

     <compiler>
        <CPPDEFS>
            <append> -D<env>OS</env> </append>
        </CPPDEFS>
     </compiler>

- The ``<base>`` element overwrites its parent element's value. For example, the following entry would overwrite the ``CONFIG_ARGS`` for machine ``melvin`` with a ``gnu`` compiler to be ``--host=Linux``.

  ::

     <compiler MACH="melvin" COMPILER="gnu">
        <CONFIG_ARGS>
           <base> --host=Linux </base>
        </CONFIG_ARGS>
     </compiler>
