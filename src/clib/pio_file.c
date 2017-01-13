/**
 * @file
 * PIO File Handling
 */
#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/* This is the next ncid that will be used when a file is opened or
   created. We start at 16 so that it will be easy for us to notice
   that it's not netcdf (starts at 4), pnetcdf (starts at 0) or
   netCDF-4/HDF5 (starts at 65xxx). */
int pio_next_ncid = 16;

/**
 * Open an existing file using PIO library.
 *
 * If the open fails, try again as netCDF serial before giving
 * up. Input parameters are read on comp task 0 and ignored elsewhere.
 *
 * @param iosysid : A defined pio system descriptor (input)
 * @param ncidp : A pio file descriptor (output)
 * @param iotype : A pio output format (input)
 * @param filename : The filename to open
 * @param mode : The netcdf mode for the open operation
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_openfile
 */
int PIOc_openfile(int iosysid, int *ncidp, int *iotype, const char *filename,
                  int mode)
{
    LOG((1, "PIOc_openfile iosysid = %d iotype = %d filename = %s mode = %d",
         iosysid, *iotype, filename, mode));

    return PIOc_openfile_retry(iosysid, ncidp, iotype, filename, mode, 1);
}

/**
 * Open an existing file using PIO library.
 *
 * Input parameters are read on comp task 0 and ignored elsewhere.
 *
 * @param iosysid A defined pio system descriptor
 * @param path The filename to open
 * @param mode The netcdf mode for the open operation
 * @param ncidp pointer to int where ncid will go
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_openfile
 */
int PIOc_open(int iosysid, const char *path, int mode, int *ncidp)
{
    int iotype;

    LOG((1, "PIOc_open iosysid = %d path = %s mode = %x", iosysid, path, mode));

    /* Figure out the iotype. */
    if (mode & NC_NETCDF4)
    {
        if (mode & NC_MPIIO || mode & NC_MPIPOSIX)
            iotype = PIO_IOTYPE_NETCDF4P;
        else
            iotype = PIO_IOTYPE_NETCDF4C;
    }
    else
    {
        if (mode & NC_PNETCDF || mode & NC_MPIIO)
            iotype = PIO_IOTYPE_PNETCDF;
        else
            iotype = PIO_IOTYPE_NETCDF;
    }

    /* Open the file. If the open fails, do not retry as serial
     * netCDF. Just return the error code. */
    return PIOc_openfile_retry(iosysid, ncidp, &iotype, path, mode, 0);
}

/**
 * Create a new file using pio. Input parameters are read on comp task
 * 0 and ignored elsewhere.
 *
 * @param iosysid A defined pio system ID, obtained from
 * PIOc_InitIntercomm() or PIOc_InitAsync().
 * @param ncidp A pointer that gets the ncid of the newly created
 * file.
 * @param iotype A pointer to a pio output format. Must be one of
 * PIO_IOTYPE_PNETCDF, PIO_IOTYPE_NETCDF, PIO_IOTYPE_NETCDF4C, or
 * PIO_IOTYPE_NETCDF4P.
 * @param filename The filename to create.
 * @param mode The netcdf mode for the create operation.
 * @returns 0 for success, error code otherwise.
 * @ingroup PIO_createfile
 */
