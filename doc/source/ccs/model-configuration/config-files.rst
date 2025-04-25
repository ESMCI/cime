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
Then ``entry`` elements in ``config_files.xml`` are used to describe the variables that make up CIME's model configuration.

The XML schema for ``entry`` is as follows.

================= =======================================================
Element           Description
================= =======================================================
type              The type of the variable. The type can be one of the following: ``char``, ``integer``, ``logical``, or ``real``.
values            This element can contain multiple ``value`` elements. This is used to provide multiple values depending on the component.
default_value     Used to define a single value for the variable.
group             Used to group variables together.
file              The file the variable should be stored in.
desc              A description of the variable.
schema            Path to a schema file that will be used to validate the contents of the variable value.
================= =======================================================

.. code-block::

    <entry id="">
         <type>char</type>
         <values>
                  <value></value>
                  <value component=""></value>
         </values>
         <default_value></default_value>
         <group></group>
         <file></file>
         <desc></desc>
         <schema></schema>
    </entry>

Variables
:::::::::
These variables will define values or reference additional files to make up a models configuration.

.. toctree::
   :maxdepth: 1

   variables/archive.rst
   variables/batch.rst
   variables/build-lib.rst
   variables/casefile-headers.rst
   variables/cmake-macros-dir.rst
   variables/compsets.rst
   variables/comp-root-dir.rst
   variables/component.rst
   variables/component_model_specific.rst
   variables/tests.rst
   variables/grids.rst
   variables/inputdata.rst
   variables/machine.rst
   variables/model.rst
   variables/namelist-definition.rst
   variables/pes.rst
   variables/pio.rst
   variables/system-tests.rst
   variables/tests-mods.rst
   variables/tests-spec.rst
   variables/user-mods.rst
   variables/workflow.rst

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
