#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/** Open an existing file using PIO library. This is an internal
 * function. Depending on the value of the retry parameter, a failed
 * open operation will be handled differently. If retry is non-zero,
 * then a failed attempt to open a file with netCDF-4 (serial or
 * parallel), or parallel-netcdf will be followed by an attempt to
 * open the file as a serial classic netCDF file. This is an important
 * feature to some NCAR users. The functionality is exposed to the
 * user as PIOc_openfile() (which does the retry), and PIOc_open()
 * (which does not do the retry).
 *
 * Input parameters are read on comp task 0 and ignored elsewhere.
 *
 * @param iosysid: A defined pio system descriptor (input)
 * @param ncidp: A pio file descriptor (output)
 * @param iotype: A pio output format (input)
 * @param filename: The filename to open
 * @param mode: The netcdf mode for the open operation
 * @param retry: non-zero to automatically retry with netCDF serial
 * classic.
 *
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_openfile
 * @private
 */
int PIOc_openfile_retry(const int iosysid, int *ncidp, int *iotype,
			const char *filename, const int mode, int retry)
{
    iosystem_desc_t *ios;  /** Pointer to io system information. */
    file_desc_t *file;     /** Pointer to file information. */
    int tmp_fh = -1;
    int ierr = PIO_NOERR;  /** Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /** Return code from MPI function codes. */

    LOG((2, "PIOc_openfile_retry iosysid = %d iotype = %d filename = %s mode = %d retry = %d",
	 iosysid, *iotype, filename, mode, retry));

    /* User must provide valid input for these parameters. */
    if (!ncidp || !iotype || !filename)
	return PIO_EINVAL;
    if (*iotype < PIO_IOTYPE_PNETCDF || *iotype > PIO_IOTYPE_NETCDF4P)
	return PIO_ENOMEM;

    /* Get the IO system info from the iosysid. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
    {
	LOG((0, "PIOc_openfile got bad iosysid %d",iosysid));
	return PIO_EBADID;
    }

    /* Allocate space for the file info. */
    if (!(file = (file_desc_t *) malloc(sizeof(*file))))
	return PIO_ENOMEM;

    /* Fill in some file values. */
    file->fh = -1;
    file->iotype = *iotype;
    file->next = NULL;
    file->iosystem = ios;
    file->mode = mode;
    for (int i = 0; i < PIO_MAX_VARS; i++)
    {
	file->varlist[i].record = -1;
	file->varlist[i].ndims = -1;
#ifdef _PNETCDF
	file->varlist[i].request = NULL;
	file->varlist[i].nreqs=0;
#endif
	file->varlist[i].fillbuf = NULL;
	file->varlist[i].iobuf = NULL;
    }

    file->buffer.validvars = 0;
    file->buffer.vid = NULL;
    file->buffer.data = NULL;
    file->buffer.next = NULL;
    file->buffer.frame = NULL;
    file->buffer.fillvalue = NULL;

    /* Set to true if this task should participate in IO (only true for
     * one task with netcdf serial files. */
    if (file->iotype == PIO_IOTYPE_NETCDF4P || file->iotype == PIO_IOTYPE_PNETCDF ||
	ios->io_rank == 0)
	file->do_io = 1;
    else
	file->do_io = 0;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
	int msg = PIO_MSG_OPEN_FILE;
	size_t len = strlen(filename);

	if (!ios->ioproc)
	{
	    /* Send the message to the message handler. */
            if (ios->compmaster)
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
#ifdef _MPISERIAL
	    ierr = nc_open(filename, file->mode, &(file->fh));
#else
	    file->mode = file->mode |  NC_MPIIO;
	    ierr = nc_open_par(filename, file->mode, ios->io_comm, ios->info, &file->fh);
#endif
	    break;

	case PIO_IOTYPE_NETCDF4C:
	    file->mode = file->mode | NC_NETCDF4;
	    // *** Note the INTENTIONAL FALLTHROUGH ***
#endif

	case PIO_IOTYPE_NETCDF:
	    if (ios->io_rank == 0)
		ierr = nc_open(filename, file->mode, &file->fh);
	    break;
#endif

#ifdef _PNETCDF
	case PIO_IOTYPE_PNETCDF:
	    ierr = ncmpi_open(ios->io_comm, filename, file->mode, ios->info, &file->fh);

	    // This should only be done with a file opened to append
	    if (ierr == PIO_NOERR && (file->mode & PIO_WRITE))
	    {
		if(ios->iomaster)
		    LOG((2, "%d Setting IO buffer %ld", __LINE__, PIO_BUFFER_SIZE_LIMIT));
		ierr = ncmpi_buffer_attach(file->fh, PIO_BUFFER_SIZE_LIMIT);
	    }
	    LOG((2, "ncmpi_open(%s) : fd = %d", filename, file->fh));
	    break;
#endif

	default:
	    ierr = iotype_error(file->iotype,__FILE__,__LINE__);
	    break;
	}

	// If we failed to open a file due to an incompatible type of
	// NetCDF, try it once with just plain old basic NetCDF.
	if (retry)
	{
#ifdef _NETCDF
	    if ((ierr == NC_ENOTNC || ierr == NC_EINVAL) && (file->iotype != PIO_IOTYPE_NETCDF))
	    {
		if (ios->iomaster)
		    printf("PIO2 pio_file.c retry NETCDF\n");

		// reset ierr on all tasks
		ierr = PIO_NOERR;

		// reset file markers for NETCDF on all tasks
		file->iotype = PIO_IOTYPE_NETCDF;

		// open netcdf file serially on main task
		if(ios->io_rank==0)
		{
		    ierr = nc_open(filename, file->mode, &(file->fh));
		}
	    }
#endif
	}
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
	return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (!ierr)
    {
	if ((mpierr = MPI_Bcast(&file->mode, 1, MPI_INT, ios->ioroot, ios->union_comm)))
	    return check_mpi(file, mpierr, __FILE__, __LINE__);

	tmp_fh = file->fh;
	if ((mpierr = MPI_Bcast(&tmp_fh, 1, MPI_INT, ios->ioroot, ios->union_comm)))
	    return check_mpi(file, mpierr, __FILE__, __LINE__);

	/* Not io proc - file handle is not set by pnetcdfc */
	if (file->fh == -1)
	    file->fh = tmp_fh;

	*ncidp = file->fh;
	pio_add_to_file_list(file);
    }

    LOG((2, "Opened file %s file->fh = %d ierr = %d", filename, file->fh, ierr));

    return ierr;
}

