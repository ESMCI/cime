/**
 * @file
 * Internal PIO functions to get and put data (excluding varm
 * functions).
 *
 * @author Ed Hartnett
 * @date  2016
 *
 * @see http://code.google.com/p/parallelio/
 */

#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/**
 * Internal PIO function which provides a type-neutral interface to
 * nc_get_vars.
 *
 * Users should not call this function directly. Instead, call one of
 * the derived functions, depending on the type of data you are
 * reading: PIOc_get_vars_text(), PIOc_get_vars_uchar(),
 * PIOc_get_vars_schar(), PIOc_get_vars_ushort(),
 * PIOc_get_vars_short(), PIOc_get_vars_uint(), PIOc_get_vars_int(),
 * PIOc_get_vars_long(), PIOc_get_vars_float(),
 * PIOc_get_vars_double(), PIOc_get_vars_ulonglong(),
 * PIOc_get_vars_longlong()
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param xtype the netCDF type of the data being passed in buf. Data
 * will be automatically covnerted from the type of the variable being
 * read from to this type.
 * @param buf pointer to the data to be written.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_vars_tc(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                     const PIO_Offset *stride, nc_type xtype, void *buf)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int ndims;   /* The number of dimensions in the variable. */
    PIO_Offset typelen; /* Size (in bytes) of the data type of data in buf. */
    PIO_Offset num_elem = 1; /* Number of data elements in the buffer. */
    char start_present = start ? true : false;
    char count_present = count ? true : false;
    char stride_present = stride ? true : false;
    PIO_Offset *rstart = NULL, *rcount = NULL;

    LOG((1, "PIOc_get_vars_tc ncid = %d varid = %d start = %d count = %d "
         "stride = %d xtype = %d", ncid, varid, start, count, stride, xtype));

    /* Find the info about this file. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide a place to put some data. */
    if (!buf)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);        

    /* Run these on all tasks if async is not in use, but only on
     * non-IO tasks if async is in use. */
    if (!ios->async_interface || !ios->ioproc)
    {
        /* Get the length of the data type. */
        if ((ierr = PIOc_inq_type(ncid, xtype, NULL, &typelen)))
            return check_netcdf(file, ierr, __FILE__, __LINE__);

        /* Get the number of dims for this var. */
        if ((ierr = PIOc_inq_varndims(ncid, varid, &ndims)))
            return check_netcdf(file, ierr, __FILE__, __LINE__);

        PIO_Offset dimlen[ndims];

        /* If no count array was passed, we need to know the dimlens
         * so we can calculate how many data elements are in the
         * buf. */
        if (!count)
        {
            int dimid[ndims];

            /* Get the dimids for this var. */
            if ((ierr = PIOc_inq_vardimid(ncid, varid, dimid)))
                return check_netcdf(file, ierr, __FILE__, __LINE__);

            /* Get the length of each dimension. */
            for (int vd = 0; vd < ndims; vd++)
                if ((ierr = PIOc_inq_dimlen(ncid, dimid[vd], &dimlen[vd])))
                    return check_netcdf(file, ierr, __FILE__, __LINE__);
        }

        /* Figure out the real start, count, and stride arrays. (The
         * user may have passed in NULLs.) */
        /* Allocate memory for these arrays, now that we know ndims. */
        if (!(rstart = malloc(ndims * sizeof(PIO_Offset))))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
        if (!(rcount = malloc(ndims * sizeof(PIO_Offset))))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

        PIO_Offset rstride[ndims];
        for (int vd = 0; vd < ndims; vd++)
        {
            rstart[vd] = start ? start[vd] : 0;
            rcount[vd] = count ? count[vd] : dimlen[vd];
            rstride[vd] = stride ? stride[vd] : 1;
            LOG((3, "rstart[%d] = %d rcount[%d] = %d rstride[%d] = %d", vd,
                 rstart[vd], vd, rcount[vd], vd, rstride[vd]));
        }

        /* How many elements in buf? */
        for (int vd = 0; vd < ndims; vd++)
            num_elem *= rcount[vd];
        LOG((2, "PIOc_get_vars_tc num_elem = %d", num_elem));

        /* Free tmp resources. */
        if (start_present)
            free(rstart);
        else
            start = rstart;

        if (count_present)
            free(rcount);
        else
            count = rcount;
    }

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_GET_VARS;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            /* Send the function parameters and associated informaiton
             * to the msg handler. */
            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&ndims, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((PIO_Offset *)start, ndims, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((PIO_Offset *)count, ndims, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&stride_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr && stride_present)
                mpierr = MPI_Bcast((PIO_Offset *)stride, ndims, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&xtype, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&num_elem, 1, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, ios->compmaster, ios->intercomm);
            LOG((2, "PIOc_get_vars_tc ncid = %d varid = %d ndims = %d "
                 "stride_present = %d xtype = %d num_elem = %d", ncid, varid,
                 ndims, stride_present, xtype, num_elem));
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);

        /* Broadcast values currently only known on computation tasks to IO tasks. */
        if ((mpierr = MPI_Bcast(&num_elem, 1, MPI_OFFSET, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);
        if ((mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
        LOG((2, "file->iotype = %d xtype = %d file->do_io = %d", file->iotype, xtype, file->do_io));
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
        {
#ifdef PNET_READ_AND_BCAST
            LOG((1, "PNET_READ_AND_BCAST"));
            ncmpi_begin_indep_data(file->fh);

            /* Only the IO master does the IO, so we are not really
             * getting parallel IO here. */
            if (ios->iomaster == MPI_ROOT)
            {
                switch(xtype)
                {
                case NC_BYTE:
                    ierr = ncmpi_get_vars_schar(file->fh, varid, start, count, stride, buf);
                    break;
                case NC_CHAR:
                    ierr = ncmpi_get_vars_text(file->fh, varid, start, count, stride, buf);
                    break;
                case NC_SHORT:
                    ierr = ncmpi_get_vars_short(file->fh, varid, start, count, stride, buf);
                    break;
                case NC_INT:
                    ierr = ncmpi_get_vars_int(file->fh, varid, start, count, stride, buf);
                    break;
                case NC_FLOAT:
                    ierr = ncmpi_get_vars_float(file->fh, varid, start, count, stride, buf);
                    break;
                case NC_DOUBLE:
                    ierr = ncmpi_get_vars_double(file->fh, varid, start, count, stride, buf);
                    break;
                case NC_INT64:
                    ierr = ncmpi_get_vars_longlong(file->fh, varid, start, count, stride, buf);
                    break;
                default:
                    LOG((0, "Unknown type for pnetcdf file! xtype = %d", xtype));
                }
            };
            ncmpi_end_indep_data(file->fh);
            bcast=true;
#else /* PNET_READ_AND_BCAST */
            LOG((1, "not PNET_READ_AND_BCAST"));
            switch(xtype)
            {
            case NC_BYTE:
                ierr = ncmpi_get_vars_schar_all(file->fh, varid, start, count, stride, buf);
                break;
            case NC_CHAR:
                ierr = ncmpi_get_vars_text_all(file->fh, varid, start, count, stride, buf);
                break;
            case NC_SHORT:
                ierr = ncmpi_get_vars_short_all(file->fh, varid, start, count, stride, buf);
                break;
            case NC_INT:
                ierr = ncmpi_get_vars_int_all(file->fh, varid, start, count, stride, buf);
                break;
            case NC_FLOAT:
                ierr = ncmpi_get_vars_float_all(file->fh, varid, start, count, stride, buf);
                break;
            case NC_DOUBLE:
                ierr = ncmpi_get_vars_double_all(file->fh, varid, start, count, stride, buf);
                break;
            case NC_INT64:
                ierr = ncmpi_get_vars_longlong_all(file->fh, varid, start, count, stride, buf);
                break;
            default:
                LOG((0, "Unknown type for pnetcdf file! xtype = %d", xtype));
            }
#endif /* PNET_READ_AND_BCAST */
        }
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
            switch(xtype)
            {
            case NC_BYTE:
                ierr = nc_get_vars_schar(file->fh, varid, (size_t *)start, (size_t *)count,
                                         (ptrdiff_t *)stride, buf);
                break;
            case NC_CHAR:
                ierr = nc_get_vars_text(file->fh, varid, (size_t *)start, (size_t *)count,
                                        (ptrdiff_t *)stride, buf);
                break;
            case NC_SHORT:
                ierr = nc_get_vars_short(file->fh, varid, (size_t *)start, (size_t *)count,
                                         (ptrdiff_t *)stride, buf);
                break;
            case NC_INT:
                ierr = nc_get_vars_int(file->fh, varid, (size_t *)start, (size_t *)count,
                                       (ptrdiff_t *)stride, buf);
                break;
            case NC_FLOAT:
                ierr = nc_get_vars_float(file->fh, varid, (size_t *)start, (size_t *)count,
                                         (ptrdiff_t *)stride, buf);
                break;
            case NC_DOUBLE:
                ierr = nc_get_vars_double(file->fh, varid, (size_t *)start, (size_t *)count,
                                          (ptrdiff_t *)stride, buf);
                break;
#ifdef _NETCDF4
            case NC_UBYTE:
                ierr = nc_get_vars_uchar(file->fh, varid, (size_t *)start, (size_t *)count,
                                         (ptrdiff_t *)stride, buf);
                break;
            case NC_USHORT:
                ierr = nc_get_vars_ushort(file->fh, varid, (size_t *)start, (size_t *)count,
                                          (ptrdiff_t *)stride, buf);
                break;
            case NC_UINT:
                ierr = nc_get_vars_uint(file->fh, varid, (size_t *)start, (size_t *)count,
                                        (ptrdiff_t *)stride, buf);
                break;
            case NC_INT64:
                LOG((3, "about to call nc_get_vars_longlong"));
                ierr = nc_get_vars_longlong(file->fh, varid, (size_t *)start, (size_t *)count,
                                            (ptrdiff_t *)stride, buf);
                break;
            case NC_UINT64:
                ierr = nc_get_vars_ulonglong(file->fh, varid, (size_t *)start, (size_t *)count,
                                             (ptrdiff_t *)stride, buf);
                break;
                /* case NC_STRING: */
                /*      ierr = nc_get_vars_string(file->fh, varid, (size_t *)start, (size_t *)count, */
                /*                                (ptrdiff_t *)stride, (void *)buf); */
                /*      break; */
            default:
                ierr = nc_get_vars(file->fh, varid, (size_t *)start, (size_t *)count,
                                   (ptrdiff_t *)stride, buf);
#endif /* _NETCDF4 */
            }
#endif /* _NETCDF */
    }

    if (!ios->async_interface || !ios->ioproc)
    {
        /* Free tmp start/count allocated to account for NULL start/counts */
        if (!start_present)
            free(rstart);
        if (!count_present)
            free(rcount);
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

    /* Send the data. */
    LOG((2, "PIOc_get_vars_tc bcasting data num_elem = %d typelen = %d ios->ioroot = %d", num_elem,
         typelen, ios->ioroot));
    if ((mpierr = MPI_Bcast(buf, num_elem * typelen, MPI_BYTE, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    LOG((2, "PIOc_get_vars_tc bcasting data complete"));

    return PIO_NOERR;
}

/**
 * Get one value of a variable of any type.
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param xtype the netcdf type of the variable.
 * @param buf pointer that will get the data.
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_get_var1_tc(int ncid, int varid, const PIO_Offset *index, nc_type xtype,
                     void *buf)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ndims;   /* The number of dimensions in the variable. */
    int ierr;    /* Return code from function calls. */

    /* Find the info about this file. We need this for error handling. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* Find the number of dimensions. */
    if ((ierr = PIOc_inq_varndims(ncid, varid, &ndims)))
        return pio_err(ios, file, ierr, __FILE__, __LINE__);

    /* Set up count array. */
    PIO_Offset count[ndims];
    for (int c = 0; c < ndims; c++)
        count[c] = 1;

    return PIOc_get_vars_tc(ncid, varid, index, count, NULL, xtype, buf);
}

/**
 * Internal PIO function which provides a type-neutral interface to
 * nc_put_vars.
 *
 * Users should not call this function directly. Instead, call one of
 * the derived functions, depending on the type of data you are
 * writing: PIOc_put_vars_text(), PIOc_put_vars_uchar(),
 * PIOc_put_vars_schar(), PIOc_put_vars_ushort(),
 * PIOc_put_vars_short(), PIOc_put_vars_uint(), PIOc_put_vars_int(),
 * PIOc_put_vars_long(), PIOc_put_vars_float(),
 * PIOc_put_vars_longlong(), PIOc_put_vars_double(),
 * PIOc_put_vars_ulonglong().
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param start an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param count an array of counts (must have same number of entries
 * as variable has dimensions). If NULL, counts matching the size of
 * the variable will be used.
 * @param stride an array of strides (must have same number of
 * entries as variable has dimensions). If NULL, strides of 1 will be
 * used.
 * @param xtype the netCDF type of the data being passed in buf. Data
 * will be automatically covnerted from this type to the type of the
 * variable being written to.
 * @param buf pointer to the data to be written.
 *
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_vars_tc(int ncid, int varid, const PIO_Offset *start, const PIO_Offset *count,
                     const PIO_Offset *stride, nc_type xtype, const void *buf)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int ndims; /* The number of dimensions in the variable. */
    PIO_Offset typelen; /* Size (in bytes) of the data type of data in buf. */
    PIO_Offset num_elem = 1; /* Number of data elements in the buffer. */
    char start_present = start ? true : false; /* Is start non-NULL? */
    char count_present = count ? true : false; /* Is count non-NULL? */
    char stride_present = stride ? true : false; /* Is stride non-NULL? */
    PIO_Offset *rstart, *rcount, *rstride;
    var_desc_t *vdesc;
    int *request;

    LOG((1, "PIOc_put_vars_tc ncid = %d varid = %d start = %d count = %d "
         "stride = %d xtype = %d", ncid, varid, start, count, stride, xtype));

    /* Get file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* User must provide a place to put some data. */
    if (!buf)
        return pio_err(ios, file, ierr, __FILE__, __LINE__);        

    /* Run these on all tasks if async is not in use, but only on
     * non-IO tasks if async is in use. */
    if (!ios->async_interface || !ios->ioproc)
    {
        /* Get the number of dims for this var. */
        if ((ierr = PIOc_inq_varndims(ncid, varid, &ndims)))
            return check_netcdf(file, ierr, __FILE__, __LINE__);

        /* Get the length of the data type. */
        if ((ierr = PIOc_inq_type(ncid, xtype, NULL, &typelen)))
            return check_netcdf(file, ierr, __FILE__, __LINE__);

        LOG((2, "ndims = %d typelen = %d", ndims, typelen));

        PIO_Offset dimlen[ndims];

        /* If no count array was passed, we need to know the dimlens
         * so we can calculate how many data elements are in the
         * buf. */
        if (!count)
        {
            int dimid[ndims];

            /* Get the dimids for this var. */
            if ((ierr = PIOc_inq_vardimid(ncid, varid, dimid)))
                return check_netcdf(file, ierr, __FILE__, __LINE__);

            /* Get the length of each dimension. */
            for (int vd = 0; vd < ndims; vd++)
            {
                if ((ierr = PIOc_inq_dimlen(ncid, dimid[vd], &dimlen[vd])))
                    return check_netcdf(file, ierr, __FILE__, __LINE__);
                LOG((3, "dimlen[%d] = %d", vd, dimlen[vd]));
            }
        }

        /* Allocate memory for these arrays, now that we know ndims. */
        if (!(rstart = malloc(ndims * sizeof(PIO_Offset))))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
        if (!(rcount = malloc(ndims * sizeof(PIO_Offset))))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
        if (!(rstride = malloc(ndims * sizeof(PIO_Offset))))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

        /* Figure out the real start, count, and stride arrays. (The
         * user may have passed in NULLs.) */
        for (int vd = 0; vd < ndims; vd++)
        {
            rstart[vd] = start ? start[vd] : 0;
            rcount[vd] = count ? count[vd] : dimlen[vd];
            rstride[vd] = stride ? stride[vd] : 1;
            LOG((3, "rstart[%d] = %d rcount[%d] = %d rstride[%d] = %d", vd,
                 rstart[vd], vd, rcount[vd], vd, rstride[vd]));
        }

        /* How many elements in buf? */
        for (int vd = 0; vd < ndims; vd++)
            num_elem *= rcount[vd];
        LOG((2, "PIOc_put_vars_tc num_elem = %d", num_elem));

        /* Free tmp resources. */
        if (start_present)
            free(rstart);
        else
            start = rstart;

        if (count_present)
            free(rcount);
        else
            count = rcount;

        /* Only PNETCDF requires a non-NULL stride, realocate it later if needed */
        free(rstride);
    }

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = PIO_MSG_PUT_VARS;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            /* Send the function parameters and associated informaiton
             * to the msg handler. */
            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&varid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&ndims, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((PIO_Offset *)start, ndims, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((PIO_Offset *)count, ndims, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&stride_present, 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr && stride_present)
                mpierr = MPI_Bcast((PIO_Offset *)stride, ndims, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&xtype, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&num_elem, 1, MPI_OFFSET, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, ios->compmaster, ios->intercomm);
            LOG((2, "PIOc_put_vars_tc ncid = %d varid = %d ndims = %d start_present = %d "
                 "count_present = %d stride_present = %d xtype = %d num_elem = %d", ncid, varid,
                 ndims, start_present, count_present, stride_present, xtype, num_elem));

            /* Send the data. */
            if (!mpierr)
                mpierr = MPI_Bcast((void *)buf, num_elem * typelen, MPI_BYTE, ios->compmaster,
                                   ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            check_mpi(file, mpierr, __FILE__, __LINE__);
        LOG((2, "PIOc_put_vars_tc checked mpierr = %d", mpierr));

        /* Broadcast values currently only known on computation tasks to IO tasks. */
        LOG((2, "PIOc_put_vars_tc bcast from comproot"));
        if ((mpierr = MPI_Bcast(&ndims, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        LOG((2, "PIOc_put_vars_tc complete bcast from comproot ndims = %d", ndims));
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
        {
            PIO_Offset *fake_stride;

            if (!stride_present)
            {
                LOG((2, "stride not present"));
                if (!(fake_stride = malloc(ndims * sizeof(PIO_Offset))))
                    return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
                for (int d = 0; d < ndims; d++)
                    fake_stride[d] = 1;
            }
            else
                fake_stride = (PIO_Offset *)stride;

            LOG((2, "PIOc_put_vars_tc calling pnetcdf function"));
            vdesc = file->varlist + varid;
            if (vdesc->nreqs % PIO_REQUEST_ALLOC_CHUNK == 0)
                if (!(vdesc->request = realloc(vdesc->request,
                                               sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
                    return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
            request = vdesc->request + vdesc->nreqs;
            LOG((2, "PIOc_put_vars_tc request = %d", vdesc->request));

            /* Only the IO master actually does the call. */
            if (ios->iomaster == MPI_ROOT)
            {
                switch(xtype)
                {
                case NC_BYTE:
                    ierr = ncmpi_bput_vars_schar(file->fh, varid, start, count, fake_stride, buf, request);
                    break;
                case NC_CHAR:
                    ierr = ncmpi_bput_vars_text(file->fh, varid, start, count, fake_stride, buf, request);
                    break;
                case NC_SHORT:
                    ierr = ncmpi_bput_vars_short(file->fh, varid, start, count, fake_stride, buf, request);
                    break;
                case NC_INT:
                    ierr = ncmpi_bput_vars_int(file->fh, varid, start, count, fake_stride, buf, request);
                    break;
                case NC_FLOAT:
                    ierr = ncmpi_bput_vars_float(file->fh, varid, start, count, fake_stride, buf, request);
                    break;
                case NC_DOUBLE:
                    ierr = ncmpi_bput_vars_double(file->fh, varid, start, count, fake_stride, buf, request);
                    break;
                case NC_INT64:
                    ierr = ncmpi_bput_vars_longlong(file->fh, varid, start, count, fake_stride, buf, request);
                    break;
                default:
                    LOG((0, "Unknown type for pnetcdf file! xtype = %d", xtype));
                }
                LOG((2, "PIOc_put_vars_tc io_rank 0 done with pnetcdf call, ierr=%d", ierr));
            }
            else
                *request = PIO_REQ_NULL;

            vdesc->nreqs++;
            flush_output_buffer(file, false, 0);
            LOG((2, "PIOc_put_vars_tc flushed output buffer"));

            /* Free malloced resources. */
            if (!stride_present)
                free(fake_stride);
        }
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
        {
            LOG((2, "PIOc_put_vars_tc calling netcdf function file->iotype = %d",
                 file->iotype));
            switch(xtype)
            {
            case NC_BYTE:
                ierr = nc_put_vars_schar(file->fh, varid, (size_t *)start, (size_t *)count,
                                         (ptrdiff_t *)stride, buf);
                break;
            case NC_CHAR:
                ierr = nc_put_vars_text(file->fh, varid, (size_t *)start, (size_t *)count,
                                        (ptrdiff_t *)stride, buf);
                break;
            case NC_SHORT:
                ierr = nc_put_vars_short(file->fh, varid, (size_t *)start, (size_t *)count,
                                         (ptrdiff_t *)stride, buf);
                break;
            case NC_INT:
                ierr = nc_put_vars_int(file->fh, varid, (size_t *)start, (size_t *)count,
                                       (ptrdiff_t *)stride, buf);
                break;
            case NC_FLOAT:
                ierr = nc_put_vars_float(file->fh, varid, (size_t *)start, (size_t *)count,
                                         (ptrdiff_t *)stride, buf);
                break;
            case NC_DOUBLE:
                ierr = nc_put_vars_double(file->fh, varid, (size_t *)start, (size_t *)count,
                                          (ptrdiff_t *)stride, buf);
                break;
#ifdef _NETCDF4
            case NC_UBYTE:
                ierr = nc_put_vars_uchar(file->fh, varid, (size_t *)start, (size_t *)count,
                                         (ptrdiff_t *)stride, buf);
                break;
            case NC_USHORT:
                ierr = nc_put_vars_ushort(file->fh, varid, (size_t *)start, (size_t *)count,
                                          (ptrdiff_t *)stride, buf);
                break;
            case NC_UINT:
                ierr = nc_put_vars_uint(file->fh, varid, (size_t *)start, (size_t *)count,
                                        (ptrdiff_t *)stride, buf);
                break;
            case NC_INT64:
                ierr = nc_put_vars_longlong(file->fh, varid, (size_t *)start, (size_t *)count,
                                            (ptrdiff_t *)stride, buf);
                break;
            case NC_UINT64:
                ierr = nc_put_vars_ulonglong(file->fh, varid, (size_t *)start, (size_t *)count,
                                             (ptrdiff_t *)stride, buf);
                break;
                /* case NC_STRING: */
                /*      ierr = nc_put_vars_string(file->fh, varid, (size_t *)start, (size_t *)count, */
                /*                                (ptrdiff_t *)stride, (void *)buf); */
                /*      break; */
            default:
                ierr = nc_put_vars(file->fh, varid, (size_t *)start, (size_t *)count,
                                   (ptrdiff_t *)stride, buf);
#endif /* _NETCDF4 */
            }
            LOG((2, "PIOc_put_vars_tc io_rank 0 done with netcdf call, ierr=%d", ierr));
        }
#endif /* _NETCDF */
    }

    if (!ios->async_interface || !ios->ioproc)
    {
        /* Free tmp start/count allocated to account for NULL start/counts */
        if (!start_present)
            free(rstart);
        if (!count_present)
            free(rcount);
    }

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);
    LOG((2, "PIOc_put_vars_tc bcast netcdf return code %d complete", ierr));

    return PIO_NOERR;
}

/**
 * Internal PIO function which provides a type-neutral interface to
 * nc_put_var1 calls.
 *
 * Users should not call this function directly. Instead, call one of
 * the derived functions, depending on the type of data you are
 * writing: PIOc_put_var1_text(), PIOc_put_var1_uchar(),
 * PIOc_put_var1_schar(), PIOc_put_var1_ushort(),
 * PIOc_put_var1_short(), PIOc_put_var1_uint(), PIOc_put_var1_int(),
 * PIOc_put_var1_long(), PIOc_put_var1_float(),
 * PIOc_put_var1_longlong(), PIOc_put_var1_double(),
 * PIOc_put_var1_ulonglong().
 *
 * This routine is called collectively by all tasks in the
 * communicator ios.union_comm.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID number
 * @param index an array of start indicies (must have same number of
 * entries as variable has dimensions). If NULL, indices of 0 will be
 * used.
 * @param xtype the netCDF type of the data being passed in buf. Data
 * will be automatically covnerted from this type to the type of the
 * variable being written to.
 * @param op pointer to the data to be written.
 *
 * @return PIO_NOERR on success, error code otherwise.
 */
int PIOc_put_var1_tc(int ncid, int varid, const PIO_Offset *index, nc_type xtype,
                     const void *op)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ndims;   /* The number of dimensions in the variable. */
    int ierr;    /* Return code from function calls. */

    /* Find the info about this file. We need this for error handling. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);
    ios = file->iosystem;

    /* Find the number of dimensions. */
    if ((ierr = PIOc_inq_varndims(ncid, varid, &ndims)))
        return pio_err(ios, file, ierr, __FILE__, __LINE__);

    /* Set up count array. */
    PIO_Offset count[ndims];
    for (int c = 0; c < ndims; c++)
        count[c] = 1;

    return PIOc_put_vars_tc(ncid, varid, index, count, NULL, xtype, op);
}
