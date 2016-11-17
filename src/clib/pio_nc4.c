/** @file
 *
 * Functions to wrap netCDF-4 functions for PIO.
 *
 * @author Ed Hartnett
 */
#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/**
 * @ingroup PIO_def_var
 * Set deflate (zlib) settings for a variable.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable.
 * @param shuffle non-zero to turn on shuffle filter (can be good for
 * integer data).
 * @param deflate non-zero to turn on zlib compression for this
 * variable.
 * @param deflate_level 1 to 9, with 1 being faster and 9 being more
 * compressed.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_def_var_deflate(int ncid, int varid, int shuffle, int deflate,
                         int deflate_level)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
	    int msg = PIO_MSG_DEF_VAR_DEFLATE;

	    if (ios->compmaster)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    if (!mpierr)
		mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
	}

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
#ifdef _NETCDF4	
	if (file->iotype == PIO_IOTYPE_NETCDF4P)
            ierr = NC_EINVAL;
	else
	    if (file->do_io)
                ierr = nc_def_var_deflate(file->fh, varid, shuffle, deflate, deflate_level);
#endif
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return ierr;
}

/**
 * @ingroup PIO_inq_var
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * Inquire about deflate (zlib compression) settings for a variable.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable to set chunksizes for.
 * @param shufflep pointer to an int that will get the status of the
 * shuffle filter.
 * @param deflatep pointer to an int that will be set to non-zero if
 * deflation is in use for this variable.
 * @param deflate_levelp pointer to an int that will get the deflation
 * level (from 1-9) if deflation is in use for this variable.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_inq_var_deflate(int ncid, int varid, int *shufflep,
                         int *deflatep, int *deflate_levelp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int msg;
    char *errstr;
    int ret;

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    msg = PIO_MSG_INQ_VAR_DEFLATE;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {

	    if (ios->compmaster)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    if (!mpierr)
		mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
	}

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
#ifdef _NETCDF4
	if (file->do_io)
            ierr = nc_inq_var_deflate(file->fh, varid, shufflep, deflatep, deflate_levelp);
#endif
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. */
    if (ierr == PIO_NOERR)
    {
        if (shufflep)
            ierr = MPI_Bcast(shufflep, 1, MPI_INT, ios->ioroot, ios->my_comm);
        if (deflatep)
            ierr = MPI_Bcast(deflatep, 1, MPI_INT, ios->ioroot, ios->my_comm);
        if (deflate_levelp)
            ierr = MPI_Bcast(deflate_levelp, 1, MPI_INT, ios->ioroot, ios->my_comm);
    }
    return ierr;
}

