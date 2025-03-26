.. _model_configuration:

Variables
=============

.. contents::
  :local:

Overview
--------
Variables are defined using an ``entry`` element. The ``id`` attribute will contain the variable name.

Schema Definition
-----------------

.. list-table:: Variable Elements
    :header-rows: 1

    * - Element
      - Required
      - Description
    * - type
      - Yes
      - The type of the variable. The type can be one of the following: ``char``, ``integer``, ``logical``, or ``real``.
    * - values
      - No
      - This element can contain multiple ``value`` elements. This is used to provide multiple values depending on the component.
    * - default_value
      - No
      - Used to define a single value for the variable.
    * - group
      - No
      - Used to group variables together.
    * - file
      - Yes
      - The file the variable should be stored in.
    * - desc
      - No
      - A description of the variable.
    * - schema
      - No
      - Path to a schema file that will be used to validate the contents of the variable value.

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
---------

.. toctree::
   :maxdepth: 1

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