/** Open an existing file using PIO library.
 *
 * If the open fails, try again as netCDF serial before giving
 * up. Input parameters are read on comp task 0 and ignored elsewhere.
 *
 * @param iosysid : A defined pio system descriptor (input)
 * @param ncidp : A pio file descriptor (output)
 * @param iotype : A pio output format (input)
 * @param filename : The filename to open
 * @param mode : The netcdf mode for the open operation
 *
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_openfile
 */
int PIOc_openfile(const int iosysid, int *ncidp, int *iotype,
		  const char *filename, const int mode)
{
    LOG((1, "PIOc_openfile iosysid = %d iotype = %d filename = %s mode = %d",
	 iosysid, *iotype, filename, mode));

    return PIOc_openfile_retry(iosysid, ncidp, iotype, filename, mode, 1);
}

/** Open an existing file using PIO library.
 *
 * Input parameters are read on comp task 0 and ignored elsewhere.
 *
 * @param iosysid: A defined pio system descriptor
 * @param path: The filename to open
 * @param mode: The netcdf mode for the open operation
 * @param ncidp: pointer to int where ncid will go
 *
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_openfile
 */
int
PIOc_open(int iosysid, const char *path, int mode, int *ncidp)
{
    int iotype;

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

/** Create a new file using pio. Input parameters are read on comp task
 * 0 and ignored elsewhere.
 *
 * @public
 * @ingroup PIO_createfile
 *
 * @param iosysid : A defined pio system descriptor (input)
 * @param ncidp : A pio file descriptor (output)
 * @param iotype : A pio output format (input)
 * @param filename : The filename to open
 * @param mode : The netcdf mode for the open operation
 */

int PIOc_createfile(const int iosysid, int *ncidp, int *iotype,
		    const char filename[], const int mode)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* User must provide valid input for these parameters. */
    if (!ncidp || !iotype || !filename || strlen(filename) > NC_MAX_NAME)
	return PIO_EINVAL;

    LOG((1, "PIOc_createfile iosysid = %d iotype = %d filename = %s mode = %d",
	 iosysid, *iotype, filename, mode));

    /* Get the IO system info from the iosysid. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
	return PIO_EBADID;

    /* Allocate space for the file info. */
    if (!(file = (file_desc_t *)malloc(sizeof(file_desc_t))))
	return PIO_ENOMEM;

    /* Fill in some file values. */
    file->next = NULL;
    file->iosystem = ios;
    file->iotype = *iotype;

    file->buffer.validvars = 0;
    file->buffer.data = NULL;
    file->buffer.next = NULL;
    file->buffer.vid = NULL;
    file->buffer.ioid = -1;
    file->buffer.frame = NULL;
    file->buffer.fillvalue = NULL;

    for(int i = 0; i < PIO_MAX_VARS; i++)
    {
	file->varlist[i].record = -1;
	file->varlist[i].ndims = -1;
#ifdef _PNETCDF
	file->varlist[i].request = NULL;
	file->varlist[i].nreqs=0;
#endif
	file->varlist[i].fillbuf = NULL;
	file->varlist[i].iobuf = NULL;
    }

    file->mode = mode;

    /* Set to true if this task should participate in IO (only true for
     * one task with netcdf serial files. */
    if (file->iotype == PIO_IOTYPE_NETCDF4P || file->iotype == PIO_IOTYPE_PNETCDF ||
	ios->io_rank == 0)
	file->do_io = 1;
    else
	file->do_io = 0;
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
            if (ios->compmaster)
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
	    if (ierr == PIO_NOERR)
	    {
		int oldfill;
		ierr = ncmpi_buffer_attach(file->fh, PIO_BUFFER_SIZE_LIMIT );
		//	ierr = ncmpi_set_fill(file->fh, NC_FILL, &oldfill);
	    }
	    break;
#endif
	default:
	    ierr = iotype_error(file->iotype,__FILE__,__LINE__);
	}
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
	return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (!ierr)
    {
	if ((mpierr = MPI_Bcast(&file->mode, 1, MPI_INT, ios->ioroot, ios->union_comm)))
	    return check_mpi(file, mpierr, __FILE__, __LINE__);

	/* This flag is implied by netcdf create functions but we need
	   to know if its set. */
	file->mode = file->mode | PIO_WRITE;

	if ((mpierr = MPI_Bcast(&file->fh, 1, MPI_INT, ios->ioroot, ios->union_comm)))
	    return check_mpi(file, mpierr, __FILE__, __LINE__);
	LOG((2, "file->fh = %d", file->fh));

	/* Return the ncid to the caller. */
	*ncidp = file->fh;

	/* Add the struct with this files info to the global list of
	 * open files. */
	pio_add_to_file_list(file);
    }

    LOG((2, "Created file %s %d", filename, file->fh));

    return ierr;
}

