.. _model-configuration-config-files:

Config Files
========================

.. contents::
    :local:

Overview
--------
The ``config_files.xml`` file is the main entrypoint for CIME to load a models configuration.

The contents define ``entry`` elements that describe various variables used to configure the model.

These varaibles defines supported compsets, components, grids, machines, batch queue, and compiler macros.

These ``config_files.xml`` are stored in ``$CIMEROOT/CIME/data/config/<model>/``.

.. note::

   The preferred method of adding a new model to CIME is to add a ``config_files.xml`` with a single entry; ``MODEL_CONFIG_FILES`` to the CIME repository.

   Using ``MODEL_CONFIG_FILES`` allows the models configuration to live outside the CIME repository.

Usage
-----
The entries in ``config_files.xml`` will describe the following variables. 

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


Schema Definition
-----------------

Version 3.0
:::::::::::
This version will reference another ``config_files.xml`` file that can be stored in the models repository.

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
