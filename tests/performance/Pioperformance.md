To run pioperformance you need a dof input file. I have a whole repo
of them here:
https://svn-ccsm-piodecomps.cgd.ucar.edu/trunk

You need an input namelist:

&pioperf
decompfile=   '/gpfs/fs1/work/jedwards/sandboxes/piodecomps/576/piodecomp576tasks03dims01.dat',
 pio_typenames = 'pnetcdf'
 rearrangers = 1,2
 nframes = 1
 nvars = 1
 niotasks = 64, 32, 16
 /

in the namelist all of the inputs are arrays and it will test all
combinations of the inputs.  You need to run it on the number of tasks
specified by the input dof There are also some options to use simple
generated dof's instead of files.