/** Open a new file using pio. Input parameters are read on comp task
 * 0 and ignored elsewhere.
 *
 * @public
 * @ingroup PIO_create
 *
 * @param iosysid : A defined pio system descriptor (input)
 * @param cmode : The netcdf mode for the create operation
 * @param filename : The filename to open
 * @param ncidp : A pio file descriptor (output)
 *
 * @return 0 for success, error code otherwise.
 */
int
PIOc_create(int iosysid, const char *filename, int cmode, int *ncidp)
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

/** Close a file previously opened with PIO.
 * @ingroup PIO_closefile
 *
 * @param ncid: the file pointer
 */
int PIOc_closefile(int ncid)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_closefile ncid = %d", ncid));

    /* Find the info about this file. */
    if (!(file = pio_get_file_from_id(ncid)))
        return PIO_EBADID;
    ios = file->iosystem;

    /* Sync changes before closing. */
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

	    if(ios->compmaster)
		mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&file->fh, 1, MPI_INT, ios->compmaster, ios->intercomm);
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
	    if(ios->io_rank==0){
		ierr = nc_close(file->fh);
	    }
	    break;
#endif
#ifdef _PNETCDF
	case PIO_IOTYPE_PNETCDF:
	    if((file->mode & PIO_WRITE)){
		ierr = ncmpi_buffer_detach(file->fh);
	    }
	    ierr = ncmpi_close(file->fh);
	    break;