/**
 * @ingroup PIO_def_var
 * Set chunksizes for a variable.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * Chunksizes have important performance repercussions. NetCDF
 * attempts to choose sensible chunk sizes by default, but for best
 * performance check chunking against access patterns.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable to set chunksizes for.
 * @param storage NC_CONTIGUOUS or NC_CHUNKED.
 * @param chunksizep an array of chunksizes. Must have a chunksize for
 * every variable dimension.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_def_var_chunking(int ncid, int varid, int storage,
                          const PIO_Offset *chunksizesp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_DEF_VAR_CHUNKING;

            if (ios->compmaster)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
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
#ifdef _NETCDF4
	if (file->do_io)
            ierr = nc_def_var_chunking(file->fh, varid, storage, chunksizesp);
#endif
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return ierr;
}

/**
 * @ingroup PIO_inq_var
 * Inquire about chunksizes for a variable.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable to set chunksizes for.
 * @param storagep pointer to int which will be set to either
 * NC_CONTIGUOUS or NC_CHUNKED.
 * @param chunksizep pointer to memory where chunksizes will be
 * set. There are the same number of chunksizes as there are
 * dimensions.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_inq_var_chunking(int ncid, int varid, int *storagep, PIO_Offset *chunksizesp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int ndims; /* The number of dimensions in the variable. */

    LOG((1, "PIOc_inq_var_chunking ncid = %d varid = %d"));

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* Run these on all tasks if async is not in use, but only on
     * non-IO tasks if async is in use. */
    if (!ios->async_interface || !ios->ioproc)
    {
	/* Find the number of dimensions of this variable. */
	if ((ierr = PIOc_inq_varndims(ncid, varid, &ndims)))
	    return ierr;
	LOG((2, "ndims = %d", ndims));
    }

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
	    int msg = PIO_MSG_INQ_VAR_CHUNKING;

	    if (ios->compmaster)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    if (!mpierr)
		mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
	}

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);

        /* Broadcast values currently only known on computation tasks to IO tasks. */
        if ((mpierr = MPI_Bcast(&ndims, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _NETCDF4
	if (file->do_io)
	    ierr = nc_inq_var_chunking(file->fh, varid, storagep, chunksizesp);
#endif
	LOG((2, "ierr = %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. */
    ierr = MPI_Bcast(&ndims, 1, MPI_INT, ios->ioroot, ios->my_comm);
    if (storagep)
        ierr = MPI_Bcast(storagep, 1, MPI_INT, ios->ioroot, ios->my_comm);
    if (chunksizesp)
        ierr = MPI_Bcast(chunksizesp, ndims, MPI_OFFSET, ios->ioroot, ios->my_comm);

    return ierr;
}

/**
 * @ingroup PIO_def_var
 * Set chunksizes for a variable.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * Chunksizes have important performance repercussions. NetCDF
 * attempts to choose sensible chunk sizes by default, but for best
 * performance check chunking against access patterns.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable to set chunksizes for.
 * @param storage NC_CONTIGUOUS or NC_CHUNKED.
 * @param chunksizep an array of chunksizes. Must have a chunksize for
 * every variable dimension.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_def_var_fill(int ncid, int varid, int no_fill, const void *fill_value)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
	    int msg = PIO_MSG_SET_FILL;

	    if (ios->compmaster)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    if (!mpierr)
		mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
	}

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
#ifdef _NETCDF4
	if (file->do_io)
	    ierr = nc_def_var_fill(file->fh, varid, no_fill, fill_value);
#endif
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return ierr;
}

/**
 * @ingroup PIO_def_var
 * Set chunksizes for a variable.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * Chunksizes have important performance repercussions. NetCDF
 * attempts to choose sensible chunk sizes by default, but for best
 * performance check chunking against access patterns.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable to set chunksizes for.
 * @param storage NC_CONTIGUOUS or NC_CHUNKED.
 * @param chunksizep an array of chunksizes. Must have a chunksize for
 * every variable dimension.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_def_var_endian(int ncid, int varid, int endian)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
	    int msg = PIO_MSG_DEF_VAR_ENDIAN;
	    if (ios->compmaster)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    if (!mpierr)
		mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
	}

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
#ifdef _NETCDF4
	if (file->do_io)
	    ierr = nc_def_var_endian(file->fh, varid, endian);
#endif
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return ierr;
}

/**
 * @ingroup PIO_inq_var
 * Inquire about chunksizes for a variable.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable to set chunksizes for.
 * @param endianp pointer to int which will be set to
 * endianness. Ignored if NULL.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_inq_var_endian(int ncid, int varid, int *endianp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_inq_var_endian ncid = %d varid = %d"));

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
	    int msg = PIO_MSG_INQ_VAR_CHUNKING;

	    if (ios->compmaster)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    if (!mpierr)
		mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
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
#ifdef _NETCDF4
	if (file->do_io)
	    ierr = nc_inq_var_endian(file->fh, varid, endianp);
#endif
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. */
    if (endianp)
        ierr = MPI_Bcast(endianp, 1, MPI_INT, ios->ioroot, ios->my_comm);

    return ierr;
}

/**
 * @ingroup PIO_def_var
 *
 * Set chunk cache netCDF files to be opened/created.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * The file chunk cache for HDF5 can be set, and will apply for any
 * files opened or created until the program ends, or the settings are
 * changed again. The cache settings apply only to the open file. They
 * do not persist with the file, and must be set each time the file is
 * opened, before it is opened, if they are to have effect.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * @param iotype the iotype of files to be created or opened.
 * @param size size of file cache.
 * @param nelems number of elements in file cache.
 * @param preemption preemption setting for file cache.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_set_chunk_cache(int iosysid, int iotype, PIO_Offset size,
                         PIO_Offset nelems, float preemption)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the IO system info. */
    ios = pio_get_iosystem_from_id(iosysid);
    if(ios == NULL)
        return PIO_EBADID;

    /* Only netCDF-4 files can use this feature. */
    if (iotype != PIO_IOTYPE_NETCDF4P && iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    int msg;
    msg = PIO_MSG_SET_CHUNK_CACHE;
    /* if (ios->async_interface && ! ios->ioproc){ */
    /*  if (ios->compmaster) */
    /*      mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm); */
    /*  mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm); */
    /* } */

#ifdef _NETCDF4
    if (iotype == PIO_IOTYPE_NETCDF4P)
        ierr = nc_set_chunk_cache(size, nelems, preemption);
    else
        if (!ios->io_rank)
            ierr = nc_set_chunk_cache(size, nelems, preemption);
#endif

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    return ierr;
}

/**
 * @ingroup PIO_def_var
 * Get current file chunk cache settings from HDF5.
 *
 * This function has no effect on netCDF classic files. Calling this
 * function with iotype of PIO_IOTYPE_PNETCDF or PIO_IOTYPE_NETCDF
 * returns an error.
 *
 * The file chunk cache for HDF5 can be set, and will apply for any
 * files opened or created until the program ends, or the settings are
 * changed again. The cache settings apply only to the open file. They
 * do not persist with the file, and must be set each time the file is
 * opened, before it is opened, if they are to have effect.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * Chunksizes have important performance repercussions. NetCDF
 * attempts to choose sensible chunk sizes by default, but for best
 * performance check chunking against access patterns.
 *
 * @param iotype the iotype of files to be created or opened.
 * @param sizep gets the size of file cache.
 * @param nelemsp gets the number of elements in file cache.
 * @param preemptionp gets the preemption setting for file cache.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_get_chunk_cache(int iosysid, int iotype, PIO_Offset *sizep,
                         PIO_Offset *nelemsp, float *preemptionp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int msg;

    /* Get the io system info. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return PIO_EBADID;

    /* Only netCDF-4 files can use this feature. */
    if (iotype != PIO_IOTYPE_NETCDF4P && iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* Since this is a property of the running HDF5 instance, not the
     * file, it's not clear if this message passing will apply. For
     * now, comment it out. EJH */
    /* msg = PIO_MSG_INQ_VAR_FLETCHER32; */

    /* if (ios->async_interface && ! ios->ioproc){ */
    /*  if (ios->compmaster)  */
    /*      mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm); */
    /*  mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm); */
    /* } */

#ifdef _NETCDF4
    if (iotype == PIO_IOTYPE_NETCDF4P)
        ierr = nc_get_chunk_cache((size_t *)sizep, (size_t *)nelemsp, preemptionp);
    else
        if (!ios->io_rank)
            ierr = nc_get_chunk_cache((size_t *)sizep, (size_t *)nelemsp, preemptionp);
#endif

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    if (!ierr)
    {
        if (sizep)
            if ((ierr = MPI_Bcast(sizep, 1, MPI_OFFSET, ios->ioroot, ios->my_comm)))
                ierr = PIO_EIO;
        if (nelemsp && !ierr)
            if ((ierr = MPI_Bcast(nelemsp, 1, MPI_OFFSET, ios->ioroot, ios->my_comm)))
                ierr = PIO_EIO;
        if (preemptionp && !ierr)
            if ((ierr = MPI_Bcast(preemptionp, 1, MPI_FLOAT, ios->ioroot, ios->my_comm)))
                ierr = PIO_EIO;
    }

    return ierr;
}

/**
 * @ingroup PIO_def_var
 * Set chunksizes for a variable.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * Chunksizes have important performance repercussions. NetCDF
 * attempts to choose sensible chunk sizes by default, but for best
 * performance check chunking against access patterns.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable to set chunksizes for.
 * @param storage NC_CONTIGUOUS or NC_CHUNKED.
 * @param chunksizep an array of chunksizes. Must have a chunksize for
 * every variable dimension.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_set_var_chunk_cache(int ncid, int varid, PIO_Offset size, PIO_Offset nelems,
                             float preemption)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
	    int msg = PIO_MSG_SET_VAR_CHUNK_CACHE;

	    if (ios->compmaster)
		mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

	    if (!mpierr)
		mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm);
	}

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (ios->ioproc)
    {
#ifdef _NETCDF4
	if (file->do_io)
	    ierr = nc_set_var_chunk_cache(file->fh, varid, size, nelems, preemption);
#endif
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return ierr;
}

/**
 * @ingroup PIO_inq_var
 * Get the variable chunk cache settings.
 *
 * This function only applies to netCDF-4 files. When used with netCDF
 * classic files, the error PIO_ENOTNC4 will be returned.
 *
 * Note that these settings are not part of the data file - they apply
 * only to the open file as long as it is open.
 *
 *  See the <a
 * href="http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html">netCDF
 * variable documentation</a> for details about the operation of this
 * function.
 *
 * @param ncid the ncid of the open file.
 * @param varid the ID of the variable to set chunksizes for.
 * @param sizep will get the size of the cache in bytes. Ignored if NULL.
 * @param nelemsp will get the number of elements in the cache. Ignored if NULL.
 * @param preemptionp will get the cache preemption value. Ignored if NULL.
 * @return PIO_NOERR for success, otherwise an error code.
 */
int PIOc_get_var_chunk_cache(int ncid, int varid, PIO_Offset *sizep, PIO_Offset *nelemsp,
                             float *preemptionp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int msg;

    LOG((1, "PIOc_get_var_chunk_cache ncid = %d varid = %d"));

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Only netCDF-4 files can use this feature. */
    if (file->iotype != PIO_IOTYPE_NETCDF4P && file->iotype != PIO_IOTYPE_NETCDF4C)
	return PIO_ENOTNC4;

    /* Since this is a property of the running HDF5 instance, not the
     * file, it's not clear if this message passing will apply. For
     * now, comment it out. EJH */
    /* msg = PIO_MSG_INQ_VAR_FLETCHER32; */

    /* if (ios->async_interface && ! ios->ioproc){ */
    /*  if (ios->compmaster)  */
    /*      mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm); */
    /*  mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm); */
    /* } */

    if (ios->ioproc)
    {
#ifdef _NETCDF4
	if (file->do_io)
	    ierr = nc_get_var_chunk_cache(file->fh, varid, (size_t *)sizep, (size_t *)nelemsp,
					  preemptionp);
#endif
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. */
    if (!ierr)
    {
	if (sizep && !ierr)
	    ierr = MPI_Bcast(sizep, 1, MPI_OFFSET, ios->ioroot, ios->my_comm);
	if (nelemsp && !ierr)
	    ierr = MPI_Bcast(nelemsp, 1, MPI_OFFSET, ios->ioroot, ios->my_comm);
	if (preemptionp && !ierr)
	    ierr = MPI_Bcast(preemptionp, 1, MPI_FLOAT, ios->ioroot, ios->my_comm);
    }

    return ierr;
}
