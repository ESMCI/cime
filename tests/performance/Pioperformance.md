# Using pioperf to Measure Performance

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

## Testing

For the automated test you can generate a decomp internally by setting
decompfile="ROUNDROBIN", or decompfile="BLOCK"

They call init_ideal_dof which internally generates a dof as follows:

    if(doftype .eq. 'ROUNDROBIN') then                                          
       do i=1,varsize                                                           
          compmap(i) = (i-1)*npe+mype+1                                         
       enddo                                                                    
    else if(doftype .eq. 'BLOCK') then                                          
       do i=1,varsize                                                           
          compmap(i) =  (i+varsize*mype)                                        
       enddo                                                                    
    endif
    
The size of the variable is npes*varsize where varsize can be set in
the namelist.