#endif
	default:
	    ierr = iotype_error(file->iotype,__FILE__,__LINE__);
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

/** Delete a file.
 * @ingroup PIO_deletefile
 *
 * @param iosysid : a pio system handle
 * @param filename : a filename
 */
int PIOc_deletefile(const int iosysid, const char filename[])
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int msg = PIO_MSG_DELETE_FILE;
    size_t len;

    /* Get the IO system info from the id. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
	return PIO_EBADID;

    /* If async is in use, send message to IO master task. */
    if (ios->async_interface)
    {
	if (!ios->ioproc)
	{
	    if(ios->comp_rank==0)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    len = strlen(filename);
	    if (!mpierr)
		mpierr = MPI_Bcast(&len, 1, MPI_INT, ios->compmaster, ios->intercomm);
	    if (!mpierr)
		mpierr = MPI_Bcast((void *)filename, len + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
	}
    }

    /* If this is an IO task, then call the netCDF function. The
     * barriers are needed to assure that no task is trying to operate
     * on the file while it is being deleted. */
    if(ios->ioproc){
	MPI_Barrier(ios->io_comm);
#ifdef _NETCDF
	if(ios->io_rank==0)
	    ierr = nc_delete(filename);
#else
#ifdef _PNETCDF
	ierr = ncmpi_delete(filename, ios->info);
#endif
#endif
	MPI_Barrier(ios->io_comm);
    }

    //   Special case - always broadcast the return from the
    MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm);

    return ierr;
}

/**
 * PIO interface to nc_sync This routine is called collectively by all
 * tasks in the communicator ios.union_comm.
 *
 * Refer to the <A
 * HREF="http://www.unidata.ucar.edu/software/netcdf/docs/modules.html"
 * target="_blank"> netcdf </A> documentation.
 */
int PIOc_sync(int ncid)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    wmulti_buffer *wmb, *twmb;

    /* Get the file info from the ncid. */
    if (!(file = pio_get_file_from_id(ncid)))
	return PIO_EBADID;
    ios = file->iosystem;

    /* If async is in use, send message to IO master tasks. */
    if (ios->async_interface)
    {
	if (!ios->ioproc)
	{
	    int msg = PIO_MSG_SYNC;

	    if(ios->comp_rank == 0)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    mpierr = MPI_Bcast(&(file->fh),1, MPI_INT, ios->compmaster, ios->intercomm);
	}
    }

    if (file->mode & PIO_WRITE)
    {
	//  cn_buffer_report( *ios, true);
	wmb = &(file->buffer);
	while(wmb != NULL){
	    //    printf("%s %d %d %d\n",__FILE__,__LINE__,wmb->ioid, wmb->validvars);
	    if(wmb->validvars>0){
		flush_buffer(ncid, wmb, true);
	    }
	    twmb = wmb;
	    wmb = wmb->next;
	    if(twmb == &(file->buffer)){
		twmb->ioid=-1;
		twmb->next=NULL;
	    }else{
		brel(twmb);
	    }
	}
	flush_output_buffer(file, true, 0);

	if(ios->ioproc){
	    switch(file->iotype){
#ifdef _NETCDF
#ifdef _NETCDF4
	    case PIO_IOTYPE_NETCDF4P:
		ierr = nc_sync(file->fh);;
		break;
	    case PIO_IOTYPE_NETCDF4C:
#endif
	    case PIO_IOTYPE_NETCDF:
		if(ios->io_rank==0){
		    ierr = nc_sync(file->fh);;
		}
		break;
#endif
#ifdef _PNETCDF
	    case PIO_IOTYPE_PNETCDF:
		ierr = ncmpi_sync(file->fh);;
		break;
#endif
	    default:
		ierr = iotype_error(file->iotype,__FILE__,__LINE__);
	    }
	}

	ierr = check_netcdf(file, ierr, __FILE__,__LINE__);
    }
    return ierr;
}
