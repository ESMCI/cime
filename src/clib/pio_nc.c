/**
 * @file
 * PIO interfaces to
 * [NetCDF](http://www.unidata.ucar.edu/software/netcdf/docs/modules.html)
 * support functions
 *
 *  This file provides an interface to the
 *  [NetCDF](http://www.unidata.ucar.edu/software/netcdf/docs/modules.html)
 *  support functions.  Each subroutine calls the underlying netcdf or
 *  pnetcdf or netcdf4 functions from the appropriate subset of mpi
 *  tasks (io_comm). Each routine must be called collectively from
 *  union_comm.
 *
 * @author Jim Edwards (jedwards@ucar.edu), Ed Hartnett
 * @date     Feburary 2014, April 2016
 */
#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/**
 * @ingroup PIO_inq
 * The PIO-C interface for the NetCDF function nc_inq.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm. For more information on the underlying
 * NetCDF commmand please read about this function in the NetCDF
 * documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__datasets.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 *
 * @return PIO_NOERR for success, error code otherwise. See
 * PIOc_Set_File_Error_Handling
 */
int PIOc_inq(int ncid, int *ndimsp, int *nvarsp, int *ngattsp, int *unlimdimidp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_inq ncid = %d", ncid));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ; /* Message for async notification. */
            char ndims_present = ndimsp ? true : false;
            char nvars_present = nvarsp ? true : false;
            char ngatts_present = ngattsp ? true : false;
            char unlimdimid_present = unlimdimidp ? true : false;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&ndims_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&nvars_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&ngatts_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&unlimdimid_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            LOG((2, "PIOc_inq ncid = %d ndims_present = %d nvars_present = %d ngatts_present = %d unlimdimid_present = %d",
                 ncid, ndims_present, nvars_present, ngatts_present, unlimdimid_present));
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
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
        {
            LOG((2, "PIOc_inq calling ncmpi_inq unlimdimidp = %d", unlimdimidp));
            ierr = ncmpi_inq(file->fh, ndimsp, nvarsp, ngattsp, unlimdimidp);
            LOG((2, "PIOc_inq called ncmpi_inq"));
            if (unlimdimidp)
                LOG((2, "PIOc_inq returned from ncmpi_inq unlimdimid = %d", *unlimdimidp));
        }
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype == PIO_IOTYPE_NETCDF && file->do_io)
        {
            LOG((2, "PIOc_inq calling classic nc_inq"));
            /* Should not be necessary to do this - nc_inq should
             * handle null pointers. This has been reported as a bug
             * to netCDF developers. */
            int tmp_ndims, tmp_nvars, tmp_ngatts, tmp_unlimdimid;
            LOG((2, "PIOc_inq calling classic nc_inq"));
            ierr = nc_inq(file->fh, &tmp_ndims, &tmp_nvars, &tmp_ngatts, &tmp_unlimdimid);
            LOG((2, "PIOc_inq calling classic nc_inq"));
            if (unlimdimidp)
                LOG((2, "classic tmp_unlimdimid = %d", tmp_unlimdimid));
            if (ndimsp)
                *ndimsp = tmp_ndims;
            if (nvarsp)
                *nvarsp = tmp_nvars;
            if (ngattsp)
                *ngattsp = tmp_ngatts;
            if (unlimdimidp)
                *unlimdimidp = tmp_unlimdimid;
            if (unlimdimidp)
                LOG((2, "classic unlimdimid = %d", *unlimdimidp));
        }
        else if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
        {
            LOG((2, "PIOc_inq calling netcdf-4 nc_inq"));
            ierr = nc_inq(file->fh, ndimsp, nvarsp, ngattsp, unlimdimidp);
        }
