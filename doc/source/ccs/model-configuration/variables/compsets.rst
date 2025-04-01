.. _model_config_compsets:

COMPSETS_SPEC_FILE
==================

.. contents::
   :local:

Overview
--------
A compset is defined by multiple components, that are targeted to their model development needs.

Each component supports a set of compset longnames that are used in testing and supported in out of the box configurations.

To determined valid compset names CIME will look in ``config_files.xml`` for ``COMPSETS_SPEC_FILE`` in order to determine which components are defined by the compset.

Entry
-----
The following is an example for ``COMPSETS_SPEC_FILE`` in ``config_files.xml``.
Each ``value`` corresponds to the compsets provided by each component.

.. code-block:: xml

  <entry id="COMPSETS_SPEC_FILE">
    <type>char</type>
    <default_value>unset</default_value>
    <values>
      <value component="allactive">$SRCROOT/cime_config/allactive/config_compsets.xml</value>
      <value component="drv"      >$COMP_ROOT_DIR_CPL/cime_config/config_compsets.xml</value>
      <value component="eam"      >$COMP_ROOT_DIR_ATM/cime_config/config_compsets.xml</value>
      <value component="scream"   >$COMP_ROOT_DIR_ATM/cime_config/config_compsets.xml</value>
      <value component="elm"      >$COMP_ROOT_DIR_LND/cime_config/config_compsets.xml</value>
      <value component="cice"     >$COMP_ROOT_DIR_ICE/cime_config/config_compsets.xml</value>
      <value component="mpaso"    >$COMP_ROOT_DIR_OCN/cime_config/config_compsets.xml</value>
      <value component="mali"     >$COMP_ROOT_DIR_GLC/cime_config/config_compsets.xml</value>
      <value component="mpassi"   >$COMP_ROOT_DIR_ICE/cime_config/config_compsets.xml</value>
      <value component="mosart"   >$COMP_ROOT_DIR_ROF/cime_config/config_compsets.xml</value>
      <value component="ww3"      >$COMP_ROOT_DIR_WAV/cime_config/config_compsets.xml</value>
    </values>
    <group>case_last</group>
    <file>env_case.xml</file>
    <desc>file containing specification of all compsets for primary component (for documentation only - DO NOT EDIT)</desc>
    <schema>$CIMEROOT/CIME/data/config/xml_schemas/config_compsets.xsd</schema>
  </entry>


Every file listed in ``COMPSETS_SPEC_FILE`` will be searched to compile possible compsets to call ``create_newcase`` with.

CIME will note which component's config_compsets.xml had the matching compset name and that component will be treated as
the **primary component** As an example, the primary component for a compset that has a prognostic atmosphere,
land and cice (in prescribed mode) and a data ocean is the atmosphere component (for cesm this is CAM) because the compset
is defined, using the above example, in ``$SRCROOT/components/cam/cime_config/config_compsets.xml``
In a compset where all components are prognostic, the primary component will be **allactive**.

Definition
-----------

Schema
------

.. code-block:: xml

    <!-- Generated with doc/generate_xmlschema.py CIME/data/config/xml_schemas/config_compsets.xsd compsets on 2025-02-06 -->

    <!-- Attributes 'version' is required-->
    <!-- Occurences min: 1 max: 1-->
    <compsets version="">
        <!-- Occurences min: 1 max: 1-->
        <help></help>
        <!-- Occurences min: 1 max: Unlimited-->
        <compset>
            <!-- Occurences min: 1 max: 1-->
            <alias></alias>
            <!-- Occurences min: 1 max: 1-->
            <lname></lname>
            <!-- Attributes 'None' is None-->
            <!-- Occurences min: 0 max: Unlimited-->
            <science_support None="">
                <!-- Occurences min: 0 max: Unlimited-->
            </science_support>
        </compset>
        <!-- Occurences min: 0 max: 1-->
        <entries>
            <!-- Attributes 'id' is required-->
            <!-- Occurences min: 1 max: Unlimited-->
            <entry id="">
                <!-- Attributes 'match' is optional-->
                <!-- Occurences min: 1 max: 1-->
                <values match="">
                    <!-- Attributes 'compset' is optional,'grid' is optional-->
                    <!-- Occurences min: 1 max: Unlimited-->
                    <value compset="" grid=""></value>
                </values>
            </entry>
        </entries>

