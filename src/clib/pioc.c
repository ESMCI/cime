/**
 * @file
 * Some initialization and support functions.
 * @author Jim Edwards
 * @date  2014
 *
 * @see http://code.google.com/p/parallelio/
 */

#include <config.h>
#include <pio.h>
#include <pio_internal.h>

static int counter = 0;

/**
 * Check to see if PIO has been initialized.
 *
 * @param iosysid the IO system ID
 * @param active pointer that gets true if IO system is active, false
 * otherwise.
 * @returns 0 on success, error code otherwise
 */
int PIOc_iosystem_is_active(int iosysid, bool *active)
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    if (active)
        if (ios->comp_comm == MPI_COMM_NULL && ios->io_comm == MPI_COMM_NULL)
            *active = false;
        else
            *active = true;

    return PIO_NOERR;
}

/**
 * Check to see if PIO file is open.
 *
 * @param ncid the ncid of an open file
 * @returns 1 if file is open, 0 otherwise.
 */
int PIOc_File_is_Open(int ncid)
{
    file_desc_t *file;

    /* If get file returns non-zero, then this file is not open. */
    if (pio_get_file(ncid, &file))
        return 0;
    else
        return 1;
}

/**
 * Set the error handling method to be used for subsequent pio library
 * calls, returns the previous method setting. This function is
 * supported but deprecated. New code should use
 * PIOc_set_file_error_handling().  This method has no way to return
 * an error, so any failure will result in MPI_Abort.
 *
 * @param ncid the ncid of an open file
 * @param method the error handling method
 * @returns old error handler
 * @ingroup PIO_error_method
 */
int PIOc_Set_File_Error_Handling(int ncid, int method)
{
    file_desc_t *file;
    int oldmethod;
    int ret;

    /* Get the file info. */
    if (pio_get_file(ncid, &file))
        piodie("Could not find file", __FILE__, __LINE__);                

    /* Get the old method. */
    oldmethod = file->iosystem->error_handler;

    /* Set the file error handler. */
    if (PIOc_set_file_error_handling(ncid, method, &oldmethod))
        piodie("Could not set the file error hanlder", __FILE__, __LINE__);        

    return oldmethod;
}

/**
 * Set the error handling method to be used for subsequent pio
 * library calls on this file.
 *
 * @param ncid the ncid of an open file
 * @param method the error handling method
 * @param old_method pointer to int that will get old method. Ignored if NULL.
 * @returns 0 for success, error code otherwise.
 * @ingroup PIO_error_method
 */
int PIOc_set_file_error_handling(int ncid, int method, int *old_method)
{
    file_desc_t *file;
    int ret;

    LOG((1, "PIOc_set_file_error_handling ncid = %d method = %d", ncid, method));

    /* Find info for this file. */
    if ((ret = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ret, __FILE__, __LINE__);

    /* Check that valid error handler was provided. */
    if (method != PIO_INTERNAL_ERROR && method != PIO_BCAST_ERROR &&
        method != PIO_RETURN_ERROR)
        return pio_err(file->iosystem, file, PIO_EINVAL, __FILE__, __LINE__);

    /* Return the current handler. */
    if (old_method)
        *old_method = file->error_handler;

    /* Set the error hanlder. */
    file->error_handler = method;
    
    return PIO_NOERR;
}

/**
 * Increment the unlimited dimension of the given variable.
 *
 * @param ncid the ncid of the open file
 * @param varid the variable ID
 * @returns 0 on success, error code otherwise
 */
int PIOc_advanceframe(int ncid, int varid)
{
    file_desc_t *file;
    int ret;

    /* Get the file info. */
    if ((ret = pio_get_file(ncid, &file)))
        return ret;

    file->varlist[varid].record++;

    return(PIO_NOERR);
}

/**
 * Set the unlimited dimension of the given variable
 *
 * @param ncid the ncid of the file.
 * @param varid the varid of the variable
 * @param frame the value of the unlimited dimension.  In c 0 for the
 * first record, 1 for the second
 * @return PIO_NOERR for no error, or error code.
 * @ingroup PIO_setframe
 */
int PIOc_setframe(int ncid, int varid, int frame)
{
    file_desc_t *file;
    int ret;

    /* Get file info. */
    if ((ret = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ret, __FILE__, __LINE__);

    /* Check inputs. */
    if (varid < 0 || varid >= PIO_MAX_VARS)
        return pio_err(NULL, file, PIO_EINVAL, __FILE__, __LINE__);

    file->varlist[varid].record = frame;

    return PIO_NOERR;
}

/**
 * Get the number of IO tasks set.
 *
 * @param iosysid the IO system ID
 * @param numiotasks a pointer taht gets the number of IO
 * tasks. Ignored if NULL.
 * @returns 0 on success, error code otherwise
 */
int PIOc_get_numiotasks(int iosysid, int *numiotasks)
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

    if (numiotasks)
        *numiotasks = ios->num_iotasks;

    return PIO_NOERR;
}

/**
 * Get the IO rank on the current task.
 *
 * @param iosysid the IO system ID
 * @param iorank a pointer that gets the IO rank of the current task,
 * or -1 if it is not an IO task. Ignored if NULL.
 * @returns 0 on success, error code otherwise
 */
int PIOc_get_iorank(int iosysid, int *iorank)
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

    if (iorank)
        *iorank = ios->io_rank;

    return PIO_NOERR;
}