#endif /* _NETCDF */
        LOG((2, "PIOc_inq netcdf call returned %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (ndimsp)
        if ((mpierr = MPI_Bcast(ndimsp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    if (nvarsp)
        if ((mpierr = MPI_Bcast(nvarsp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    if (ngattsp)
        if ((mpierr = MPI_Bcast(ngattsp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    if (unlimdimidp)
        if ((mpierr = MPI_Bcast(unlimdimidp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_ndims
 * Find out how many dimensions are defined in the file.
 *
 * @param ncid the ncid of the open file.
 * @param ndimsp a pointer that will get the number of dimensions.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_inq_ndims(int ncid, int *ndimsp)
{
    LOG((1, "PIOc_inq_ndims"));
    return PIOc_inq(ncid, ndimsp, NULL, NULL, NULL);
}

/**
 * @ingroup PIO_inq_nvars
 * Find out how many variables are defined in a file.
 *
 * @param ncid the ncid of the open file.
 * @param nvarsp a pointer that will get the number of variables.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_inq_nvars(int ncid, int *nvarsp)
{
    return PIOc_inq(ncid, NULL, nvarsp, NULL, NULL);
}

/**
 * @ingroup PIO_inq_natts
 * Find out how many global attributes are defined in a file.
 *
 * @param ncid the ncid of the open file.
 * @param nattsp a pointer that will get the number of attributes.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_inq_natts(int ncid, int *ngattsp)
{
    return PIOc_inq(ncid, NULL, NULL, ngattsp, NULL);
}

/**
 * @ingroup PIO_inq_unlimdim
 * Find out the dimension ids of any unlimited dimensions.
 *
 * @param ncid the ncid of the open file.
 * @param nattsp a pointer that will get an array of unlimited
 * dimension IDs.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_inq_unlimdim(int ncid, int *unlimdimidp)
{
    LOG((1, "PIOc_inq_unlimdim ncid = %d unlimdimidp = %d", ncid, unlimdimidp));
    return PIOc_inq(ncid, NULL, NULL, NULL, unlimdimidp);
}

/**
 * @ingroup PIO_typelen
 * Learn the name and size of a type.
 *
 * @param ncid the ncid of the open file.
 * @param xtype the type to learn about
 * @param name pointer that will get the name of the type.
 * @param sizep pointer that will get the size of the type in bytes.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_inq_type(int ncid, nc_type xtype, char *name, PIO_Offset *sizep)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_inq_type ncid = %d xtype = %d", ncid, xtype));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_TYPE; /* Message for async notification. */
            char name_present = name ? true : false;
            char size_present = sizep ? true : false;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&xtype, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&name_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&size_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
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
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = pioc_pnetcdf_inq_type(ncid, xtype, name, sizep);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_inq_type(file->fh, xtype, name, (size_t *)sizep);
#endif /* _NETCDF */
        LOG((2, "PIOc_inq_type netcdf call returned %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (name)
    {
        int slen;
        if (ios->iomaster == MPI_ROOT)
            slen = strlen(name);
        if ((mpierr = MPI_Bcast(&slen, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        if (!mpierr)
            if ((mpierr = MPI_Bcast((void *)name, slen + 1, MPI_CHAR, ios->ioroot, ios->my_comm)))
                return check_mpi(file, mpierr, __FILE__, __LINE__);
    }
    if (sizep)
        if ((mpierr = MPI_Bcast(sizep , 1, MPI_OFFSET, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_format
 * Learn the netCDF format of an open file.
 *
 * @param ncid the ncid of an open file.
 * @param formatp a pointer that will get the format.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_inq_format(int ncid, int *formatp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_inq ncid = %d", ncid));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_FORMAT;
            char format_present = formatp ? true : false;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&format_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
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
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_inq_format(file->fh, formatp);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_inq_format(file->fh, formatp);
#endif /* _NETCDF */
        LOG((2, "PIOc_inq netcdf call returned %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (formatp)
        if ((mpierr = MPI_Bcast(formatp , 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_dim
 * The PIO-C interface for the NetCDF function nc_inq_dim.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__dimensions.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param lenp a pointer that will get the number of values
 * @return PIO_NOERR for success, error code otherwise.  See PIOc_Set_File_Error_Handling
 */
int PIOc_inq_dim(int ncid, int dimid, char *name, PIO_Offset *lenp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_inq_dim ncid = %d dimid = %d", ncid, dimid));

    /* Get the file info, based on the ncid. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_DIM;
            char name_present = name ? true : false;
            char len_present = lenp ? true : false;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&dimid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&name_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            LOG((2, "PIOc_inq netcdf Bcast name_present = %d", name_present));
            if (!mpierr)
                mpierr = MPI_Bcast(&len_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            LOG((2, "PIOc_inq netcdf Bcast len_present = %d", len_present));
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
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
        {
            LOG((2, "calling ncmpi_inq_dim"));
            ierr = ncmpi_inq_dim(file->fh, dimid, name, lenp);;
        }
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
        {
            LOG((2, "calling nc_inq_dim"));
            ierr = nc_inq_dim(file->fh, dimid, name, (size_t *)lenp);;
        }
#endif /* _NETCDF */
        LOG((2, "ierr = %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (name)
    {
        int slen;
        LOG((2, "bcasting results my_comm = %d", ios->my_comm));
        if (ios->iomaster == MPI_ROOT)
            slen = strlen(name);
        if ((mpierr = MPI_Bcast(&slen, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        if ((mpierr = MPI_Bcast((void *)name, slen + 1, MPI_CHAR, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    if (lenp)
        if ((mpierr = MPI_Bcast(lenp , 1, MPI_OFFSET, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    LOG((2, "done with PIOc_inq_dim"));
    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_dimname
 * Find the name of a dimension.
 *
 * @param ncid the ncid of an open file.
 * @param dimid the dimension ID.
 * @param name a pointer that gets the name of the dimension. Igorned
 * if NULL.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_inq_dimname(int ncid, int dimid, char *name)
{
    LOG((1, "PIOc_inq_dimname ncid = %d dimid = %d", ncid, dimid));
    return PIOc_inq_dim(ncid, dimid, name, NULL);
}

/**
 * @ingroup PIO_inq_dimlen
 * Find the length of a dimension.
 *
 * @param ncid the ncid of an open file.
 * @param dimid the dimension ID.
 * @param lenp a pointer that gets the length of the dimension. Igorned
 * if NULL.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_inq_dimlen(int ncid, int dimid, PIO_Offset *lenp)
{
    return PIOc_inq_dim(ncid, dimid, NULL, lenp);
}

/**
 * @ingroup PIO_inq_dimid
 * The PIO-C interface for the NetCDF function nc_inq_dimid.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__dimensions.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param idp a pointer that will get the id of the variable or attribute.
 * @return PIO_NOERR for success, error code otherwise.  See PIOc_Set_File_Error_Handling
 */
int PIOc_inq_dimid(int ncid, const char *name, int *idp)
{
    iosystem_desc_t *ios;
    file_desc_t *file;
    int ierr;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the file info, based on the ncid. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;
    LOG((2, "iosysid = %d", ios->iosysid));

    /* User must provide name shorter than NC_MAX_NAME +1. */
    if (!name || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_inq_dimid ncid = %d name = %s", ncid, name));

    /* If using async, and not an IO task, then send parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_DIMID;
            char id_present = idp ? true : false;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            int namelen = strlen(name);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&id_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* IO tasks call the netCDF functions. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_inq_dimid(file->fh, name, idp);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_inq_dimid(file->fh, name, idp);
#endif /* _NETCDF */
    }
    LOG((3, "nc_inq_dimid call complete ierr = %d", ierr));

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results. */
    if (idp)
        if ((mpierr = MPI_Bcast(idp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_var
 * The PIO-C interface for the NetCDF function nc_inq_var.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param xtypep a pointer that will get the type of the attribute.
 * @param nattsp a pointer that will get the number of attributes
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_var(int ncid, int varid, char *name, nc_type *xtypep, int *ndimsp,
                 int *dimidsp, int *nattsp)
{
    iosystem_desc_t *ios;
    file_desc_t *file;
    int ndims;    /* The number of dimensions for this variable. */
    int ierr;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_inq_var ncid = %d varid = %d", ncid, varid));

    /* Get the file info, based on the ncid. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;
    LOG((2, "got file and iosystem"));

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_VAR;
            char name_present = name ? true : false;
            char xtype_present = xtypep ? true : false;
            char ndims_present = ndimsp ? true : false;
            char dimids_present = dimidsp ? true : false;
            char natts_present = nattsp ? true : false;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&name_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&xtype_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&ndims_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&dimids_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&natts_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            LOG((2, "PIOc_inq_var name_present = %d xtype_present = %d ndims_present = %d "
                 "dimids_present = %d, natts_present = %d nattsp = %d",
                 name_present, xtype_present, ndims_present, dimids_present, natts_present, nattsp));
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* Call the netCDF layer. */
    if (ios->ioproc)
    {
        LOG((2, "Calling the netCDF layer"));
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
        {
            ierr = ncmpi_inq_varndims(file->fh, varid, &ndims);
            LOG((2, "from pnetcdf ndims = %d", ndims));
            if (!ierr)
                ierr = ncmpi_inq_var(file->fh, varid, name, xtypep, ndimsp, dimidsp, nattsp);
        }
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
        {
            ierr = nc_inq_varndims(file->fh, varid, &ndims);
            char my_name[NC_MAX_NAME + 1];
            nc_type my_xtype;
            int my_ndims, my_dimids[ndims], my_natts;
            LOG((2, "file->fh = %d varid = %d xtypep = %d ndimsp = %d dimidsp = %d nattsp = %d",
                 file->fh, varid, xtypep, ndimsp, dimidsp, nattsp));
            if (!ierr)
                ierr = nc_inq_var(file->fh, varid, my_name, &my_xtype, &my_ndims, my_dimids, &my_natts);
            LOG((3, "my_name = %s my_xtype = %d my_ndims = %d my_natts = %d",  my_name, my_xtype, my_ndims, my_natts));
            if (name)
                strcpy(name, my_name);
            if (xtypep)
                *xtypep = my_xtype;
            if (ndimsp)
                *ndimsp = my_ndims;
            if (dimidsp)
                for (int d = 0; d < ndims; d++)
                    dimidsp[d] = my_dimids[d];
            if (nattsp)
                *nattsp = my_natts;
        }
#endif /* _NETCDF */
        if (ndimsp)
            LOG((2, "PIOc_inq_var ndims = %d ierr = %d", *ndimsp, ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast the results for non-null pointers. */
    if (name)
    {
        int slen;
        if (ios->iomaster == MPI_ROOT)
            slen = strlen(name);
        if ((mpierr = MPI_Bcast(&slen, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        if ((mpierr = MPI_Bcast((void *)name, slen + 1, MPI_CHAR, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }
    if (xtypep)
        if ((mpierr = MPI_Bcast(xtypep, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    if (ndimsp)
    {
        if (ios->ioroot)
            LOG((2, "PIOc_inq_var about to Bcast ndims = %d ios->ioroot = %d", *ndimsp, ios->ioroot));
        if ((mpierr = MPI_Bcast(ndimsp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        file->varlist[varid].ndims = *ndimsp;
        LOG((2, "PIOc_inq_var Bcast ndims = %d", *ndimsp));
    }
    if (dimidsp)
    {
        if ((mpierr = MPI_Bcast(&ndims, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        if ((mpierr = MPI_Bcast(dimidsp, ndims, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }
    if (nattsp)
        if ((mpierr = MPI_Bcast(nattsp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_varname
 * Get the name of a variable.
 *
 * @param ncid the ncid of the open file.
 * @param varid the variable ID.
 * @param name a pointer that will get the variable name.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_varname(int ncid, int varid, char *name)
{
    return PIOc_inq_var(ncid, varid, name, NULL, NULL, NULL, NULL);
}

/**
 * @ingroup PIO_inq_vartype
 * Find the type of a variable.
 *
 * @param ncid the ncid of the open file.
 * @param varid the variable ID.
 * @param xtypep a pointer that will get the type of the
 * attribute. Ignored if NULL.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_vartype(int ncid, int varid, nc_type *xtypep)
{
    return PIOc_inq_var(ncid, varid, NULL, xtypep, NULL, NULL, NULL);
}

/**
 * @ingroup PIO_inq_varndims
 * Find the number of dimensions of a variable.
 *
 * @param ncid the ncid of the open file.
 * @param varid the variable ID.
 * @param ndimsp a pointer that will get the number of
 * dimensions. Ignored if NULL.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_varndims(int ncid, int varid, int *ndimsp)
{
    return PIOc_inq_var(ncid, varid, NULL, NULL, ndimsp, NULL, NULL);
}

/**
 * @ingroup PIO_inq_vardimid
 * Find the dimension IDs associated with a variable.
 *
 * @param ncid the ncid of the open file.
 * @param varid the variable ID.
 * @param dimidsp a pointer that will get an array of dimids. Ignored
 * if NULL.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_vardimid(int ncid, int varid, int *dimidsp)
{
    return PIOc_inq_var(ncid, varid, NULL, NULL, NULL, dimidsp, NULL);
}

/**
 * @ingroup PIO_inq_varnatts
 * Find the number of attributes associated with a variable.
 *
 * @param ncid the ncid of the open file.
 * @param varid the variable ID.
 * @param nattsp a pointer that will get the number of attriburtes. Ignored
 * if NULL.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_varnatts(int ncid, int varid, int *nattsp)
{
    return PIOc_inq_var(ncid, varid, NULL, NULL, NULL, NULL, nattsp);
}

/**
 * @ingroup PIO_inq_varid
 * The PIO-C interface for the NetCDF function nc_inq_varid.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param varidp a pointer that will get the variable id
 * @return PIO_NOERR for success, error code otherwise.  See PIOc_Set_File_Error_Handling
 */
int PIOc_inq_varid(int ncid, const char *name, int *varidp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get file info based on ncid. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* Caller must provide name. */
    if (!name || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_inq_varid ncid = %d name = %s", ncid, name));

    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_VARID;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            int namelen;
            namelen = strlen(name);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_inq_varid(file->fh, name, varidp);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_inq_varid(file->fh, name, varidp);
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (varidp)
        if ((mpierr = MPI_Bcast(varidp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_att
 * The PIO-C interface for the NetCDF function nc_inq_att.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__attributes.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param xtypep a pointer that will get the type of the attribute.
 * @param lenp a pointer that will get the number of values
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_att(int ncid, int varid, const char *name, nc_type *xtypep,
                 PIO_Offset *lenp)
{
    int msg = PIO_MSG_INQ_ATT;
    iosystem_desc_t *ios;
    file_desc_t *file;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int ierr;

    /* Find file based on ncid. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide name shorter than NC_MAX_NAME +1. */
    if (!name || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_inq_att ncid = %d varid = %d xtpyep = %d lenp = %d",
         ncid, varid, xtypep, lenp));

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            char xtype_present = xtypep ? true : false;
            char len_present = lenp ? true : false;
            int namelen = strlen(name);

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&xtype_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&len_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_inq_att(file->fh, varid, name, xtypep, lenp);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_inq_att(file->fh, varid, name, xtypep, (size_t *)lenp);
#endif /* _NETCDF */
        LOG((2, "PIOc_inq netcdf call returned %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results. */
    if (xtypep)
        if ((mpierr = MPI_Bcast(xtypep, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);
    if (lenp)
        if ((mpierr = MPI_Bcast(lenp, 1, MPI_OFFSET, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_attlen
 * Get the length of an attribute.
 *
 * @param ncid the ID of an open file.
 * @param varid the variable ID, or NC_GLOBAL for global attributes.
 * @param name the name of the attribute.
 * @param lenp a pointer that gets the lenght of the attribute
 * array. Ignored if NULL.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_attlen(int ncid, int varid, const char *name, PIO_Offset *lenp)
{
    return PIOc_inq_att(ncid, varid, name, NULL, lenp);
}

/**
 * @ingroup PIO_inq_atttype
 * Get the type of an attribute.
 *
 * @param ncid the ID of an open file.
 * @param varid the variable ID, or NC_GLOBAL for global attributes.
 * @param name the name of the attribute.
 * @param xtypep a pointer that gets the type of the
 * attribute. Ignored if NULL.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_inq_atttype(int ncid, int varid, const char *name, nc_type *xtypep)
{
    return PIOc_inq_att(ncid, varid, name, xtypep, NULL);
}

/**
 * @ingroup PIO_inq_attname
 * The PIO-C interface for the NetCDF function nc_inq_attname.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__attributes.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param attnum the attribute ID.
 * @return PIO_NOERR for success, error code otherwise.  See PIOc_Set_File_Error_Handling
 */
int PIOc_inq_attname(int ncid, int varid, int attnum, char *name)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_inq_attname ncid = %d varid = %d attnum = %d", ncid, varid,
         attnum));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_ATTNAME;
            char name_present = name ? true : false;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&attnum, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&name_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_inq_attname(file->fh, varid, attnum, name);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_inq_attname(file->fh, varid, attnum, name);
#endif /* _NETCDF */
        LOG((2, "PIOc_inq_attname netcdf call returned %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (name)
    {
        int namelen = strlen(name);
        if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);
        /* Casting to void to avoid warnings on some compilers. */
        if ((mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_attid
 * The PIO-C interface for the NetCDF function nc_inq_attid.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__attributes.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param idp a pointer that will get the id of the variable or attribute.
 * @return PIO_NOERR for success, error code otherwise.  See PIOc_Set_File_Error_Handling
 */
int PIOc_inq_attid(int ncid, int varid, const char *name, int *idp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide name shorter than NC_MAX_NAME +1. */
    if (!name || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_inq_attid ncid = %d varid = %d name = %s", ncid, varid, name));

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_ATTID;
            int namelen = strlen(name);
            char id_present = idp ? true : false;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((char *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&id_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_inq_attid(file->fh, varid, name, idp);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_inq_attid(file->fh, varid, name, idp);
#endif /* _NETCDF */
        LOG((2, "PIOc_inq_attname netcdf call returned %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results. */
    if (idp)
        if ((mpierr = MPI_Bcast(idp, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_rename_dim
 * The PIO-C interface for the NetCDF function nc_rename_dim.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__dimensions.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @return PIO_NOERR for success, error code otherwise.  See PIOc_Set_File_Error_Handling
 */
int PIOc_rename_dim(int ncid, int dimid, const char *name)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide name shorter than NC_MAX_NAME +1. */
    if (!name || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_rename_dim ncid = %d dimid = %d name = %s", ncid, dimid, name));

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_RENAME_DIM; /* Message for async notification. */
            int namelen = strlen(name);

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&dimid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            LOG((2, "PIOc_rename_dim Bcast file->fh = %d dimid = %d namelen = %d name = %s",
                 file->fh, dimid, namelen, name));
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }


    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_rename_dim(file->fh, dimid, name);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_rename_dim(file->fh, dimid, name);
#endif /* _NETCDF */
        LOG((2, "PIOc_inq netcdf call returned %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_rename_var
 * The PIO-C interface for the NetCDF function nc_rename_var.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @return PIO_NOERR for success, error code otherwise.  See PIOc_Set_File_Error_Handling
 */
int PIOc_rename_var(int ncid, int varid, const char *name)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide name shorter than NC_MAX_NAME +1. */
    if (!name || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_rename_var ncid = %d varid = %d name = %s", ncid, varid, name));

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_RENAME_VAR; /* Message for async notification. */
            int namelen = strlen(name);

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            LOG((2, "PIOc_rename_var Bcast file->fh = %d varid = %d namelen = %d name = %s",
                 file->fh, varid, namelen, name));
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }


    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_rename_var(file->fh, varid, name);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_rename_var(file->fh, varid, name);
#endif /* _NETCDF */
        LOG((2, "PIOc_inq netcdf call returned %d", ierr));
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_rename_att
 * The PIO-C interface for the NetCDF function nc_rename_att.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__attributes.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @return PIO_NOERR for success, error code otherwise.  See
 * PIOc_Set_File_Error_Handling
 */
int PIOc_rename_att(int ncid, int varid, const char *name,
                    const char *newname)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI functions. */

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide names of correct length. */
    if (!name || strlen(name) > NC_MAX_NAME ||
        !newname || strlen(newname) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_rename_att ncid = %d varid = %d name = %s newname = %s",
         ncid, varid, name, newname));

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_RENAME_ATT; /* Message for async notification. */
            int namelen = strlen(name);
            int newnamelen = strlen(newname);

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((char *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&newnamelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((char *)newname, newnamelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_rename_att(file->fh, varid, name, newname);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_rename_att(file->fh, varid, name, newname);
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    LOG((2, "PIOc_rename_att succeeded"));
    return PIO_NOERR;
}

/**
 * @ingroup PIO_del_att
 * The PIO-C interface for the NetCDF function nc_del_att.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__attributes.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name of the attribute to delete.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_del_att(int ncid, int varid, const char *name)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI functions. */

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide name shorter than NC_MAX_NAME +1. */
    if (!name || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_del_att ncid = %d varid = %d name = %s", ncid, varid, name));

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_DEL_ATT;
            int namelen = strlen(name); /* Length of name string. */

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((char *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_del_att(file->fh, varid, name);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_del_att(file->fh, varid, name);
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_set_fill
 * The PIO-C interface for the NetCDF function nc_set_fill.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__datasets.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_set_fill(int ncid, int fillmode, int *old_modep)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI functions. */

    LOG((1, "PIOc_set_fill ncid = %d fillmode = %d old_modep = %d", ncid, fillmode,
         old_modep));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_SET_FILL;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_set_fill(file->fh, fillmode, old_modep);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_set_fill(file->fh, fillmode, old_modep);
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    LOG((2, "PIOc_set_fill succeeded"));
    return PIO_NOERR;
}

/**
 * @ingroup PIO_enddef
 * The PIO-C interface for the NetCDF function nc_enddef.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__datasets.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_enddef(int ncid)
{
    return pioc_change_def(ncid, 1);
}

/**
 * @ingroup PIO_redef
 * The PIO-C interface for the NetCDF function nc_redef.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__datasets.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_redef(int ncid)
{
    return pioc_change_def(ncid, 0);
}

/**
 * @ingroup PIO_def_dim
 * The PIO-C interface for the NetCDF function nc_def_dim.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__dimensions.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param idp a pointer that will get the id of the variable or attribute.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_def_dim(int ncid, const char *name, PIO_Offset len, int *idp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide name shorter than NC_MAX_NAME +1. */
    if (!name || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_def_dim ncid = %d name = %s len = %d", ncid, name, len));

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_DEF_DIM;
            int namelen = strlen(name);

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);

            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&len, 1, MPI_INT,  ios->compmaster, ios->intercomm);
        }


        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_def_dim(file->fh, name, len, idp);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_def_dim(file->fh, name, (size_t)len, idp);
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (idp)
        if ((mpierr = MPI_Bcast(idp , 1, MPI_INT, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);

    LOG((2, "def_dim ierr = %d", ierr));
    return PIO_NOERR;
}

/**
 * The PIO-C interface for the NetCDF function nc_def_var.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param varidp a pointer that will get the variable id
 * @return PIO_NOERR for success, error code otherwise.
 * @ingroup PIO_def_var
 */
int PIOc_def_var(int ncid, const char *name, nc_type xtype, int ndims,
                 const int *dimidsp, int *varidp)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    /* Get the file information. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide name and storage for varid. */
    if (!name || !varidp || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_def_var ncid = %d name = %s xtype = %d ndims = %d", ncid, name,
         xtype, ndims));

    /* If using async, and not an IO task, then send parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_DEF_VAR;
            int namelen = strlen(name);

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&(ncid), 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&xtype, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&ndims, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)dimidsp, ndims, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_def_var(file->fh, name, xtype, ndims, dimidsp, varidp);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_def_var(file->fh, name, xtype, ndims, dimidsp, varidp);
#ifdef _NETCDF4
        /* For netCDF-4 serial files, turn on compression for this variable. */
        if (!ierr && file->iotype == PIO_IOTYPE_NETCDF4C)
            ierr = nc_def_var_deflate(file->fh, *varidp, 0, 1, 1);

        /* For netCDF-4 parallel files, set parallel access to collective. */
        if (!ierr && file->iotype == PIO_IOTYPE_NETCDF4P)
            ierr = nc_var_par_access(file->fh, *varidp, NC_COLLECTIVE);
#endif /* _NETCDF4 */
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results. */
    if (varidp)
        if ((mpierr = MPI_Bcast(varidp , 1, MPI_INT, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_inq_var_fill
 * The PIO-C interface for the NetCDF function nc_inq_var_fill.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm. For more information on the underlying NetCDF commmand
 * please read about this function in the NetCDF documentation at:
 * http://www.unidata.ucar.edu/software/netcdf/docs/group__variables.html
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @return PIO_NOERR for success, error code otherwise.  See PIOc_Set_File_Error_Handling
 */
int PIOc_inq_var_fill(int ncid, int varid, int *no_fill, void *fill_valuep)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_inq ncid = %d", ncid));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_INQ_VAR_FILL;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_inq_var_fill(file->fh, varid, no_fill, fill_valuep);
#endif /* _PNETCDF */
#ifdef _NETCDF4
        /* The inq_var_fill is not supported in classic-only builds. */
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_inq_var_fill(file->fh, varid, no_fill, fill_valuep);
#else
        ierr = PIO_ENOTNC4;
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if (fill_valuep)
        if ((mpierr = MPI_Bcast(fill_valuep, 1, MPI_INT, ios->ioroot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_get_att
 * Get the value of an attribute of any type.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att(int ncid, int varid, const char *name, void *ip)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr;              /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    PIO_Offset attlen, typelen;
    nc_type atttype;

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide a name and destination pointer. */
    if (!name || !ip || strlen(name) > NC_MAX_NAME)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_get_att ncid %d varid %d name %s", ncid, varid, name));

    /* Run these on all tasks if async is not in use, but only on
     * non-IO tasks if async is in use. */
    if (!ios->async_interface || !ios->ioproc)
    {
        /* Get the type and length of the attribute. */
        if ((ierr = PIOc_inq_att(ncid, varid, name, &atttype, &attlen)))
            return check_netcdf(file, ierr, __FILE__, __LINE__);
        LOG((2, "atttype = %d attlen = %d", atttype, attlen));

        /* Get the length (in bytes) of the type. */
        if ((ierr = PIOc_inq_type(ncid, atttype, NULL, &typelen)))
            return check_netcdf(file, ierr, __FILE__, __LINE__);
        LOG((2, "typelen = %d", typelen));
    }
    LOG((2, "again typelen = %d", typelen));

    /* If async is in use, and this is not an IO task, bcast the
     * parameters and the attribute and type information we fetched. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_GET_ATT;
            LOG((2, "sending parameters"));

            /* Send the message to IO master. */
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            /* Send the function parameters. */
            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            int namelen = strlen(name);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&file->iotype, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&atttype, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&attlen, 1, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, ios->compmaster, ios->intercomm);
            LOG((2, "Bcast complete ncid = %d varid = %d namelen = %d name = %s iotype = %d "
                 "atttype = %d attlen = %d typelen = %d", ncid, varid, namelen, name, file->iotype,
                 atttype, attlen, typelen));
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        LOG((2, "mpi errors handled"));

        /* Broadcast values currently only known on computation tasks to IO tasks. */
        LOG((2, "PIOc_get_att bcast from comproot = %d attlen = %d typelen = %d", ios->comproot, attlen, typelen));
        if ((mpierr = MPI_Bcast(&attlen, 1, MPI_OFFSET, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        if ((mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        LOG((2, "PIOc_get_att bcast complete attlen = %d typelen = %d", attlen, typelen));
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
        LOG((2, "calling pnetcdf/netcdf"));
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_get_att(file->fh, varid, name, ip);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_get_att(file->fh, varid, name, ip);
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    LOG((2, "ierr = %d", ierr));
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Broadcast results to all tasks. */
    if ((mpierr = MPI_Bcast(ip, (int)attlen * typelen, MPI_BYTE, ios->ioroot,
                            ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    LOG((2, "get_att data bcast complete"));
    return PIO_NOERR;
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute of any type.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att(int ncid, int varid, const char *name, nc_type xtype,
                 PIO_Offset len, const void *op)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    PIO_Offset typelen; /* Length (in bytes) of the type. */
    int ierr;           /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_put_att ncid = %d varid = %d name = %s", ncid, varid, name));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* Run these on all tasks if async is not in use, but only on
     * non-IO tasks if async is in use. */
    if (!ios->async_interface || !ios->ioproc)
    {
        /* Get the length (in bytes) of the type. */
        if ((ierr = PIOc_inq_type(ncid, xtype, NULL, &typelen)))
            return check_netcdf(file, ierr, __FILE__, __LINE__);
        LOG((2, "PIOc_put_att typelen = %d", ncid, typelen));
    }

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_PUT_ATT;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            int namelen = strlen(name);
            if (!mpierr)
                mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&xtype, 1, MPI_INT,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&len, 1, MPI_OFFSET,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET,  ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)op, len * typelen, MPI_BYTE, ios->compmaster,
                                   ios->intercomm);
            LOG((2, "PIOc_put_att finished bcast ncid = %d varid = %d namelen = %d name = %s "
                 "len = %d typelen = %d", ncid, varid, namelen, name, len, typelen));
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);

        /* Broadcast values currently only known on computation tasks to IO tasks. */
        LOG((2, "PIOc_put_att bcast from comproot = %d typelen = %d", ios->comproot, typelen));
        if ((mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            ierr = ncmpi_put_att(file->fh, varid, name, xtype, len, op);
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            ierr = nc_put_att(file->fh, varid, name, xtype, (size_t)len, op);
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 64-bit floating point array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_double(int ncid, int varid, const char *name, double *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 8-bit unsigned char array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_uchar(int ncid, int varid, const char *name, unsigned char *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 16-bit unsigned integer array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_ushort(int ncid, int varid, const char *name, unsigned short *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * Get the value of an 32-bit unsigned integer array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 * @ingroup PIO_get_att
 */
int PIOc_get_att_uint(int ncid, int varid, const char *name, unsigned int *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 32-bit ingeger array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_long(int ncid, int varid, const char *name, long *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 8-bit unsigned byte array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_ubyte(int ncid, int varid, const char *name, unsigned char *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an text attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_text(int ncid, int varid, const char *name, char *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 8-bit signed char array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_schar(int ncid, int varid, const char *name, signed char *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 64-bit unsigned integer array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_ulonglong(int ncid, int varid, const char *name, unsigned long long *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 16-bit integer array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_short(int ncid, int varid, const char *name, short *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 32-bit integer array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_int(int ncid, int varid, const char *name, int *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 64-bit integer array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_longlong(int ncid, int varid, const char *name, long long *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_get_att
 * Get the value of an 32-bit floating point array attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute to get
 * @param ip a pointer that will get the attribute value.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_get_att_float(int ncid, int varid, const char *name, float *ip)
{
    return PIOc_get_att(ncid, varid, name, (void *)ip);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 8-bit signed chars.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_schar(int ncid, int varid, const char *name, nc_type xtype,
                       PIO_Offset len, const signed char *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 32-bit signed integers.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_long(int ncid, int varid, const char *name, nc_type xtype,
                      PIO_Offset len, const long *op)
{
    return PIOc_put_att(ncid, varid, name, NC_CHAR, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 32-bit signed integers.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_int(int ncid, int varid, const char *name, nc_type xtype,
                     PIO_Offset len, const int *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 8-bit unsigned chars.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_uchar(int ncid, int varid, const char *name, nc_type xtype,
                       PIO_Offset len, const unsigned char *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 64-bit signed integers.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_longlong(int ncid, int varid, const char *name, nc_type xtype,
                          PIO_Offset len, const long long *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 32-bit unsigned integers.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_uint(int ncid, int varid, const char *name, nc_type xtype,
                      PIO_Offset len, const unsigned int *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 8-bit unsigned bytes.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_ubyte(int ncid, int varid, const char *name, nc_type xtype,
                       PIO_Offset len, const unsigned char *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 32-bit floating points.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_float(int ncid, int varid, const char *name, nc_type xtype,
                       PIO_Offset len, const float *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 64-bit unsigned integers.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_ulonglong(int ncid, int varid, const char *name, nc_type xtype,
                           PIO_Offset len, const unsigned long long *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 16-bit unsigned integers.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_ushort(int ncid, int varid, const char *name, nc_type xtype,
                        PIO_Offset len, const unsigned short *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF text attribute.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_text(int ncid, int varid, const char *name,
                      PIO_Offset len, const char *op)
{
    return PIOc_put_att(ncid, varid, name, NC_CHAR, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 16-bit integers.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_short(int ncid, int varid, const char *name, nc_type xtype,
                       PIO_Offset len, const short *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}

/**
 * @ingroup PIO_put_att
 * Write a netCDF attribute array of 64-bit floating points.
 *
 * This routine is called collectively by all tasks in the communicator
 * ios.union_comm.
 *
 * @param ncid the ncid of the open file, obtained from
 * PIOc_openfile() or PIOc_createfile().
 * @param varid the variable ID.
 * @param name the name of the attribute.
 * @param xtype the nc_type of the attribute.
 * @param len the length of the attribute array.
 * @param op a pointer with the attribute data.
 * @return PIO_NOERR for success, error code otherwise.
 */
int PIOc_put_att_double(int ncid, int varid, const char *name, nc_type xtype,
                        PIO_Offset len, const double *op)
{
    return PIOc_put_att(ncid, varid, name, xtype, len, op);
}