.. _defining-compsets:

Compset longname
-------------------

Each config_compsets.xml file has a list of allowed component sets in the form of a longname and an alias.

A compset longname has this form::

  TIME_ATM[%phys]_LND[%phys]_ICE[%phys]_OCN[%phys]_ROF[%phys]_GLC[%phys]_WAV[%phys]_ESP[_BGC%phys]

Supported values for each element of the longname::

  TIME = model time period (e.g. 1850, 2000, 20TR, SSP585...)

  CIME supports the following values for ATM,LND,ICE,OCN,ROF,GLC,WAV and ESP.
  ATM  = [DATM, SATM, XATM]
  LND  = [DLND, SLND, XLND]
  ICE  = [DICE, SICE, SICE]
  OCN  = [DOCN, SOCN, XOCN]
  ROF  = [DROF, SROF, XROF]
  GLC  = [SGLC, XGLC]
  WAV  = [SWAV, XWAV]
  ESP  = [SESP]

A CIME-driven model may have other options available.  Use `query_config  <../Tools_user/query_config.html>`_ to determine the available options.

The OPTIONAL %phys attributes specify sub-modes of the given system.
For example, DOCN%DOM is the DOCN data ocean (rather than slab-ocean) mode.
**All** the possible %phys choices for each component are listed by calling `query_config --compsets <../Tools_user/query_config.html>`_.
**All** data models have a %phys option that corresponds to the data model mode.

.. _creating-new-compsets:

Creating New Compsets
-----------------------

A description of how CIME interprets a compset name is given in the section :ref:`defining-compsets` .

To create a new compset, you will at a minimum have to:

1. edit the approprite ``config_components.xml`` file(s) to add your new requirements
2. edit associate ``namelist_definitions_xxx.xml`` in the associated ``cime_config`` directories.
   (e.g. if a change is made to the the ``config_components.xml`` for ``DOCN`` then ``namelist_definitions_docn.xml`` file will also need to be modified).

It is important to point out, that you will need expertise in the target component(s) you are trying to modify in order to add new compset functionality for that particular component.
We provide a few examples below that outline this process for a few simple cases.

Say you want to add a new mode, ``FOO``,  to the data ocean model, ``DOCN``. Lets call this mode, ``FOO``.
This would imply when parsing the compset longname, CIME would need to be able to recognize the string ``_DOCN%FOO_``.
To enable this, you will need to do the following:

.. note::

    The ``$DOCNROOT`` is depenedent on the model.

1. Edit ``$DOCNROOT/cime_config/config_component.xml`` (see the ``FOO`` additions below).
   * add an entry to the ``<description modifier_mode="1">`` block as shown below ::

       <description modifier_mode="1">
          <desc ocn="DOCN...[%FOO]">DOCN </desc>
          ...
          <desc option="FOO"> new  mode</desc>
          ....
       </description>

   * add an entry to the ``<entry id="DOCN_MODE">`` block as shown below::

       <entry id="DOCN_MODE">
          ....
          <values match="last">
          ....
          <value compset="_DOCN%FOO_" >prescribed</value>
          ...
       </entry>

   * modify any of the other xml entries that need a new dependence on ``FOO``

2. edit ``$DOCNROOT/cime_config/namelist_definition_docn.xml`` (see the ``FOO`` additions below).

   * add an entry to the ``datamode`` block as shown below. ::

       <entry id="datamode">
          ....
          <valid_values>...FOO</valid_values>
          ...
       </entry>

   * add additional changes to ``namelist_definition_docn.xml`` for the new mode


.. todo:: Add additional examples for creating a case
