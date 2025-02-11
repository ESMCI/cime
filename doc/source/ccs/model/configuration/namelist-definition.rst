.. _model_config_namelist_definition:

Namelist Definition
========================

.. contents::
    :local:

Provides CIME with the possible namelist options for a component.

Entry
-----

This is an example entry for ``config_files.xml``.

.. code-block:: xml

    <entry id="NAMELIST_DEFINITION_FILE">
        <type>char</type>
        <default_value>unset</default_value>
        <values>
            <value component="drv"     >$COMP_ROOT_DIR_CPL/cime_config/namelist_definition_drv.xml</value>
            <!-- data model components -->
            <value component="drof">$COMP_ROOT_DIR_ROF/cime_config/namelist_definition_drof.xml</value>
            <value component="datm">$COMP_ROOT_DIR_ATM/cime_config/namelist_definition_datm.xml</value>
            <value component="dice">$COMP_ROOT_DIR_ICE/cime_config/namelist_definition_dice.xml</value>
            <value component="dlnd">$COMP_ROOT_DIR_LND/cime_config/namelist_definition_dlnd.xml</value>
            <value component="docn">$COMP_ROOT_DIR_OCN/cime_config/namelist_definition_docn.xml</value>
            <value component="dwav">$COMP_ROOT_DIR_WAV/cime_config/namelist_definition_dwav.xml</value>
            <value component="desp">$COMP_ROOT_DIR_ESP/cime_config/namelist_definition_desp.xml</value>
            <!-- external model components -->
            <!--  TODO
            <value component="cam"      >$SRCROOT/components/cam/bld/namelist_files/namelist_definition.xml</value>
            <value component="cice"     >$SRCROOT/components/cice/cime_config/namelist_definition_cice.xml</value>
            <value component="clm"      >$SRCROOT/components/clm/bld/namelist_files/namelist_definition_clm4_5.xml</value>
            <value component="clm"      >$SRCROOT/components/clm/bld/namelist_files/namelist_definition_clm4_0.xml</value>
            -->
        </values>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing namelist_definitions for all components </desc>
        <schema>$CIMEROOT/CIME/data/config/xml_schemas/entry_id_namelist.xsd</schema>
    </entry>

Definition
----------

This is the contents of ``namelist_definition.xml``.

Schema
```````

.. code-block:: xml

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/entry_id_namelist.xsd entry_id on 2025-02-11 -->

    <!-- Attributes 'version' is optional-->
    <!-- Occurences min: 1 max: 1-->
    <entry_id version="">
        <!-- Attributes 'id' is required,'modify_via_xml' is optional,'skip_default_entry' is optional,'per_stream_entry' is optional-->
        <!-- Occurences min: 1 max: Unlimited-->
        <entry id="" modify_via_xml="" skip_default_entry="" per_stream_entry="">
            <!-- Occurences min: 1 max: 1-->
            <type></type>
            <!-- Attributes 'None' is None-->
            <!-- Occurences min: 1 max: 1-->
            <valid_values None=""></valid_values>
            <!-- Occurences min: 1 max: 1-->
            <default_value></default_value>
            <!-- Occurences min: 1 max: 1-->
            <file></file>
            <!-- Occurences min: 1 max: 1-->
            <group></group>
            <!-- Attributes 'modifier' is optional,'match' is optional-->
            <!-- Occurences min: 1 max: 1-->
            <values modifier="" match="">
                <!-- Attributes 'None' is None-->
                <!-- Occurences min: 1 max: Unlimited-->
                <value None=""></value>
            </values>
            <!-- Attributes 'compset' is optional-->
            <!-- Occurences min: 1 max: 1-->
            <desc compset="">
            </desc>
            <!-- Occurences min: 1 max: 1-->
            <category></category>
            <!-- Occurences min: 1 max: 1-->
            <input_pathname></input_pathname>
            <!-- Attributes 'version' is optional-->
            <!-- Occurences min: 0 max: 1-->
            <schema version="">
            </schema>
        </entry>
        <!-- Occurences min: 0 max: 1-->
        <description>
            <!-- Attributes 'compset' is optional-->
            <!-- Occurences min: 1 max: Unlimited-->
            <desc compset="">
            </desc>
        </description>
        <!-- Occurences min: 0 max: 1-->
        <help></help>
    </entry_id>