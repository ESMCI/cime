.. _model_config_inputdata:

Inputdata
===================

.. contents::
    :local:

Entry
-----

This is an example entry for ``config_files.xml``.

.. code-block:: xml

    <entry id="INPUTDATA_SPEC_FILE">
        <type>char</type>
        <default_value>$SRCROOT/cime_config/config_inputdata.xml</default_value>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing inputdata server descriptions  (for documentation only - DO NOT EDIT)</desc>
        <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_inputdata.xsd</schema>
    </entry>    

Definition
----------

Schema
``````        

.. code-block:: xml

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/config_inputdata.xsd inputdata on 2025-02-06 -->

    <!-- Occurences min: 1 max: 1-->
    <inputdata>
        <!-- Occurences min: 0 max: Unlimited-->
        <server>
            <!-- Occurences min: 0 max: 1-->
            <comment></comment>
            <!-- Occurences min: 1 max: 1-->
            <protocol></protocol>
            <!-- Occurences min: 1 max: 1-->
            <address></address>
            <!-- Occurences min: 0 max: 1-->
            <user></user>
            <!-- Occurences min: 0 max: 1-->
            <password></password>
            <!-- Occurences min: 0 max: 1-->
            <checksum></checksum>
            <!-- Occurences min: 0 max: 1-->
            <inventory></inventory>
            <!-- Occurences min: 0 max: 1-->
            <ic_filepath></ic_filepath>
        </server>
    </inputdata>