/**
 * Get the local size of the variable.
 *
 * @param ioid
 * @returns 0 on success, error code otherwise
 */
int PIOc_get_local_array_size(int ioid)
{
    io_desc_t *iodesc;

    iodesc = pio_get_iodesc_from_id(ioid);

    return iodesc->ndof;
}

/**
 * Set the error handling method used for subsequent calls. This
 * function is deprecated. New code should use
 * PIOc_set_iosystem_error_handling(). This method has no way to
 * return an error, so any failure will result in MPI_Abort.
 *
 * @param iosysid the IO system ID
 * @param method the error handling method
 * @returns old error handler
 * @ingroup PIO_error_method
 */
int PIOc_Set_IOSystem_Error_Handling(int iosysid, int method)
{
    iosystem_desc_t *ios;
    int oldmethod;
    int ret;

    /* Get the iosystem info. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))    
        piodie("Could not get the IOSystem", __FILE__, __LINE__);

    /* Remember old method setting. */
    oldmethod = ios->error_handler;

    /* Set the file error handler. */
    if (PIOc_set_iosystem_error_handling(iosysid, method, &oldmethod))
        piodie("Could not set the IOSystem error hanlder", __FILE__, __LINE__);

    return oldmethod;
}

/**
 * Set the error handling method used for subsequent calls for this IO
 * system. This may be overridden for individual files by
 * PIOc_set_file_error_handling().
 *
 * @param iosysid the IO system ID
 * @param method the error handling method
 * @param old_method pointer to int that will get old method. Ignored if NULL.
 * @returns 0 for success, error code otherwise.
 * @ingroup PIO_error_method
 */
int PIOc_set_iosystem_error_handling(int iosysid, int method, int *old_method)
{
    iosystem_desc_t *ios;

    LOG((1, "PIOc_set_iosystem_error_handling iosysid = %d method = %d", iosysid, method));

    /* Find info about this iosystem. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* Check that valid error handler was provided. */
    if (method != PIO_INTERNAL_ERROR && method != PIO_BCAST_ERROR &&
        method != PIO_RETURN_ERROR)
        return pio_err(ios, NULL, PIO_EINVAL, __FILE__, __LINE__);

    /* Return the current handler. */
    if (old_method)
        *old_method = ios->error_handler;

    /* Set new error handler. */
    ios->error_handler = method;

    return PIO_NOERR;
}

