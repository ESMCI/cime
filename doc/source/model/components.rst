.. _components:

==========
Components
==========

A single component in the smallest unit within a model. Multiple components make up a component set.

Configuration
--------------

The configuration for a component can be found under `cime_config` in the component directory.

Example contents of a components `config_component.xml`.

::

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

::

  <entry id="REBUILD_TRIGGER_ATM">
    <type>char</type>
    <default_value>NTASKS,NTHREADS,NINST</default_value>
    <group>rebuild_triggers</group>
    <file>env_build.xml</file>
    <desc>Settings that will trigger a rebuild</desc>
  </entry>

If a user was to change `NTASKS`, `NTHREADS`, or `NINST` in a case using the component, then a rebuild would be required before the case could be submitted again.