int PIOc_createfile(int iosysid, int *ncidp, int *iotype, const char *filename, int mode)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the IO system info from the iosysid. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* User must provide valid input for these parameters. */
    if (!ncidp || !iotype || !filename || strlen(filename) > NC_MAX_NAME)
        return pio_err(ios, NULL, PIO_EINVAL, __FILE__, __LINE__);

    /* A valid iotype must be specified. */
    if (!iotype_is_valid(*iotype))
        return pio_err(ios, NULL, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_createfile iosysid = %d iotype = %d filename = %s mode = %d",
         iosysid, *iotype, filename, mode));

    /* Allocate space for the file info. */
    if (!(file = calloc(sizeof(file_desc_t), 1)))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    /* Fill in some file values. */
    file->fh = -1;
    file->iosystem = ios;
    file->iotype = *iotype;
    file->buffer.ioid = -1;
    for (int i = 0; i < PIO_MAX_VARS; i++)
    {
        file->varlist[i].record = -1;
        file->varlist[i].ndims = -1;
    }
    file->mode = mode;

    /* Set to true if this task should participate in IO (only true for
     * one task with netcdf serial files. */
    if (file->iotype == PIO_IOTYPE_NETCDF4P || file->iotype == PIO_IOTYPE_PNETCDF ||
        ios->io_rank == 0)
        file->do_io = 1;

    LOG((2, "file->do_io = %d ios->async_interface = %d", file->do_io, ios->async_interface));

    /* If async is in use, and this is not an IO task, bcast the
     * parameters. */
    if (ios->async_interface)
    {
        int msg = PIO_MSG_CREATE_FILE;
        size_t len = strlen(filename);

        if (!ios->ioproc)
        {
            /* Send the message to the message handler. */
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            /* Send the parameters of the function call. */
            if (!mpierr)
                mpierr = MPI_Bcast(&len, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)filename, len + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&file->iotype, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&file->mode, 1, MPI_INT, ios->compmaster, ios->intercomm);
            LOG((2, "len = %d filename = %s iotype = %d mode = %d", len, filename,
                 file->iotype, file->mode));
        }

        /* Handle MPI errors. */
        LOG((2, "handling mpi errors mpierr = %d", mpierr));
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this task is in the IO component, do the IO. */
    if (ios->ioproc)
    {
        switch (file->iotype)
        {
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            file->mode = file->mode |  NC_MPIIO | NC_NETCDF4;
            LOG((2, "Calling nc_create_par io_comm = %d mode = %d fh = %d",
                 ios->io_comm, file->mode, file->fh));
            ierr = nc_create_par(filename, file->mode, ios->io_comm, ios->info, &file->fh);
            LOG((2, "nc_create_par returned %d file->fh = %d", ierr, file->fh));
            break;
        case PIO_IOTYPE_NETCDF4C:
            file->mode = file->mode | NC_NETCDF4;
#endif
        case PIO_IOTYPE_NETCDF:
            if (!ios->io_rank)
            {
                LOG((2, "Calling nc_create mode = %d", file->mode));
                ierr = nc_create(filename, file->mode, &file->fh);
            }
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            LOG((2, "Calling ncmpi_create mode = %d", file->mode));
            ierr = ncmpi_create(ios->io_comm, filename, file->mode, ios->info, &file->fh);
            if (!ierr)
                ierr = ncmpi_buffer_attach(file->fh, pio_buffer_size_limit);
            break;
#endif
        }
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    /* If there was an error, free the memory we allocated and handle error. */
    if (ierr)
    {
        free(file);
        return check_netcdf2(ios, NULL, ierr, __FILE__, __LINE__);
    }

    /* Broadcast mode to all tasks. */
    if ((mpierr = MPI_Bcast(&file->mode, 1, MPI_INT, ios->ioroot, ios->union_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    /* This flag is implied by netcdf create functions but we need
       to know if its set. */
    file->mode = file->mode | PIO_WRITE;

    /* Assign the PIO ncid, necessary because files may be opened
     * on mutilple iosystems, causing the underlying library to
     * reuse ncids. Hilarious confusion ensues. */
    file->pio_ncid = pio_next_ncid++;
    LOG((2, "file->fh = %d file->pio_ncid = %d", file->fh, file->pio_ncid));

    /* Return the ncid to the caller. */
    *ncidp = file->pio_ncid;

    /* Add the struct with this files info to the global list of
     * open files. */
    pio_add_to_file_list(file);

    LOG((2, "Created file %s file->fh = %d file->pio_ncid = %d", filename,
         file->fh, file->pio_ncid));

    return ierr;
}

/**
 * Open a new file using pio. Input parameters are read on comp task
 * 0 and ignored elsewhere.
 *
 * @param iosysid : A defined pio system descriptor (input)
 * @param cmode : The netcdf mode for the create operation
 * @param filename : The filename to open
 * @param ncidp : A pio file descriptor (output)
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_create
 */
int PIOc_create(int iosysid, const char *filename, int cmode, int *ncidp)
{
    int iotype;            /* The PIO IO type. */

    /* Figure out the iotype. */
    if (cmode & NC_NETCDF4)
    {
        if (cmode & NC_MPIIO || cmode & NC_MPIPOSIX)
            iotype = PIO_IOTYPE_NETCDF4P;
        else
            iotype = PIO_IOTYPE_NETCDF4C;
    }
    else
    {
        if (cmode & NC_PNETCDF || cmode & NC_MPIIO)
            iotype = PIO_IOTYPE_PNETCDF;
        else
            iotype = PIO_IOTYPE_NETCDF;
    }

    return PIOc_createfile(iosysid, ncidp, &iotype, filename, cmode);
}

/**
 * Close a file previously opened with PIO.
 *
 * @param ncid: the file pointer
 * @returns PIO_NOERR for success, error code otherwise.
 */
int PIOc_closefile(int ncid)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_closefile ncid = %d", ncid));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* Sync changes before closing on all tasks if async is not in
     * use, but only on non-IO tasks if async is in use. */
    if (!ios->async_interface || !ios->ioproc)
        if (file->mode & PIO_WRITE)
            PIOc_sync(ncid);

    /* If async is in use and this is a comp tasks, then the compmaster
     * sends a msg to the pio_msg_handler running on the IO master and
     * waiting for a message. Then broadcast the ncid over the intercomm
     * to the IO tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_CLOSE_FILE;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
        switch (file->iotype)
        {
#ifdef _NETCDF
#ifdef _NETCDF4
        case PIO_IOTYPE_NETCDF4P:
            ierr = nc_close(file->fh);
            break;
        case PIO_IOTYPE_NETCDF4C:
#endif
        case PIO_IOTYPE_NETCDF:
            if (ios->io_rank == 0)
                ierr = nc_close(file->fh);
            break;
#endif
#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            if ((file->mode & PIO_WRITE)){
                ierr = ncmpi_buffer_detach(file->fh);
            }
            ierr = ncmpi_close(file->fh);
            break;
#endif
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Delete file from our list of open files. */
    pio_delete_file_from_list(ncid);

    return ierr;
}

/**
 * Delete a file.
 *
 * @param iosysid a pio system handle.
 * @param filename a filename.
 * @returns PIO_NOERR for success, error code otherwise.
 */
int PIOc_deletefile(int iosysid, const char *filename)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int delete_called = 0; /* Becomes non-zero after delete is called. */
    int msg = PIO_MSG_DELETE_FILE;
    size_t len;

    LOG((1, "PIOc_deletefile iosysid = %d filename = %s", iosysid, filename));

    /* Get the IO system info from the id. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* If async is in use, send message to IO master task. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            if (ios->comp_rank==0)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            len = strlen(filename);
            if (!mpierr)
                mpierr = MPI_Bcast(&len, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)filename, len + 1, MPI_CHAR, ios->compmaster,
                                   ios->intercomm);
            LOG((2, "Bcast len = %d filename = %s", len, filename));
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi2(ios, NULL, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);
        LOG((3, "done hanlding errors mpierr = %d", mpierr));
    }

    /* If this is an IO task, then call the netCDF function. The
     * barriers are needed to assure that no task is trying to operate
     * on the file while it is being deleted. */
    if (ios->ioproc)
    {
        mpierr = MPI_Barrier(ios->io_comm);

#ifdef _NETCDF
        if (!mpierr && ios->io_rank == 0)
        {
            ierr = nc_delete(filename);
            delete_called++;
        }
#else
#ifdef _PNETCDF
        if (!mpierr && !delete_called)
            ierr = ncmpi_delete(filename, ios->info);
#endif
#endif
        if (!mpierr)
            mpierr = MPI_Barrier(ios->io_comm);
    }
    LOG((2, "PIOc_deletefile ierr = %d", ierr));

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi2(ios, NULL, mpierr2, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf2(ios, NULL, ierr, __FILE__, __LINE__);

    return ierr;
}

/**
 * PIO interface to nc_sync This routine is called collectively by all
 * tasks in the communicator ios.union_comm.
 *
 * Refer to the <A
 * HREF="http://www.unidata.ucar.edu/software/netcdf/docs/modules.html"
 * target="_blank"> netcdf </A> documentation.
 *
 * @param ncid the ncid of the file to sync.
 * @returns PIO_NOERR for success, error code otherwise.
 */
int PIOc_sync(int ncid)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    wmulti_buffer *wmb, *twmb;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */

    /* Get the file info from the ncid. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_SYNC;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (file->mode & PIO_WRITE)
    {
        LOG((3, "PIOc_sync checking buffers"));
        
        /*  cn_buffer_report( *ios, true); */
        wmb = &file->buffer;
        while (wmb)
        {
            if (wmb->validvars > 0)
                flush_buffer(ncid, wmb, true);
            twmb = wmb;
            wmb = wmb->next;
            if (twmb == &file->buffer)
            {
                twmb->ioid = -1;
                twmb->next = NULL;
            }
            else
            {
                brel(twmb);
            }
        }
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            flush_output_buffer(file, true, 0);

        if (ios->ioproc)
        {
            switch(file->iotype)
            {
#ifdef _NETCDF
#ifdef _NETCDF4
            case PIO_IOTYPE_NETCDF4P:
                ierr = nc_sync(file->fh);
                break;
            case PIO_IOTYPE_NETCDF4C:
#endif
            case PIO_IOTYPE_NETCDF:
                if (ios->io_rank == 0)
                    ierr = nc_sync(file->fh);
                break;
#endif
#ifdef _PNETCDF
            case PIO_IOTYPE_PNETCDF:
                ierr = ncmpi_sync(file->fh);
                break;
#endif
            default:
                return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
            }
        }
        LOG((2, "PIOc_sync ierr = %d", ierr));        
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf2(ios, NULL, ierr, __FILE__, __LINE__);

    return ierr;
}
