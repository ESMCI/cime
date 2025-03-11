.. _model_configuration:

Configuration
=============

.. contents::
    :local:

Entry ID
--------

The ``entry_id`` XML element is the basic building block of CIME's model configuration. The details can be found :ref:`here<model_config_entry_id>`.

Config Files
------------

The ``config_files.xml`` file is the main entrypoint for CIME to load a models configuration.

The configuration defines supported compsets, components, grids, machines, batch queue, and compiler settings.

These files are located at ``$CIMEROOT/CIME/data/config/<model>/config_files.xml``.

.. note::

   The preferred method of adding a new model to CIME is to add a ``config_files.xml`` with a single entry; ``MODEL_CONFIG_FILES`` to the CIME repository.

   Using ``MODEL_CONFIG_FILES`` allows the models configuration to live outside the CIME repository.

Example
```````

In this example the ``config_files.xml`` tells CIME it can find the models ``config_files.xml`` in the ``$SRCROOT`` (the models repository) under ``cime_config/``.

The ``config_files.xml`` in the models repository would be where all the :ref:`variables<mode_config_variables>` are stored.

.. code-block:: xml

   <?xml version="1.0"?>
   <?xml-stylesheet type="text/xsl" href="definitions_variables.xsl" ?>
   <entry_id version="3.0">
      <entry id="MODEL_CONFIG_FILES">
         <type>char</type>
         <default_value>$SRCROOT/cime_config/config_files.xml</default_value>
         <group>case_last</group>
         <file>env_case.xml</file>
         <desc>file containing paths</desc>
      </entry>
   </entry_id>

.. _mode_config_variables:
Variables
`````````

These variables should be defined in models ``config_files.xml`` to provide CIME with it's configuration.

* :ref:`ARCHIVE_SPEC_FILE<model_config_archive>`
* :ref:`BATCH_SPEC_FILE<model_config_batch>`
* :ref:`BUILD_LIB_FILE<model_config_build_lib>`
* :ref:`CASEFILE_HEADERS<model_config_casefile_headers>`
* :ref:`CMAKE_MACROS_DIR<model_config_cmake_macros_dir>`
* :ref:`COMPSETS_SPEC_FILE<model_config_compsets>`
* :ref:`COMP_ROOT_DIR_*<model_config_comp_root_dir>`
* :ref:`CONFIG_*_FILE<model_config_component>`
* :ref:`CONFIG_*_FILE_MODEL_SPECIFIC<model_config_component_model_specific>`
* :ref:`CONFIG_TESTS_FILE<model_config_tests>`
* :ref:`GRIDS_SPEC_FILE<model_config_grids>`
* :ref:`INPUTDATA_SPEC_FILE<model_config_inputdata>`
* :ref:`MACHINES_SPEC_FILE<model_config_machines>`
* :ref:`MODEL<model_config_model>`
* :ref:`NAMELIST_DEFINITION_FILE<model_config_namelist_definition>`
* :ref:`PES_SPEC_FILE<model_config_pes>`
* :ref:`PIO_SPEC_FILE<model_config_pio>`
* :ref:`SYSTEM_TESTS_DIR<model_config_system_tests>`
* :ref:`TESTS_MODS_DIR<model_config_tests_mods>`
* :ref:`TESTS_SPEC_FILE<model_config_tests_spec>`
* :ref:`USER_MODS_DIR<model_config_user_mods>`
* :ref:`WORKFLOW_SPEC_FILE<model_config_workflow>`

.. toctree::
   :maxdepth: 2
   :hidden:

   entry-id.rst
   archive.rst
   batch.rst
   build-lib.rst
   casefile-headers.rst
   cmake-macros-dir.rst
   compsets.rst
   comp-root-dir.rst
   component.rst
   component_model_specific.rst
   tests.rst
   grids.rst
   inputdata.rst
   machine.rst
   model.rst
   namelist-definition.rst
   pes.rst
   pio.rst
   system-tests.rst
   tests-mods.rst
   tests-spec.rst
   user-mods.rst
   workflow.rst
   