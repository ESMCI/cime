.. _model_config_component:

Component
=============

.. contents::
  :local:

A single component in the smallest unit within a model. Multiple components make up a compset.

Entry
-----

This is an example entry for ``config_files.xml``.

There should be an entry for each component supported by the model, e.g. CONFIG_ATM_FILE, CONFIG_CPL_FILE, CONFIG_LND_FILE, etc.

.. code-block:: xml

    <entry id="CONFIG_ATM_FILE">
        <type>char</type>
        <values>
            <value>$COMP_ROOT_DIR_ATM/cime_config/config_component.xml</value>
        </values>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing specification of component specific definitions and values(for documentation only - DO NOT EDIT)</desc>
        <schema version="2.0">$CIMEROOT/CIME/data/config/xml_schemas/entry_id.xsd</schema>
        <schema version="3.0">$CIMEROOT/CIME/data/config/xml_schemas/entry_id_version3.xsd</schema>
    </entry>

Definition
----------

The configuration is stored in ``config_component.xml`` under the components ``cime_config`` directory e.g. ``mosart/cime_config/config_component.xml``.
This file will store multiple variables for the component defined using :ref:`*entry*<model_config_entry_id>` elements.
Example contents of ``config_component.xml``.

.. code-block:: xml

    <?xml version="1.0"?>
    <?xml-stylesheet type="text/xsl" href="entry_id.xsl" ?>

    <entry_id version="3.0">
        <description>
            <desc atm="SATM">Stub atm component</desc>
        </description>

        <entry id="COMP_ATM">
            <type>char</type>
            <valid_values>satm</valid_values>
            <default_value>satm</default_value>
            <group>case_comp</group>
            <file>env_case.xml</file>
            <desc>Name of atmosphere component</desc>
        </entry>

        <help>
        =========================================
        SATM naming conventions in compset name
        =========================================
        </help>
    </entry_id>

Triggering a rebuild
--------------------

It's the responsibility of a component to define which settings will require a component to be rebuilt.

These triggers can be defined as follows.

.. code-block:: xml

    <entry id="REBUILD_TRIGGER_ATM">
        <type>char</type>
        <default_value>NTASKS,NTHREADS,NINST</default_value>
        <group>rebuild_triggers</group>
        <file>env_build.xml</file>
        <desc>Settings that will trigger a rebuild</desc>
    </entry>

If a user was to change `NTASKS`, `NTHREADS`, or `NINST` in a case using the component, then a rebuild would be required before the case could be submitted again.