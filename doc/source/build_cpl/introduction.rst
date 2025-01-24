Introduction
============

Content to go here:

How to add a new component model to cime.
The cime to a component model is expected to be found in directory components/model/cime_config.  Each component will have xml file config_component.xml and will optionally have xml files config_compsets.xml, config_archive.xml, config_pes.xml, config_tests.xml.   It will have python interface scripts buildlib which provides the component build instructions and buildnml which will create the input arguments to the component model - there is also a file user_nl_xxx (where xxx is the component name) which allows the user to override input defaults on a case by case basis.  The cime_config directory may also have subdirectories SystemTests and testdefs which describe CIME based tests that are unique to the component model.  

How to replace an existing cime model with another one.
  
How to integrate your model in to the cime build/configure system and coupler.

How to work with the CIME-supplied models.

What to do if you want to add another component to the long name.
