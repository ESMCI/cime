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
int PIOc_iosystem_is_active(const int iosysid, bool *active)
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

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
 * Set the error handling method to be used for subsequent pio
 * library calls, returns the previous method setting.
 *
 * @param ncid the ncid of an open file
 * @param method the error handling method
 * @returns 0 on success, error code otherwise
 */
int PIOc_Set_File_Error_Handling(int ncid, int method)
{
    file_desc_t *file;
    int oldmethod;
    int ret;

    /* Find info for this file. */
    if ((ret = pio_get_file(ncid, &file)))
        return ret;

    oldmethod = file->iosystem->error_handler;
    file->iosystem->error_handler = method;
    return oldmethod;
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
 * @ingroup PIO_setframe
 * Set the unlimited dimension of the given variable
 *
 * @param ncid the ncid of the file.
 * @param varid the varid of the variable
 * @param frame the value of the unlimited dimension.  In c 0 for the
 * first record, 1 for the second
 *
 * @return PIO_NOERR for no error, or error code.
 */
int PIOc_setframe(const int ncid, const int varid, const int frame)
{
    file_desc_t *file;
    int ret;

    /* Check inputs. */
    if (varid < 0 || varid >= PIO_MAX_VARS)
        return PIO_EINVAL;

    /* Get file info. */
    if ((ret = pio_get_file(ncid, &file)))
        return ret;

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
 * @ingroup PIO_error_method
 * Set the error handling method used for subsequent calls.
 *
 * @param iosysid the IO system ID
 * @param method the error handling method
 * @returns 0 on success, error code otherwise
 */
int PIOc_Set_IOSystem_Error_Handling(int iosysid, int method)
{
    iosystem_desc_t *ios;
    int oldmethod;

    /* Find info about this iosystem. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

    /* Remember old method setting. */
    oldmethod = ios->error_handler;

    /* Set new error handler. */
    ios->error_handler = method;

    return oldmethod;
}

/**
 * @ingroup PIO_initdecomp
 * C interface to the initdecomp.
 *
 * @param  iosysid @copydoc iosystem_desc_t (input)
 * @param  basetype the basic PIO data type used (input)
 * @param  ndims the number of dimensions in the variable (input)
 * @param  dims an array of global size of each dimension.
 * @param  maplen the local length of the compmap array (input)
 * @param compmap[] a 1 based array of offsets into the array record
 * on file.  A 0 in this array indicates a value which should not be
 * transfered. (input)
 * @param ioidp  the io description pointer (output)
 * @param rearranger the rearranger to be used for this decomp or NULL
 * to use the default (optional input)
 * @param iostart An optional array of start values for block cyclic
 * decompositions (optional input)
 * @param iocount An optional array of count values for block cyclic
 * decompositions (optional input)
 * @returns 0 on success, error code otherwise
 */
int PIOc_InitDecomp(const int iosysid, const int basetype, const int ndims, const int *dims,
                    const int maplen, const PIO_Offset *compmap, int *ioidp, const int *rearranger,
                    const PIO_Offset *iostart, const PIO_Offset *iocount)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    int iosize;
    int ndisp;
    int mpierr; /* Return code from MPI calls. */
    int ierr;   /* Return code. */

    LOG((1, "PIOc_InitDecomp iosysid = %d basetype = %d ndims = %d maplen = %d",
         iosysid, basetype, ndims, maplen));

    /* Check the dim lengths. */
    for (int i = 0; i < ndims; i++)
        if (dims[i] <= 0)
            piodie("Invalid dims argument",__FILE__,__LINE__);

    /* Get IO system info. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

    /* If desired, save the computed decompositions to files. */
    if (PIO_Save_Decomps)
    {
        char filename[30];
        if (ios->num_comptasks < 100)
            sprintf(filename, "piodecomp%2.2dtasks%2.2ddims%2.2d.dat", ios->num_comptasks, ndims, counter);
        else if (ios->num_comptasks < 10000)
            sprintf(filename, "piodecomp%4.4dtasks%2.2ddims%2.2d.dat", ios->num_comptasks, ndims, counter);
        else
            sprintf(filename, "piodecomp%6.6dtasks%2.2ddims%2.2d.dat", ios->num_comptasks, ndims, counter);

        PIOc_writemap(filename, ndims, dims, maplen, (PIO_Offset *)compmap, ios->comp_comm);
        counter++;
    }

    /* Allocate space for the iodesc info. */
    iodesc = malloc_iodesc(basetype, ndims);

    /* Set the rearranger. */
    if (rearranger == NULL)
        iodesc->rearranger = ios->default_rearranger;
    else
        iodesc->rearranger = *rearranger;

    if (iodesc->rearranger == PIO_REARR_SUBSET)
    {
        if (iostart && iocount)
        {
            fprintf(stderr,"%s %s\n","Iostart and iocount arguments to PIOc_InitDecomp",
                    "are incompatable with subset rearrange method and will be ignored");
        }
        iodesc->num_aiotasks = ios->num_iotasks;
        ierr = subset_rearrange_create(*ios, maplen, (PIO_Offset *)compmap, dims,
                                       ndims, iodesc);
    }
    else
    {
        if (ios->ioproc)
        {
            /*  Unless the user specifies the start and count for each
             *  IO task compute it. */
            if (iostart && iocount)
            {
                iodesc->maxiobuflen=1;
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
        CheckMPIReturn(MPI_Bcast(&(iodesc->num_aiotasks), 1, MPI_INT, ios->ioroot,
                                 ios->my_comm),__FILE__,__LINE__);

        /* Compute the communications pattern for this decomposition. */
        if (iodesc->rearranger == PIO_REARR_BOX)
            ierr = box_rearrange_create( *ios, maplen, compmap, dims, ndims, iodesc);

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

    performance_tune_rearranger(*ios, iodesc);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_initdecomp
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
 */
int PIOc_InitDecomp_bc(const int iosysid, const int basetype, const int ndims, const int dims[],
                       const long int start[], const long int count[], int *ioidp)

{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    int mpierr;
    int ierr;
    int iosize;
    int ndisp;

    for (int i=0;i<ndims;i++){
        if (dims[i]<=0){
            piodie("Invalid dims argument",__FILE__,__LINE__);
        }
        if (start[i]<0 || count[i]< 0 || (start[i]+count[i])>dims[i]){
            piodie("Invalid start or count argument ",__FILE__,__LINE__);
        }
    }
    ios = pio_get_iosystem_from_id(iosysid);
    if (ios == NULL)
        return PIO_EBADID;

    int n, i, maplen=1;

    for ( i=0;i<ndims;i++){
        maplen*=count[i];
    }
    PIO_Offset compmap[maplen], prod[ndims], loc[ndims];

    prod[ndims-1]=1;
    loc[ndims-1]=0;
    for (n=ndims-2;n>=0;n--){
        prod[n]=prod[n+1]*dims[n+1];
        loc[n]=0;
    }
    for (i=0;i<maplen;i++){
        compmap[i]=0;
        for (n=ndims-1;n>=0;n--){
            compmap[i]+=(start[n]+loc[n])*prod[n];
        }
        n=ndims-1;
        loc[n]=(loc[n]+1)%count[n];
        while(loc[n]==0 && n>0){
            n--;
            loc[n]=(loc[n]+1)%count[n];
        }
    }
    int rearr = PIO_REARR_SUBSET;
    PIOc_InitDecomp( iosysid, basetype,ndims, dims,
                     maplen,  compmap, ioidp, &rearr, NULL, NULL);


    return PIO_NOERR;
}

/**
 * @ingroup PIO_init
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
 */
int PIOc_Init_Intracomm(const MPI_Comm comp_comm, const int num_iotasks,
                        const int stride, const int base, const int rearr,
                        int *iosysidp)
{
    iosystem_desc_t *iosys;
    int ierr = PIO_NOERR;
    int ustride;
    int lbase;
    int mpierr;

    LOG((1, "PIOc_Init_Intracomm comp_comm = %d num_iotasks = %d stride = %d base = %d "
         "rearr = %d", comp_comm, num_iotasks, stride, base, rearr));

    if (!(iosys = malloc(sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;

    /* Copy the computation communicator into union_comm. */
    mpierr = MPI_Comm_dup(comp_comm, &iosys->union_comm);
    CheckMPIReturn(mpierr, __FILE__, __LINE__);
    if (mpierr)
        ierr = PIO_EIO;

    /* Copy the computation communicator into comp_comm. */
    if (!ierr)
    {
        mpierr = MPI_Comm_dup(comp_comm, &iosys->comp_comm);
        CheckMPIReturn(mpierr, __FILE__, __LINE__);
        if (mpierr)
            ierr = PIO_EIO;
    }
    LOG((2, "union_comm = %d comp_comm = %d", iosys->union_comm, iosys->comp_comm));

    if (!ierr)
    {
        iosys->my_comm = iosys->comp_comm;
        iosys->io_comm = MPI_COMM_NULL;
        iosys->intercomm = MPI_COMM_NULL;
        iosys->error_handler = PIO_INTERNAL_ERROR;
        iosys->async_interface= false;
        iosys->compmaster = 0;
        iosys->iomaster = 0;
        iosys->ioproc = false;
        iosys->default_rearranger = rearr;
        iosys->num_iotasks = num_iotasks;

        ustride = stride;

        /* Find MPI rank and number of tasks in comp_comm communicator. */
        CheckMPIReturn(MPI_Comm_rank(iosys->comp_comm, &(iosys->comp_rank)),__FILE__,__LINE__);
        CheckMPIReturn(MPI_Comm_size(iosys->comp_comm, &(iosys->num_comptasks)),__FILE__,__LINE__);
        if (iosys->comp_rank==0)
            iosys->compmaster = MPI_ROOT;
        LOG((2, "comp_rank = %d num_comptasks = %d", iosys->comp_rank, iosys->num_comptasks));

        /* Ensure that settings for number of computation tasks, number
         * of IO tasks, and the stride are reasonable. */
        if ((iosys->num_comptasks == 1) && (num_iotasks*ustride > 1)) {
            // This is a serial run with a bad configuration. Set up a single task.
            fprintf(stderr, "PIO_TP PIOc_Init_Intracomm reset stride and tasks.\n");
            iosys->num_iotasks = 1;
            ustride = 1;
        }
        if ((iosys->num_iotasks < 1) || ((iosys->num_iotasks*ustride) > iosys->num_comptasks)){
            fprintf(stderr, "PIO_TP PIOc_Init_Intracomm error\n");
            fprintf(stderr, "num_iotasks=%d, ustride=%d, num_comptasks=%d\n", num_iotasks, ustride, iosys->num_comptasks);
            return PIO_EBADID;
        }

        /* Create an array that holds the ranks of the tasks to be used for IO. */
        iosys->ioranks = (int *) calloc(sizeof(int), iosys->num_iotasks);
        for (int i=0;i< iosys->num_iotasks; i++){
            iosys->ioranks[i] = (base + i*ustride) % iosys->num_comptasks;
            if (iosys->ioranks[i] == iosys->comp_rank)
                iosys->ioproc = true;
        }
        iosys->ioroot = iosys->ioranks[0];

        for (int i = 0; i < iosys->num_iotasks; i++)
            LOG((3, "iosys->ioranks[%d] = %d", i, iosys->ioranks[i]));

        /* Create an MPI info object. */
        CheckMPIReturn(MPI_Info_create(&(iosys->info)),__FILE__,__LINE__);
        iosys->info = MPI_INFO_NULL;

        if (iosys->comp_rank == iosys->ioranks[0])
            iosys->iomaster = MPI_ROOT;

        /* Create a group for the computation tasks. */
        CheckMPIReturn(MPI_Comm_group(iosys->comp_comm, &(iosys->compgroup)),__FILE__,__LINE__);

        /* Create a group for the IO tasks. */
        CheckMPIReturn(MPI_Group_incl(iosys->compgroup, iosys->num_iotasks, iosys->ioranks,
                                      &(iosys->iogroup)),__FILE__,__LINE__);

        /* Create an MPI communicator for the IO tasks. */
        CheckMPIReturn(MPI_Comm_create(iosys->comp_comm, iosys->iogroup, &(iosys->io_comm))
                       ,__FILE__,__LINE__);

        /* For the tasks that are doing IO, get their rank. */
        if (iosys->ioproc)
            CheckMPIReturn(MPI_Comm_rank(iosys->io_comm, &(iosys->io_rank)),__FILE__,__LINE__);
        else
            iosys->io_rank = -1;
        LOG((3, "iosys->io_comm = %d iosys->io_rank = %d", iosys->io_comm, iosys->io_rank));

        iosys->union_rank = iosys->comp_rank;

        /* Add this iosys struct to the list in the PIO library. */
        *iosysidp = pio_add_to_iosystem_list(iosys);

        /* Allocate buffer space for compute nodes. */
        compute_buffer_init(*iosys);

        LOG((2, "Init_Intracomm complete iosysid = %d", *iosysidp));
    }

    return ierr;
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
int PIOc_set_hint(const int iosysid, char hint[], const char hintval[])
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

    /* Set the MPI hint. */
    if (ios->ioproc)
        CheckMPIReturn(MPI_Info_set(ios->info, hint, hintval), __FILE__,__LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_finalize
 * Clean up internal data structures, free MPI resources, and exit the
 * pio library.
 *
 * @param iosysid: the io system ID provided by PIOc_Init_Intracomm().
 * @returns 0 for success or non-zero for error.
 */
int PIOc_finalize(const int iosysid)
{
    iosystem_desc_t *ios, *nios;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int ierr = PIO_NOERR;

    LOG((1, "PIOc_finalize iosysid = %d MPI_COMM_NULL = %d", iosysid,
         MPI_COMM_NULL));

    /* Find the IO system information. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;
    LOG((3, "found iosystem info comproot = %d union_comm = %d comp_idx = %d",
         ios->comproot, ios->union_comm, ios->comp_idx));

    /* If asynch IO is in use, send the PIO_MSG_EXIT message from the
     * comp master to the IO processes. This may be called by
     * componets for other components iosysid. So don't send unless
     * there is a valid union_comm. */
    if (ios->async_interface && ios->union_comm != MPI_COMM_NULL)
    {
        int msg = PIO_MSG_EXIT;

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
    ierr = pio_delete_iosystem_from_list(iosysid);
    LOG((2, "PIOc_finalize completed successfully"));

    return ierr;
}

/**
 * Return a logical indicating whether this task is an IO task.
 *
 * @param iosysid the io system ID
 * @param ioproc a pointer that gets 1 if task is an IO task, 0
 * otherwise. Ignored if NULL.
 * @returns 0 for success, or PIO_BADID if iosysid can't be found.
 */
int PIOc_iam_iotask(const int iosysid, bool *ioproc)
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

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
int PIOc_iotask_rank(const int iosysid, int *iorank)
{
    iosystem_desc_t *ios;

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

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
int PIOc_iotype_available(const int iotype)
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
