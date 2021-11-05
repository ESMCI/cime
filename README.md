# cime
Common Infrastructure for Modeling the Earth

CIME, pronounced "SEAM", primarily consists of a Case Control System that supports the configuration, compilation, execution, system testing and unit testing of an Earth System Model. The two main components of the Case Control System are:

1. Scripts to enable simple generation of model executables and associated input files for different scientific cases, component resolutions and combinations of full, data and stub components with a handful of commands.
2. Testing utilities to run defined system tests and report results for different configurations of the coupled system.

CIME does **not** contain the source code for any Earth System Model drivers or components. It is typically included alongside the source code of a host model. However, CIME does include pointers to external repositories that contain drivers, data models and other test components. These external components can be easily assembled to facilitate end-to-end system tests of the CIME infrastructure, which are defined in the CIME repository.

CIME is currently used by the
<a href="http://www2.cesm.ucar.edu">Community Earth System Model </a>
     (CESM) and the <a href="https://climatemodeling.science.energy.gov/projects/energy-exascale-earth-system-model">
Energy Exascale Earth System Model</a> (E3SM).

# Documentation

See <a href="http://esmci.github.io/cime">esmci.github.io/cime</a>

# Developers

## Lead Developers
Jim Edwards (NCAR), Jim Foucar (SNL)

## Also Developed by
Alice Bertini (NCAR), Jason Boutte (LLNL), Tony Craig (NCAR), Michael Deakin (SNL), Chris Fischer (NCAR), Erich Foster (SNL), Steve Goldhaber (NCAR), Robert Jacob (ANL), Mike Levy (NCAR), Bill Sacks (NCAR), Andrew Salinger (SNL), Sean Santos (NCAR), Jason Sarich (ANL), Mariana Vertenstein (NCAR), Andreas Wilke (ANL).

# Acknowledgements

CIME is jointly developed with support from the Earth System Modeling program of DOE's BER office and the CESM program
of NSF's Division of Atmospheric and Geospace Sciences.

# License

CIME is free software made available under the BSD License. For details see the LICENSE file.

# Digital Object Identifier

DOI:[10.5065/WE0D-9K91](http://dx.doi.org/10.5065/WE0D-9K91)
