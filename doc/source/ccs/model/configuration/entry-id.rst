.. _model_config_entry_id:

Entry ID
========

.. contents::
    :local:

The ``entry_id`` is a core element that is used throughout of CIME's model configuration.

Definition
----------

Schema
`````````

Version 3.0
:::::::::::::

.. code-block:: xml
    :tab-width: 4

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/entry_id_version3.xsd entry_id on 2025-02-06 -->

    <!-- Attributes 'version' is optional-->
    <!-- Occurences min: 1 max: 1-->
    <entry_id version="">
        <!-- Attributes 'modifier_mode' is optional-->
        <!-- Occurences min: 1 max: 1-->
        <description modifier_mode="">
            <!-- Attributes 'atm' is optional,'cpl' is optional,'ocn' is optional,'wav' is optional,'glc' is optional,'ice' is optional,'rof' is optional,'lnd' is optional,'iac' is optional,'esp' is optional,'forcing' is optional,'option' is optional-->
            <!-- Occurences min: 1 max: Unlimited-->
            <desc atm="" cpl="" ocn="" wav="" glc="" ice="" rof="" lnd="" iac="" esp="" forcing="" option="">
            </desc>
        </description>
        <!-- Attributes 'id' is required-->
        <!-- Occurences min: 1 max: Unlimited-->
        <entry id="">
            <!-- Occurences min: 1 max: 1-->
            <type></type>
            <!-- Occurences min: 1 max: 1-->
            <valid_values></valid_values>
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
            <!-- Attributes 'atm' is optional,'cpl' is optional,'ocn' is optional,'wav' is optional,'glc' is optional,'ice' is optional,'rof' is optional,'lnd' is optional,'iac' is optional,'esp' is optional,'forcing' is optional,'option' is optional-->
            <!-- Occurences min: 1 max: 1-->
            <desc atm="" cpl="" ocn="" wav="" glc="" ice="" rof="" lnd="" iac="" esp="" forcing="" option="">
            </desc>
            <!-- Occurences min: 0 max: 1-->
            <schema></schema>
        </entry>
        <!-- Occurences min: 0 max: 1-->
        <help></help>
    </entry_id>

Version 2.0
::::::::::::

.. code-block:: xml
    :tab-width: 4

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/entry_id.xsd entry_id on 2025-02-06 -->

    <!-- Attributes 'version' is optional-->
    <!-- Occurences min: 1 max: 1-->
    <entry_id version="">
        <!-- Attributes 'id' is required-->
        <!-- Occurences min: 1 max: Unlimited-->
        <entry id="">
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