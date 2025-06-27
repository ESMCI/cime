.. _model_config_component:

CONFIG_*_FILE
=============

.. contents::
  :local:

Overview
--------
This variables defines the configuration XML for each component.

Entry
-----
The following is an example entry for ``CONFIG_<component>_FILE`` in ``config_files.xml``.
The ``<component>`` is replaced by the name of the component.
There will be multiple ``entry`` elements, one for each component supported by the model.

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

Schema Definition
-----------------

The configuration is stored in ``config_component.xml`` under the components ``cime_config`` directory e.g. ``mosart/cime_config/config_component.xml``.
This file will store multiple variables for the component defined using :ref:`*entry*<model-configuration-entry>` elements.
Example contents of ``config_component.xml``.

=================== ==================================
Element/Attribute   Description
=================== ==================================
desc                Description for the component.
entry               XML variable entries.
help                Help text for the component.
=================== ==================================

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