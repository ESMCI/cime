.. _model_config_component_model_specific:

Component Model Specific
==============================

.. contents::
    :local:

Provides CIME with model specific component settings.

Entry
-----

This is an example entry for ``config_files.xml``.

.. code-block:: xml

    <entry id="CONFIG_CPL_FILE_MODEL_SPECIFIC">
        <type>char</type>
        <values>
            <value>$SRCROOT/driver-$COMP_INTERFACE/cime_config/config_component_$MODEL.xml</value>
        </values>
        <group>case_last</group>
        <file>env_case.xml</file>
        <desc>file containing all component specific driver configuration variables (for documentation only - DO NOT EDIT)</desc>
        <schema version="2.0">$CIMEROOT/CIME/data/config/xml_schemas/entry_id.xsd</schema>
        <schema version="3.0">$CIMEROOT/CIME/data/config/xml_schemas/entry_id_version3.xsd</schema>
    </entry>


.. _defining-component-specific-compset-settings:

Component specific settings in a compset
-----------------------------------------

Every model component also contains a **config_component.xml** file that has two functions:

1. Specifying the component-specific definitions of what can appear after the ``%`` in the compset longname, (for example, ``DOM`` in ``DOCN%DOM``).

2. Specifying the compset-specific ``$CASEROOT`` xml variables.

.. _xml_schema_component_model:

CIME first parses the following nodes to identify appropriate **config_component.xml** files for the driver. There are two such files; one is model-independent and the other is model-specific.
::

   <entry id="CONFIG_CPL_FILE">
      ...
      <default_value>$CIMEROOT/driver_cpl/cime_config/config_component.xml</default_value>
      ..
      </entry>

     <entry id="CONFIG_CPL_FILE_MODEL_SPECIFIC">
        <default_value>$CIMEROOT/driver_cpl/cime_config/config_component_$MODEL.xml</default_value>
     </entry>

CIME then parses each of the nodes listed below, using using the value of the *component* attribute to determine which xml files to use for the requested compset longname.
::

     <entry id="CONFIG_ATM_FILE">
     <entry id="CONFIG_ESP_FILE">
     <entry id="CONFIG_ICE_FILE">
     <entry id="CONFIG_GLC_FILE">
     <entry id="CONFIG_LND_FILE">
     <entry id="CONFIG_OCN_FILE">
     <entry id="CONFIG_ROF_FILE">
     <entry id="CONFIG_WAV_FILE">

As an example, the possible atmosphere components for CESM have the following associated xml files.
::

     <entry id="CONFIG_ATM_FILE">
       <type>char</type>
       <default_value>unset</default_value>
       <values>
         <value component="cam" >$SRCROOT/components/cam/cime_config/config_component.xml</value>
         <value component="datm">$CIMEROOT/components/data_comps/datm/cime_config/config_component.xml</value>
         <value component="satm">$CIMEROOT/components/stub_comps/satm/cime_config/config_component.xml</value>
         <value component="xatm">$CIMEROOT/components/xcpl_comps/xatm/cime_config/config_component.xml</value>
       </values>
       <group>case_last</group>
       <file>env_case.xml</file>
       <desc>file containing specification of component specific definitions and values(for documentation only - DO NOT EDIT)</desc>
       <schema>$CIMEROOT/cime_config/xml_schemas/entry_id.xsd</schema>
     </entry>

If the compset's atm component attribute is ``datm``, the file ``$CIMEROOT/components/data_comps/datm/cime_config/config_component.xml`` specifies all possible component settings for ``DATM``.

The schema for every **config_component.xml** file has a ``<description>`` node that specifies all possible values that can follow the ``%`` character in the compset name.

To list the possible values, use the `query_config --component datm <../Tools_user/query_config.html>`_ command.