/**
 * Initialize the decomposition used with distributed arrays. The
 * decomposition describes how the data will be distributed between
 * tasks.
 *
 * @param iosysid the IO system ID.
 * @param basetype the basic PIO data type used.
 * @param ndims the number of dimensions in the variable.
 * @param dims an array of global size of each dimension.
 * @param maplen the local length of the compmap array.
 * @param compmap a 1 based array of offsets into the array record on
 * file. A 0 in this array indicates a value which should not be
 * transfered.
 * @param ioidp pointer that will get the io description ID.
 * @param rearranger pointer to the rearranger to be used for this
 * decomp or NULL to use the default.
 * @param iostart An array of start values for block cyclic
 * decompositions. If NULL ???
 * @param iocount An array of count values for block cyclic
 * decompositions. If NULL ???
 * @returns 0 on success, error code otherwise
 * @ingroup PIO_initdecomp
 */
int PIOc_InitDecomp(int iosysid, int basetype, int ndims, const int *dims, int maplen,
                    const PIO_Offset *compmap, int *ioidp, const int *rearranger,
                    const PIO_Offset *iostart, const PIO_Offset *iocount)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    io_desc_t *iodesc;     /* The IO description. */
    int mpierr;            /* Return code from MPI calls. */
    int ierr;              /* Return code. */

    LOG((1, "PIOc_InitDecomp iosysid = %d basetype = %d ndims = %d maplen = %d",
         iosysid, basetype, ndims, maplen));

    /* Check the dim lengths. */
    for (int i = 0; i < ndims; i++)
        if (dims[i] <= 0)
            piodie("Invalid dims argument", __FILE__, __LINE__);

    /* Get IO system info. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

    /* If desired, save the computed decompositions to
     * files. PIO_Save_Decomps is a global var set in
     * pioc_support.c. This used to be set by environment variable and
     * needs to be settable for debug purposes. */
    if (PIO_Save_Decomps)
    {
        char filename[NC_MAX_NAME];
        if (ios->num_comptasks < 100)
            sprintf(filename, "piodecomp%2.2dtasks%2.2ddims%2.2d.dat", ios->num_comptasks,
		    ndims, counter);
        else if (ios->num_comptasks < 10000)
            sprintf(filename, "piodecomp%4.4dtasks%2.2ddims%2.2d.dat", ios->num_comptasks,
		    ndims, counter);
        else
            sprintf(filename, "piodecomp%6.6dtasks%2.2ddims%2.2d.dat", ios->num_comptasks,
		    ndims, counter);

	LOG((2, "saving decomp map to %s", filename));
        PIOc_writemap(filename, ndims, dims, maplen, (PIO_Offset *)compmap, ios->comp_comm);
        counter++;
    }

    /* Allocate space for the iodesc info. */
    if (!(iodesc = malloc_iodesc(basetype, ndims)))
	piodie("Out of memory", __FILE__, __LINE__);
    
    /* Set the rearranger. */
    if (!rearranger)
        iodesc->rearranger = ios->default_rearranger;
    else
        iodesc->rearranger = *rearranger;
    LOG((2, "iodesc->rearranger = %d", iodesc->rearranger));
    
    /* Is this the subset rearranger? */
    if (iodesc->rearranger == PIO_REARR_SUBSET)
    {
	LOG((2, "Handling subset rearranger."));
        if (iostart && iocount)
            fprintf(stderr,"%s %s\n","Iostart and iocount arguments to PIOc_InitDecomp",
                    "are incompatable with subset rearrange method and will be ignored");
        iodesc->num_aiotasks = ios->num_iotasks;
        ierr = subset_rearrange_create(*ios, maplen, (PIO_Offset *)compmap, dims,
                                       ndims, iodesc);
    }
    else
    {
	LOG((2, "Handling not the subset rearranger."));
        if (ios->ioproc)
        {
            /*  Unless the user specifies the start and count for each
             *  IO task compute it. */
            if (iostart && iocount)
            {
                iodesc->maxiobuflen = 1;
                for (int i = 0; i < ndims; i++)
                {
                    iodesc->firstregion->start[i] = iostart[i];
                    iodesc->firstregion->count[i] = iocount[i];
                    compute_maxIObuffersize(ios->io_comm, iodesc);

                }
                iodesc->num_aiotasks = ios->num_iotasks;
            }
            else
            {
                iodesc->num_aiotasks = CalcStartandCount(basetype, ndims, dims,
                                                         ios->num_iotasks, ios->io_rank,
                                                         iodesc->firstregion->start, iodesc->firstregion->count);
            }
            compute_maxIObuffersize(ios->io_comm, iodesc);
        }

        /* Depending on array size and io-blocksize the actual number
         * of io tasks used may vary. */
        if ((mpierr = MPI_Bcast(&(iodesc->num_aiotasks), 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
	LOG((3, "iodesc->num_aiotasks = %d", iodesc->num_aiotasks));

        /* Compute the communications pattern for this decomposition. */
        if (iodesc->rearranger == PIO_REARR_BOX)
            ierr = box_rearrange_create(*ios, maplen, compmap, dims, ndims, iodesc);

        /*
          if (ios->ioproc){
          io_region *ioregion = iodesc->firstregion;
          while(ioregion != NULL){
          for (int i=0;i<ndims;i++)
          printf("%s %d i %d dim %d start %ld count %ld\n",__FILE__,__LINE__,i,dims[i],ioregion->start[i],ioregion->count[i]);
          ioregion = ioregion->next;
          }
          }
        */
    }

    /* Add this IO description to the list. */
    *ioidp = pio_add_to_iodesc_list(iodesc);

    LOG((3, "About to tune rearranger..."));
    performance_tune_rearranger(*ios, iodesc);
    LOG((3, "Done with rearranger tune."));

    return PIO_NOERR;
}

/**
 * This is a simplified initdecomp which can be used if the memory
 * order of the data can be expressed in terms of start and count on
 * the file.  In this case we compute the compdof and use the subset
 * rearranger.
 *
 * @param iosysid the IO system ID
 * @param basetype
 * @param ndims the number of dimensions
 * @param dims array of dimensions
 * @param start start array
 * @param count count array
 * @param pointer that gets the IO ID.
 * @returns 0 for success, error code otherwise
 * @ingroup PIO_initdecomp
 */
int PIOc_InitDecomp_bc(const int iosysid, const int basetype, const int ndims, const int dims[],
                       const long int start[], const long int count[], int *ioidp)

{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    int mpierr;
    int ierr;
    int n, i, maplen = 1;
    int rearr = PIO_REARR_SUBSET;
    
    for (int i = 0; i < ndims; i++)
    {
        if (dims[i] <= 0)
            piodie("Invalid dims argument",__FILE__,__LINE__);

        if (start[i] < 0 || count[i] < 0 || (start[i] + count[i]) > dims[i])
            piodie("Invalid start or count argument ",__FILE__,__LINE__);
    }

    /* Get the info about the io system. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

    for (i = 0; i < ndims; i++)
        maplen *= count[i];

    PIO_Offset compmap[maplen], prod[ndims], loc[ndims];

    prod[ndims - 1] = 1;
    loc[ndims - 1] = 0;
    for (n = ndims - 2; n >= 0; n--)
    {
        prod[n] = prod[n + 1] * dims[n + 1];
        loc[n] = 0;
    }
    for (i = 0; i < maplen; i++)
    {
        compmap[i] = 0;
        for (n = ndims - 1; n >= 0; n--)
            compmap[i]+=(start[n]+loc[n])*prod[n];

        n = ndims - 1;
        loc[n] = (loc[n] + 1) % count[n];
        while (loc[n] == 0 && n > 0)
	{
            n--;
            loc[n] = (loc[n] + 1) % count[n];
        }
    }

    PIOc_InitDecomp( iosysid, basetype,ndims, dims,
                     maplen,  compmap, ioidp, &rearr, NULL, NULL);

    return PIO_NOERR;
}

/**
 * Library initialization used when IO tasks are a subset of compute
 * tasks.
 *
 * This function creates an MPI intracommunicator between a set of IO
 * tasks and one or more sets of computational tasks.
 *
 * The caller must create all comp_comm and the io_comm MPI
 * communicators before calling this function.
 *
 * @param comp_comm the MPI_Comm of the compute tasks
 * @param num_iotasks the number of io tasks to use
 * @param stride the offset between io tasks in the comp_comm
 * @param base the comp_comm index of the first io task
 * @param rearr the rearranger to use by default, this may be
 * overriden in the @ref PIO_initdecomp
 * @param iosysidp index of the defined system descriptor
 * @return 0 on success, otherwise a PIO error code.
 * @ingroup PIO_init
 */
int PIOc_Init_Intracomm(MPI_Comm comp_comm, int num_iotasks, int stride, int base,
                        int rearr, int *iosysidp)
{
    iosystem_desc_t *ios;
    int ustride;
    int lbase;
    int mpierr; /* Return value for MPI calls. */

    pio_init_logging();

    LOG((1, "PIOc_Init_Intracomm comp_comm = %d num_iotasks = %d stride = %d base = %d "
         "rearr = %d", comp_comm, num_iotasks, stride, base, rearr));

    /* Allocate memory for the iosystem info. */
    if (!(ios = calloc(1, sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;

    ios->io_comm = MPI_COMM_NULL;
    ios->intercomm = MPI_COMM_NULL;
    ios->error_handler = PIO_INTERNAL_ERROR;
    ios->default_rearranger = rearr;
    ios->num_iotasks = num_iotasks;

    /* Copy the computation communicator into union_comm. */
    if ((mpierr = MPI_Comm_dup(comp_comm, &ios->union_comm)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);

    /* Copy the computation communicator into comp_comm. */
    if ((mpierr = MPI_Comm_dup(comp_comm, &ios->comp_comm)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);            
    LOG((2, "union_comm = %d comp_comm = %d", ios->union_comm, ios->comp_comm));

    ios->my_comm = ios->comp_comm;
    ustride = stride;

    /* Find MPI rank and number of tasks in comp_comm communicator. */
    if ((mpierr = MPI_Comm_rank(ios->comp_comm, &ios->comp_rank)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);
    if ((mpierr = MPI_Comm_size(ios->comp_comm, &ios->num_comptasks)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);
    
    if (ios->comp_rank == 0)
        ios->compmaster = MPI_ROOT;
    LOG((2, "comp_rank = %d num_comptasks = %d", ios->comp_rank, ios->num_comptasks));

    /* Ensure that settings for number of computation tasks, number
     * of IO tasks, and the stride are reasonable. */
    if (ios->num_comptasks == 1 && num_iotasks * ustride > 1)
    {
        // This is a serial run with a bad configuration. Set up a single task.
        fprintf(stderr, "PIO_TP PIOc_Init_Intracomm reset stride and tasks.\n");
        ios->num_iotasks = 1;
        ustride = 1;
    }
    
    if (ios->num_iotasks < 1 || ios->num_iotasks * ustride > ios->num_comptasks)
    {
        fprintf(stderr, "PIO_TP PIOc_Init_Intracomm error\n");
        fprintf(stderr, "num_iotasks=%d, ustride=%d, num_comptasks=%d\n", num_iotasks,
                ustride, ios->num_comptasks);
        return pio_err(ios, NULL, PIO_EINVAL, __FILE__, __LINE__);
    }

    /* Create an array that holds the ranks of the tasks to be used
     * for IO. NOTE that sizeof(int) should probably be 1, not
     * sizeof(int) ???*/
    if (!(ios->ioranks = calloc(sizeof(int), ios->num_iotasks)))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
    for (int i = 0; i < ios->num_iotasks; i++)
    {
        ios->ioranks[i] = (base + i * ustride) % ios->num_comptasks;
        if (ios->ioranks[i] == ios->comp_rank)
            ios->ioproc = true;
    }
    ios->ioroot = ios->ioranks[0];

    for (int i = 0; i < ios->num_iotasks; i++)
        LOG((3, "ios->ioranks[%d] = %d", i, ios->ioranks[i]));

    /* We are not providing an info object. */
    ios->info = MPI_INFO_NULL;

    /* The task that has an iomaster value of MPI_ROOT will be the
     * root of the IO communicator. */
    if (ios->comp_rank == ios->ioranks[0])
        ios->iomaster = MPI_ROOT;

    /* Create a group for the computation tasks. */
    if ((mpierr = MPI_Comm_group(ios->comp_comm, &ios->compgroup)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);

    /* Create a group for the IO tasks. */
    if ((mpierr = MPI_Group_incl(ios->compgroup, ios->num_iotasks, ios->ioranks,
                                 &ios->iogroup)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);        

    /* Create an MPI communicator for the IO tasks. */
    if ((mpierr = MPI_Comm_create(ios->comp_comm, ios->iogroup, &ios->io_comm)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);                

    /* For the tasks that are doing IO, get their rank within the IO
     * communicator. For some reason when I check the return value of
     * this MPI call, all tests start to fail! */
    if (ios->ioproc)
    {
        if ((mpierr = MPI_Comm_rank(ios->io_comm, &ios->io_rank)))
            return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);                            
    }
    else
        ios->io_rank = -1;
    LOG((3, "ios->io_comm = %d ios->io_rank = %d", ios->io_comm, ios->io_rank));

    ios->union_rank = ios->comp_rank;

    /* Add this ios struct to the list in the PIO library. */
    *iosysidp = pio_add_to_iosystem_list(ios);

    /* Allocate buffer space for compute nodes. */
    compute_buffer_init(*ios);

    LOG((2, "Init_Intracomm complete iosysid = %d", *iosysidp));

    return PIO_NOERR;
}

/**
 * Interface to call from pio_init from fortran.
 *
 * @param f90_comp_comm
 * @param num_iotasks the number of IO tasks
 * @param stride the stride to use assigning tasks
 * @param base the starting point when assigning tasks
 * @param rearr the rearranger
 * @param iosysidp a pointer that gets the IO system ID
 * @returns 0 for success, error code otherwise
 */
int PIOc_Init_Intracomm_from_F90(int f90_comp_comm,
                                 const int num_iotasks, const int stride,
                                 const int base, const int rearr, int *iosysidp)
{
    return PIOc_Init_Intracomm(MPI_Comm_f2c(f90_comp_comm), num_iotasks, stride, base, rearr,
                               iosysidp);
}

/**
 * Send a hint to the MPI-IO library.
 *
 * @param iosysid the IO system ID
 * @param hint the hint for MPI
 * @param hintval the value of the hint
 * @returns 0 for success, or PIO_BADID if iosysid can't be found.
 */
int PIOc_set_hint(int iosysid, const char *hint, const char *hintval)
{
    iosystem_desc_t *ios;
    int mpierr; /* Return value for MPI calls. */
    
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* Set the MPI hint. */
    if (ios->ioproc)
        if ((mpierr = MPI_Info_set(ios->info, hint, hintval)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    
    return PIO_NOERR;
}

/**
 * Clean up internal data structures, free MPI resources, and exit the
 * pio library.
 *
 * @param iosysid: the io system ID provided by PIOc_Init_Intracomm().
 * @returns 0 for success or non-zero for error.
 * @ingroup PIO_finalize
 */
int PIOc_finalize(int iosysid)
{
    iosystem_desc_t *ios, *nios;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int ierr = PIO_NOERR;

    LOG((1, "PIOc_finalize iosysid = %d MPI_COMM_NULL = %d", iosysid,
         MPI_COMM_NULL));

    /* Find the IO system information. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* If asynch IO is in use, send the PIO_MSG_EXIT message from the
     * comp master to the IO processes. This may be called by
     * componets for other components iosysid. So don't send unless
     * there is a valid union_comm. */
    if (ios->async_interface && ios->union_comm != MPI_COMM_NULL)
    {
        int msg = PIO_MSG_EXIT;

        LOG((3, "found iosystem info comproot = %d union_comm = %d comp_idx = %d",
             ios->comproot, ios->union_comm, ios->comp_idx));
        if (!ios->ioproc)
        {
            LOG((2, "sending msg = %d ioroot = %d union_comm = %d", msg,
                 ios->ioroot, ios->union_comm));

            /* Send the message to the message handler. */
            if (ios->compmaster)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            /* Send the parameters of the function call. */
            if (!mpierr)
                mpierr = MPI_Bcast((int *)&iosysid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        LOG((3, "handling async errors mpierr = %d my_comm = %d", mpierr, ios->my_comm));
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(NULL, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        LOG((3, "async errors bcast"));
    }

    /* Free this memory that was allocated in init_intracomm. */
    if (ios->ioranks)
        free(ios->ioranks);
    LOG((3, "Freed ioranks."));

    /* Free the buffer pool. */
    int niosysid;
    if ((ierr = pio_num_iosystem(&niosysid)))
        return ierr;
    LOG((2, "%d iosystems are still open.", niosysid));

    /* Only free the buffer pool if this is the last open iosysid. */
    if (niosysid == 1)
    {
        free_cn_buffer_pool(*ios);
        LOG((2, "Freed buffer pool."));
    }

    /* Free the MPI groups. */
    if (ios->compgroup != MPI_GROUP_NULL)
        MPI_Group_free(&ios->compgroup);

    if (ios->iogroup != MPI_GROUP_NULL)
        MPI_Group_free(&(ios->iogroup));

    /* Free the MPI communicators. my_comm is just a copy (but not an
     * MPI copy), so does not have to have an MPI_Comm_free()
     * call. comp_comm and io_comm are MPI duplicates of the comms
     * handed into init_intercomm. So they need to be freed by MPI. */
    if (ios->intercomm != MPI_COMM_NULL)
        MPI_Comm_free(&ios->intercomm);
    if (ios->union_comm != MPI_COMM_NULL)
        MPI_Comm_free(&ios->union_comm);
    if (ios->io_comm != MPI_COMM_NULL)
        MPI_Comm_free(&ios->io_comm);
    if (ios->comp_comm != MPI_COMM_NULL)
        MPI_Comm_free(&ios->comp_comm);
    if (ios->my_comm != MPI_COMM_NULL)
        ios->my_comm = MPI_COMM_NULL;

    /* Delete the iosystem_desc_t data associated with this id. */
    LOG((2, "About to delete iosysid %d.", iosysid));
    if ((ierr = pio_delete_iosystem_from_list(iosysid)))
        return ierr;
    
    LOG((2, "About to finalize logging"));
    pio_finalize_logging();

    LOG((2, "PIOc_finalize completed successfully"));
    return PIO_NOERR;
}

/**
 * Return a logical indicating whether this task is an IO task.
 *
 * @param iosysid the io system ID
 * @param ioproc a pointer that gets 1 if task is an IO task, 0
 * otherwise. Ignored if NULL.
 * @returns 0 for success, or PIO_BADID if iosysid can't be found.
 */
int PIOc_iam_iotask(int iosysid, bool *ioproc)
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    if (ioproc)
        *ioproc = ios->ioproc;

    return PIO_NOERR;
}

/**
 * Return the rank of this task in the IO communicator or -1 if this
 * task is not in the communicator.
 *
 * @param iosysid the io system ID
 * @param iorank a pointer that gets the io rank, or -1 if task is not
 * in the IO communicator. Ignored if NULL.
 * @returns 0 for success, or PIO_BADID if iosysid can't be found.
 */
int PIOc_iotask_rank(int iosysid, int *iorank)
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    if (iorank)
        *iorank = ios->io_rank;

    return PIO_NOERR;
}

/**
 * Return true if this iotype is supported in the build, 0 otherwise.
 *
 * @param iotype the io type to check
 * @returns 1 if iotype is in build, 0 if not.
 */
int PIOc_iotype_available(int iotype)
{
    switch(iotype)
    {
#ifdef _NETCDF
#ifdef _NETCDF4
    case PIO_IOTYPE_NETCDF4P:
    case PIO_IOTYPE_NETCDF4C:
        return 1;
#endif
    case PIO_IOTYPE_NETCDF:
        return 1;
#endif
#ifdef _PNETCDF
    case PIO_IOTYPE_PNETCDF:
        return 1;
        break;
#endif
    default:
        return 0;
    }
}
