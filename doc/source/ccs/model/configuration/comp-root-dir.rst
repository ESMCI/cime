.. _model_config_comp_root_dir:

Component Root Directory
========================

.. contents::
    :local:

Provides CIME with the paths to the root directories for each supported component.

Entry
-----

This is an example entry for ``config_files.xml``.

For each component a model supports, CIME expects to find a variable entry in the form of ``COMP_ROOT_DIR_<component>``.

Where ``<component>`` is replaced by one of the following.

* CPL
* ATM
* LND
* ROF
* ICE
* OCN
* WAV
* GLC
* IAC
* ESP

Each of these ``value`` entries will provide the root directory for the component.

Example
-------

In this example the atmospheric model (``COMP_ROOT_DIR_ATM``) provides a few different components.

.. code-block:: xml

    <entry id="COMP_ROOT_DIR_ATM">
        <type>char</type>
        <values>
        <value component="datm"                        >$SRCROOT/components/data_comps/datm</value>
        <value component="satm"                        >$SRCROOT/components/stub_comps/satm</value>
        <value component="xatm"                        >$SRCROOT/components/xcpl_comps/xatm</value>
        <value component="eam"                         >$SRCROOT/components/eam/</value>
        <value component="eamxx"                       >$SRCROOT/components/eamxx/</value>
        <value component="scream"                      >$SRCROOT/components/eamxx/</value>
        </values>
        <group>case_comps</group>
        <file>env_case.xml</file>
        <desc>Root directory of the case atmospheric component  </desc>
        <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_compsets.xsd</schema>
    </entry>