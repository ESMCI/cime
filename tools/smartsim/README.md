Running CESM with the CrayLabs SmartSim tool.  https://github.com/CrayLabs/SmartSim

The tools provided here can be used with PBS version 2021 or newer.
PBS must support the create_resv_from_job option and the user must be
enabled to use that option.  

It allows you to submit multiple jobs to the queue and
assure that all of the jobs will start and run concurrently.  

If --ngpus-per-node > 0 then the SmartSim database will be submitted
to gpu nodes while the CESM case(s) will run on cpu nodes.  

See also:
https://github.com/ESCOMP/CESM/wiki/Using-HPE-SmartSim-with-CESM

The smartredis https://github.com/CrayLabs/SmartRedis interface is built in share
and available to all components.  If USE_SMARTSIM is false then a stub library is built
so that no cpp ifdefs are required. 

