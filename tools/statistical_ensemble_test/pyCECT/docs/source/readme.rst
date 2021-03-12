
Overview
==============================

The Community Earth System Model Ensemble
Consistency Test (CESM-ECT or CECT) suite was developed as an
alternative to requiring bitwise identical output for quality
assurance. This objective test provides a statistical measurement
of consistency between an accepted ensemble created
by small initial temperature perturbations and a test set of
CESM simulations.

The pyCECT  package, or *python CESM Ensemble Consistency Test*
package contains the necessary tools to to compare the results of a set of new (modified)
CESM simulations against the accepted ensemble (pyCECT) as well as the tools to
create the ensemble summary files (pyEnsSum and pyEnsSumPop). These
three modules will be explained in more detail.

CESM/CIME notes:
---------------------
1. The pyCECT package is also included in CIME (Common Infrastructure for
    Modeling the Earth).  See:

    https://github.com/ESMCI/cime

2. Creating the ensemble summaries (via pyEnsSum and pyEnsSumPop) is
    typically done by the CESM software developers.  See: 

    http://www.cesm.ucar.edu/models/cesm2/python-tools/

3. A web-based interface to this tool is available here:

   http://www.cesm.ucar.edu/models/cesm2/verification/
    

Relevant publications:
----------------------

Daniel J. Milroy, Allison H. Baker, Dorit M. Hammerling, and Elizabeth R. Jessup, “Nine time steps: ultra-fast statistical consistency testing of the Community Earth System Model (pyCECT v3.0)”, Geoscientific Model Development, 11, pp. 697-711, 2018.
https://gmd.copernicus.org/articles/11/697/2018/

A.H. Baker, Y. Hu, D.M. Hammerling, Y. Tseng, X. Hu, X. Huang, F.O. Bryan, and G. Yang, “Evaluating Statistical Consistency in the Ocean Model Component of the Community Earth System Model (pyCECT v2.0).” Geoscientific Model Development, 9, pp. 2391-2406, 2016.
https://gmd.copernicus.org/articles/9/2391/2016/

A.H. Baker, D.M. Hammerling, M.N. Levy, H. Xu, J.M. Dennis, B.E. Eaton, J. Edwards, C. Hannay, S.A. Mickelson, R.B. Neale, D. Nychka, J. Shollenberger, J. Tribbia, M. Vertenstein, and D. Williamson, “A new ensemble-based consistency test for the community earth system model (pyCECT v1.0).” Geoscientific Model Development, 8, pp. 2829–2840, 2015.
https://gmd.copernicus.org/articles/8/2829/2015/
