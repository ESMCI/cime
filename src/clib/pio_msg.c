/** @file
 *
 * PIO async message handling. This file contains the code which
 * runs on the IO nodes when async is in use. This code waits for
 * messages from the computation nodes, and responds to messages by
 * running the appropriate netCDF function.
 *
 * @author Ed Hartnett
 */

#include <config.h>
#include <pio.h>
#include <pio_internal.h>

#ifdef PIO_ENABLE_LOGGING
extern int my_rank;
extern int pio_log_level;
#endif /* PIO_ENABLE_LOGGING */

/** This function is run on the IO tasks to handle nc_inq_type*()
 * functions.
 *
 * @param ios pointer to the iosystem info.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_type_handler(iosystem_desc_t *ios)
{
    int ncid;
    int xtype;
    char name_present, size_present;
    char *namep = NULL, name[NC_MAX_NAME + 1];
    PIO_Offset *sizep = NULL, size;
    int mpierr;
    int ret;

    LOG((1, "inq_type_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&xtype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&name_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&size_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;

    /* Handle null pointer issues. */
    if (name_present)
        namep = name;
    if (size_present)
        sizep = &size;

    /* Call the function. */
    if ((ret = PIOc_inq_type(ncid, xtype, namep, sizep)))
        return ret;

    LOG((1, "inq_type_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to find netCDF file
 * format.
 *
 * @param ios pointer to the iosystem info.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_format_handler(iosystem_desc_t *ios)
{
    int ncid;
    int *formatp = NULL, format;
    char format_present;
    int mpierr;
    int ret;

    LOG((1, "inq_format_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&format_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "inq_format_handler got parameters ncid = %d format_present = %d",
         ncid, format_present));

    /* Manage NULL pointers. */
    if (format_present)
        formatp = &format;

    /* Call the function. */
    if ((ret = PIOc_inq_format(ncid, formatp)))
        return ret;

    if (formatp)
        LOG((2, "inq_format_handler format = %d", *formatp));
    LOG((1, "inq_format_handler succeeded!"));

    return PIO_NOERR;
}

/** This function is run on the IO tasks to create a netCDF file.
 *
 * @param ios pointer to the iosystem info.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int create_file_handler(iosystem_desc_t *ios)
{
    int ncid;
    int len;
    int iotype;
    char *filename;
    int mode;
    int mpierr;
    int ret;

    LOG((1, "create_file_handler comproot = %d\n", ios->comproot));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&len, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "create_file_handler got parameter len = %d\n", len));
    if (!(filename = malloc(len + 1 * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)filename, len + 1, MPI_CHAR, 0,
                            ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&iotype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&mode, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "create_file_handler got parameters len = %d "
         "filename = %s iotype = %d mode = %d\n",
         len, filename, iotype, mode));

    /* Call the create file function. */
    if ((ret = PIOc_createfile(ios->iosysid, &ncid, &iotype, filename, mode)))
        return ret;

    /* Free resources. */
    free(filename);

    LOG((1, "create_file_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to close a netCDF file. It is
 * only ever run on the IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int close_file_handler(iosystem_desc_t *ios)
{
    int ncid;
    int mpierr;
    int ret;

    LOG((1, "close_file_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "create_file_handler got parameter ncid = %d", ncid));

    /* Call the close file function. */
    if ((ret = PIOc_closefile(ncid)))
        return ret;

    LOG((1, "close_file_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to inq a netCDF file. It is
 * only ever run on the IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_handler(iosystem_desc_t *ios)
{
    int ncid;
    int ndims, nvars, ngatts, unlimdimid;
    int *ndimsp = NULL, *nvarsp = NULL, *ngattsp = NULL, *unlimdimidp = NULL;
    char ndims_present, nvars_present, ngatts_present, unlimdimid_present;
    int mpierr;
    int ret;

    LOG((1, "inq_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&ndims_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&nvars_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&ngatts_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&unlimdimid_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "inq_handler ndims_present = %d nvars_present = %d ngatts_present = %d unlimdimid_present = %d\n",
         ndims_present, nvars_present, ngatts_present, unlimdimid_present));

    /* NULLs passed in to any of the pointers in the original call
     * need to be matched with NULLs here. Assign pointers where
     * non-NULL pointers were passed in. */
    if (ndims_present)
        ndimsp = &ndims;
    if (nvars_present)
        nvarsp = &nvars;
    if (ngatts_present)
        ngattsp = &ngatts;
    if (unlimdimid_present)
        unlimdimidp = &unlimdimid;

    /* Call the inq function to get the values. */
    if ((ret = PIOc_inq(ncid, ndimsp, nvarsp, ngattsp, unlimdimidp)))
        return ret;

    return PIO_NOERR;
}

/** Do an inq_dim on a netCDF dimension. This function is only run on
 * IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @param msg the message sent my the comp root task.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_dim_handler(iosystem_desc_t *ios, int msg)
{
    int ncid;
    int dimid;
    char name_present, len_present;
    char *dimnamep = NULL;
    PIO_Offset *dimlenp = NULL;
    char dimname[NC_MAX_NAME + 1];
    PIO_Offset dimlen;

    int mpierr;
    int ret;

    LOG((1, "inq_dim_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&dimid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&name_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&len_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "inq_handler name_present = %d len_present = %d", name_present,
         len_present));

    /* Set the non-null pointers. */
    if (name_present)
        dimnamep = dimname;
    if (len_present)
        dimlenp = &dimlen;

    /* Call the inq function to get the values. */
    if ((ret = PIOc_inq_dim(ncid, dimid, dimnamep, dimlenp)))
        return ret;

    return PIO_NOERR;
}

/** Do an inq_dimid on a netCDF dimension name. This function is only
 * run on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_dimid_handler(iosystem_desc_t *ios)
{
    int ncid;
    int *dimidp = NULL, dimid;
    int mpierr;
    int id_present;
    int ret;
    int namelen;
    char *name;

    LOG((1, "inq_dimid_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&id_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "inq_dimid_handler ncid = %d namelen = %d name = %s id_present = %d",
         ncid, namelen, name, id_present));

    /* Set non-null pointer. */
    if (id_present)
        dimidp = &dimid;

    /* Call the inq_dimid function. */
    if ((ret = PIOc_inq_dimid(ncid, name, dimidp)))
        return ret;

    /* Free resources. */
    free(name);

    return PIO_NOERR;
}

/** Handle attribute inquiry operations. This code only runs on IO
 * tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @param msg the message sent my the comp root task.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_att_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int mpierr;
    int ret;
    char *name;
    int namelen;
    int *op, *ip;
    nc_type xtype, *xtypep = NULL;
    PIO_Offset len, *lenp = NULL;
    char xtype_present, len_present;

    LOG((1, "inq_att_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster,
                            ios->intercomm)))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast(&xtype_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&len_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;

    /* Match NULLs in collective function call. */
    if (xtype_present)
        xtypep = &xtype;
    if (len_present)
        lenp = &len;

    /* Call the function to learn about the attribute. */
    if ((ret = PIOc_inq_att(ncid, varid, name, xtypep, lenp)))
        return ret;

    /* Free memory. */
    free(name);

    return PIO_NOERR;
}

/** Handle attribute inquiry operations. This code only runs on IO
 * tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @param msg the message sent my the comp root task.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_attname_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int attnum;
    char name[NC_MAX_NAME + 1], *namep = NULL;
    char name_present;
    int mpierr;
    int ret;

    LOG((1, "inq_att_name_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&attnum, 1, MPI_INT,  ios->compmaster, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&name_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "inq_attname_handler got ncid = %d varid = %d attnum = %d name_present = %d",
         ncid, varid, attnum, name_present));

    /* Match NULLs in collective function call. */
    if (name_present)
        namep = name;

    /* Call the function to learn about the attribute. */
    if ((ret = PIOc_inq_attname(ncid, varid, attnum, namep)))
        return ret;

    return PIO_NOERR;
}

/** Handle attribute inquiry operations. This code only runs on IO
 * tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @param msg the message sent my the comp root task.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_attid_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int attnum;
    char *name;
    int namelen;
    int id, *idp = NULL;
    char id_present;
    int mpierr;
    int ret;

    LOG((1, "inq_attid_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast(name, namelen + 1, MPI_CHAR,  ios->compmaster, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&id_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "inq_attid_handler got ncid = %d varid = %d attnum = %d id_present = %d",
         ncid, varid, attnum, id_present));

    /* Match NULLs in collective function call. */
    if (id_present)
        idp = &id;

    /* Call the function to learn about the attribute. */
    if ((ret = PIOc_inq_attid(ncid, varid, name, idp)))
        return ret;

    /* Free resources. */
    free(name);

    return PIO_NOERR;
}

/** Handle attribute operations. This code only runs on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @param msg the message sent my the comp root task.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int att_put_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int mpierr;
    int ierr;
    char *name;
    int namelen;
    PIO_Offset attlen, typelen;
    nc_type atttype;
    int *op, *ip;
    int iotype;

    LOG((1, "att_put_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster,
                       ios->intercomm);
    if ((mpierr = MPI_Bcast(&atttype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&attlen, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(op = malloc(attlen * typelen)))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)op, attlen * typelen, MPI_BYTE, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "att_put_handler ncid = %d varid = %d namelen = %d name = %s iotype = %d"
         "atttype = %d attlen = %d typelen = %d",
         ncid, varid, namelen, name, iotype, atttype, attlen, typelen));

    /* Call the function to read the attribute. */
    if ((ierr = PIOc_put_att(ncid, varid, name, atttype, attlen, op)))
        return ierr;
    LOG((2, "put_handler called PIOc_put_att, ierr = %d", ierr));

    /* Free resources. */
    free(name);
    free(op);

    LOG((2, "put_handler complete!"));
    return PIO_NOERR;
}

/** Handle attribute operations. This code only runs on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @param msg the message sent my the comp root task.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int att_get_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int mpierr;
    int ierr;
    char *name;
    int namelen;
    PIO_Offset attlen, typelen;
    nc_type atttype;
    int *op, *ip;
    int iotype;

    LOG((1, "att_get_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    mpierr = MPI_Bcast(&namelen, 1, MPI_INT,  ios->compmaster, ios->intercomm);
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, ios->compmaster,
                       ios->intercomm);
    if ((mpierr = MPI_Bcast(&iotype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&atttype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&attlen, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "att_get_handler ncid = %d varid = %d namelen = %d name = %s iotype = %d"
         "atttype = %d attlen = %d typelen = %d",
         ncid, varid, namelen, name, iotype, atttype, attlen, typelen));

    /* Allocate space for the attribute data. */
    if (!(ip = malloc(attlen * typelen)))
        return PIO_ENOMEM;

    /* Call the function to read the attribute. */
    if ((ierr = PIOc_get_att(ncid, varid, name, ip)))
        return ierr;

    /* Free resources. */
    free(name);
    free(ip);

    return PIO_NOERR;
}

/** Handle var put operations. This code only runs on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int put_vars_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int mpierr;
    int ierr;
    char *name;
    int namelen;
    PIO_Offset typelen; /** Length (in bytes) of this type. */
    nc_type xtype; /** Type of the data being written. */
    char stride_present;
    PIO_Offset *startp = NULL, *countp = NULL, *stridep = NULL;
    int ndims; /** Number of dimensions. */
    void *buf; /** Buffer for data storage. */
    PIO_Offset num_elem; /** Number of data elements in the buffer. */

    LOG((1, "put_vars_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&ndims, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;

    /* Now we know how big to make these arrays. */
    PIO_Offset start[ndims], count[ndims], stride[ndims];

    if (!mpierr)
    {
        if ((mpierr = MPI_Bcast(start, ndims, MPI_OFFSET, 0, ios->intercomm)))
            return PIO_EIO;
        LOG((1, "put_vars_handler getting start[0] = %d ndims = %d", start[0], ndims));
    }
    if (!mpierr)
        if ((mpierr = MPI_Bcast(count, ndims, MPI_OFFSET, 0, ios->intercomm)))
            return PIO_EIO;
    if ((mpierr = MPI_Bcast(&stride_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if (!mpierr && stride_present)
        if ((mpierr = MPI_Bcast(stride, ndims, MPI_OFFSET, 0, ios->intercomm)))
            return PIO_EIO;
    if ((mpierr = MPI_Bcast(&xtype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&num_elem, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "put_vars_handler ncid = %d varid = %d ndims = %d "
         "stride_present = %d xtype = %d num_elem = %d typelen = %d",
         ncid, varid, ndims, stride_present, xtype,
         num_elem, typelen));

    for (int d = 0; d < ndims; d++)
    {
        LOG((2, "start[%d] = %d\n", d, start[d]));
        LOG((2, "count[%d] = %d\n", d, count[d]));
        if (stride_present)
            LOG((2, "stride[%d] = %d\n", d, stride[d]));
    }

    /* Allocate room for our data. */
    if (!(buf = malloc(num_elem * typelen)))
        return PIO_ENOMEM;

    /* Get the data. */
    if ((mpierr = MPI_Bcast(buf, num_elem * typelen, MPI_BYTE, 0, ios->intercomm)))
        return PIO_EIO;

    /* for (int e = 0; e < num_elem; e++) */
    /*  LOG((2, "element %d = %d", e, ((int *)buf)[e])); */

    /* Set the non-NULL pointers. */
    startp = start;
    countp = count;
    if (stride_present)
        stridep = stride;

    /* Call the function to write the data. */
    switch(xtype)
    {
    case NC_BYTE:
        ierr = PIOc_put_vars_schar(ncid, varid, startp, countp, stridep, buf);
        break;
    case NC_CHAR:
        ierr = PIOc_put_vars_schar(ncid, varid, startp, countp, stridep, buf);
        break;
    case NC_SHORT:
        ierr = PIOc_put_vars_short(ncid, varid, startp, countp, stridep, buf);
        break;
    case NC_INT:
        ierr = PIOc_put_vars_int(ncid, varid, startp, countp,
                                 stridep, buf);
        break;
    case NC_FLOAT:
        ierr = PIOc_put_vars_float(ncid, varid, startp, countp,
                                   stridep, buf);
        break;
    case NC_DOUBLE:
        ierr = PIOc_put_vars_double(ncid, varid, startp, countp,
                                    stridep, buf);
        break;
#ifdef _NETCDF4
    case NC_UBYTE:
        ierr = PIOc_put_vars_uchar(ncid, varid, startp, countp,
                                   stridep, buf);
        break;
    case NC_USHORT:
        ierr = PIOc_put_vars_ushort(ncid, varid, startp, countp,
                                    stridep, buf);
        break;
    case NC_UINT:
        ierr = PIOc_put_vars_uint(ncid, varid, startp, countp,
                                  stridep, buf);
        break;
    case NC_INT64:
        ierr = PIOc_put_vars_longlong(ncid, varid, startp, countp,
                                      stridep, buf);
        break;
    case NC_UINT64:
        ierr = PIOc_put_vars_ulonglong(ncid, varid, startp, countp,
                                       stridep, buf);
        break;
        /* case NC_STRING: */
        /*      ierr = PIOc_put_vars_string(ncid, varid, startp, countp, */
        /*                                stridep, (void *)buf); */
        /*      break; */
        /*    default:*/
        /* ierr = PIOc_put_vars(ncid, varid, startp, countp, */
        /*                   stridep, buf); */
#endif /* _NETCDF4 */
    }

    free(buf);

    return PIO_NOERR;
}

/** Handle var get operations. This code only runs on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int get_vars_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int mpierr;
    int ierr;
    char *name;
    int namelen;
    PIO_Offset typelen; /** Length (in bytes) of this type. */
    nc_type xtype; /** Type of the data being written. */
    char stride_present;
    PIO_Offset *startp = NULL, *countp = NULL, *stridep = NULL;
    int ndims; /** Number of dimensions. */
    void *buf; /** Buffer for data storage. */
    PIO_Offset num_elem; /** Number of data elements in the buffer. */

    LOG((1, "get_vars_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&ndims, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;

    /* Now we know how big to make these arrays. */
    PIO_Offset start[ndims], count[ndims], stride[ndims];

    if (!mpierr)
    {
        if ((mpierr = MPI_Bcast(start, ndims, MPI_OFFSET, 0, ios->intercomm)))
            return PIO_EIO;
        LOG((1, "put_vars_handler getting start[0] = %d ndims = %d", start[0], ndims));
    }
    if (!mpierr)
        if ((mpierr = MPI_Bcast(count, ndims, MPI_OFFSET, 0, ios->intercomm)))
            return PIO_EIO;
    if ((mpierr = MPI_Bcast(&stride_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if (!mpierr && stride_present)
        if ((mpierr = MPI_Bcast(stride, ndims, MPI_OFFSET, 0, ios->intercomm)))
            return PIO_EIO;
    if ((mpierr = MPI_Bcast(&xtype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&num_elem, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&typelen, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "get_vars_handler ncid = %d varid = %d ndims = %d "
         "stride_present = %d xtype = %d num_elem = %d typelen = %d",
         ncid, varid, ndims, stride_present, xtype,
         num_elem, typelen));

    for (int d = 0; d < ndims; d++)
    {
        LOG((2, "start[%d] = %d\n", d, start[d]));
        LOG((2, "count[%d] = %d\n", d, count[d]));
        if (stride_present)
            LOG((2, "stride[%d] = %d\n", d, stride[d]));
    }

    /* Allocate room for our data. */
    if (!(buf = malloc(num_elem * typelen)))
        return PIO_ENOMEM;

    /* Set the non-NULL pointers. */
    startp = start;
    countp = count;
    if (stride_present)
        stridep = stride;

    /* Call the function to read the data. */
    switch(xtype)
    {
    case NC_BYTE:
        ierr = PIOc_get_vars_schar(ncid, varid, startp, countp,
                                   stridep, buf);
        break;
    case NC_CHAR:
        ierr = PIOc_get_vars_schar(ncid, varid, startp, countp,
                                   stridep, buf);
        break;
    case NC_SHORT:
        ierr = PIOc_get_vars_short(ncid, varid, startp, countp,
                                   stridep, buf);
        break;
    case NC_INT:
        ierr = PIOc_get_vars_int(ncid, varid, startp, countp,
                                 stridep, buf);
        break;
    case NC_FLOAT:
        ierr = PIOc_get_vars_float(ncid, varid, startp, countp,
                                   stridep, buf);
        break;
    case NC_DOUBLE:
        ierr = PIOc_get_vars_double(ncid, varid, startp, countp,
                                    stridep, buf);
        break;
#ifdef _NETCDF4
    case NC_UBYTE:
        ierr = PIOc_get_vars_uchar(ncid, varid, startp, countp,
                                   stridep, buf);
        break;
    case NC_USHORT:
        ierr = PIOc_get_vars_ushort(ncid, varid, startp, countp,
                                    stridep, buf);
        break;
    case NC_UINT:
        ierr = PIOc_get_vars_uint(ncid, varid, startp, countp,
                                  stridep, buf);
        break;
    case NC_INT64:
        ierr = PIOc_get_vars_longlong(ncid, varid, startp, countp,
                                      stridep, buf);
        break;
    case NC_UINT64:
        ierr = PIOc_get_vars_ulonglong(ncid, varid, startp, countp,
                                       stridep, buf);
        break;
        /* case NC_STRING: */
        /*      ierr = PIOc_get_vars_string(ncid, varid, startp, countp, */
        /*                                stridep, (void *)buf); */
        /*      break; */
        /*    default:*/
        /* ierr = PIOc_get_vars(ncid, varid, startp, countp, */
        /*                   stridep, buf); */
#endif /* _NETCDF4 */
    }

    free(buf);
    LOG((1, "get_vars_handler succeeded!"));
    return PIO_NOERR;
}

/** 
 * Do an inq_var on a netCDF variable. This function is only run on
 * IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, error code otherwise.
 */
int inq_var_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int mpierr;
    char name_present, xtype_present, ndims_present, dimids_present, natts_present;
    char name[NC_MAX_NAME + 1], *namep = NULL;
    nc_type xtype, *xtypep = NULL;
    int *ndimsp = NULL, *dimidsp = NULL, *nattsp = NULL;
    int ndims, dimids[NC_MAX_DIMS], natts;
    int ret;

    LOG((1, "inq_var_handler"));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&name_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&xtype_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&ndims_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&dimids_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&natts_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2,"inq_var_handler ncid = %d varid = %d name_present = %d xtype_present = %d ndims_present = %d "
         "dimids_present = %d natts_present = %d\n",
         ncid, varid, name_present, xtype_present, ndims_present, dimids_present, natts_present));

    /* Set the non-NULL pointers. */
    if (name_present)
        namep = name;
    if (xtype_present)
        xtypep = &xtype;
    if (ndims_present)
        ndimsp = &ndims;
    if (dimids_present)
        dimidsp = dimids;
    if (natts_present)
        nattsp = &natts;

    /* Call the inq function to get the values. */
    if ((ret = PIOc_inq_var(ncid, varid, namep, xtypep, ndimsp, dimidsp, nattsp)))
        return ret;

    if (ndims_present)
        LOG((2, "inq_var_handler ndims = %d", ndims));

    return PIO_NOERR;
}

/** 
 * Do an inq_var_chunking on a netCDF variable. This function is only
 * run on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, error code otherwise.
 */
int inq_var_chunking_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    char storage_present, chunksizes_present;
    int storage, *storagep;
    PIO_Offset chunksizes[NC_MAX_DIMS], *chunksizesp = NULL;
    int mpierr;
    int ret;

    assert(ios);
    LOG((1, "inq_var_chunking_handler"));

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&storage_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&chunksizes_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2,"inq_var_handler ncid = %d varid = %d storage_present = %d chunksizes_present = %d",
         ncid, varid, storage_present, chunksizes_present));

    /* Set the non-NULL pointers. */
    if (storage_present)
        storagep = &storage;
    if (chunksizes_present)
        chunksizesp = chunksizes;

    /* Call the inq function to get the values. */
    if ((ret = PIOc_inq_var_chunking(ncid, varid, storagep, chunksizesp)))
        return ret;

    return PIO_NOERR;
}

/** 
 * Do an inq_var_endian on a netCDF variable. This function is only
 * run on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, error code otherwise.
 */
int inq_var_endian_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    char endian_present;
    int endian, *endianp = NULL;
    int mpierr;
    int ret;

    assert(ios);
    LOG((1, "inq_var_endian_handler"));

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&endian_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2,"inq_var_endian_handler ncid = %d varid = %d endian_present = %d", ncid, varid,
         endian_present));

    /* Set the non-NULL pointers. */
    if (endian_present)
        endianp = &endian;

    /* Call the inq function to get the values. */
    if ((ret = PIOc_inq_var_endian(ncid, varid, endianp)))
        return ret;

    return PIO_NOERR;
}

/** 
 * Do an inq_var_deflate on a netCDF variable. This function is only
 * run on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, error code otherwise.
 */
int inq_var_deflate_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    char shuffle_present;
    char deflate_present;
    char deflate_level_present;
    int shuffle, *shufflep;
    int deflate, *deflatep;
    int deflate_level, *deflate_levelp;
    int mpierr;
    int ret;

    assert(ios);
    LOG((1, "inq_var_deflate_handler"));

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&shuffle_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if (shuffle_present && !mpierr)
        if ((mpierr = MPI_Bcast(&shuffle, 1, MPI_INT, 0, ios->intercomm)))
            return PIO_EIO;
    if ((mpierr = MPI_Bcast(&deflate_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if (deflate_present && !mpierr)
        if ((mpierr = MPI_Bcast(&deflate, 1, MPI_INT, 0, ios->intercomm)))
            return PIO_EIO;
    if ((mpierr = MPI_Bcast(&deflate_level_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if (deflate_level_present && !mpierr)
        if ((mpierr = MPI_Bcast(&deflate_level, 1, MPI_INT, 0, ios->intercomm)))
            return PIO_EIO;
    LOG((2, "inq_var_handler ncid = %d varid = %d shuffle_present = %d deflate_present = %d "
         "deflate_level_present = %d", ncid, varid, shuffle_present, deflate_present,
         deflate_level_present));

    /* Set the non-NULL pointers. */
    if (shuffle_present)
        shufflep = &shuffle;
    if (deflate_present)
        deflatep = &deflate;
    if (deflate_level_present)
        deflate_levelp = &deflate_level;

    /* Call the inq function to get the values. */
    if ((ret = PIOc_inq_var_deflate(ncid, varid, shufflep, deflatep, deflate_levelp)))
        return ret;

    return PIO_NOERR;
}

/** Do an inq_varid on a netCDF variable name. This function is only
 * run on IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int inq_varid_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int mpierr;
    int ret;
    int namelen;
    char *name;

    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;

    /* Call the inq_dimid function. */
    if ((ret = PIOc_inq_varid(ncid, name, &varid)))
        return ret;

    /* Free resources. */
    free(name);

    return PIO_NOERR;
}

/** This function is run on the IO tasks to sync a netCDF file.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int sync_file_handler(iosystem_desc_t *ios)
{
    int ncid;
    int mpierr;
    int ret;

    LOG((1, "sync_file_handler"));
    assert(ios);

    /* Get the parameters for this function that the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "sync_file_handler got parameter ncid = %d", ncid));

    /* Call the sync file function. */
    if ((ret = PIOc_sync(ncid)))
        return ret;

    LOG((2, "sync_file_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to enddef a netCDF file.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int change_def_file_handler(iosystem_desc_t *ios, int msg)
{
    int ncid;
    int mpierr;
    int ret;

    LOG((1, "change_def_file_handler"));
    assert(ios);

    /* Get the parameters for this function that the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;

    /* Call the function. */
    ret = (msg == PIO_MSG_ENDDEF) ? PIOc_enddef(ncid) : PIOc_redef(ncid);

    LOG((1, "change_def_file_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to define a netCDF
 *  variable.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int def_var_handler(iosystem_desc_t *ios)
{
    int ncid;
    int len, namelen;
    int iotype;
    char *name;
    int mode;
    int mpierr;
    int ret;
    int varid;
    nc_type xtype;
    int ndims;
    int *dimids;

    LOG((1, "def_var_handler comproot = %d", ios->comproot));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc(namelen + 1 * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, 0,
                            ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&xtype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&ndims, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(dimids = malloc(ndims * sizeof(int))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast(dimids, ndims, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "def_var_handler got parameters namelen = %d "
         "name = %s len = %d ncid = %d\n", namelen, name, len, ncid));

    /* Call the create file function. */
    if ((ret = PIOc_def_var(ncid, name, xtype, ndims, dimids, &varid)))
        return ret;

    /* Free resources. */
    free(name);
    free(dimids);

    LOG((1, "def_var_handler succeeded!"));
    return PIO_NOERR;
}

/** 
 * This function is run on the IO tasks to define chunking for a
 *  netCDF variable.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, error code otherwise.
 */
int def_var_chunking_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int ndims;
    int storage;
    char chunksizes_present;
    PIO_Offset chunksizes[NC_MAX_DIMS], *chunksizesp = NULL;
    int mpierr;
    int ret;

    assert(ios);
    LOG((1, "def_var_chunking_handler comproot = %d", ios->comproot));

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&storage, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&ndims, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&chunksizes_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if (chunksizes_present)
        if ((mpierr = MPI_Bcast(chunksizes, ndims, MPI_OFFSET, 0, ios->intercomm)))
            return PIO_EIO;
    LOG((1, "def_var_chunking_handler got parameters ncid = %d varid = %d storage = %d "
         "ndims = %d chunksizes_present = %d", ncid, varid, storage, ndims, chunksizes_present));

    /* Set the non-NULL pointers. */
    if (chunksizes_present)
        chunksizesp = chunksizes;

    /* Call the create file function. */
    if ((ret = PIOc_def_var_chunking(ncid, varid, storage, chunksizesp)))
        return ret;

    LOG((1, "def_var_chunking_handler succeeded!"));
    return PIO_NOERR;
}

/** 
 * This function is run on the IO tasks to define endianness for a
 * netCDF variable.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, error code otherwise.
 */
int def_var_endian_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int endian;
    int mpierr;
    int ret;

    assert(ios);
    LOG((1, "def_var_endian_handler comproot = %d", ios->comproot));

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&endian, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "def_var_endian_handler got parameters ncid = %d varid = %d endain = %d ",
         ncid, varid, endian));

    /* Call the function. */
    if ((ret = PIOc_def_var_endian(ncid, varid, endian)))
        return ret;

    LOG((1, "def_var_chunking_handler succeeded!"));
    return PIO_NOERR;
}

/** 
 * This function is run on the IO tasks to define chunk cache settings
 * for a netCDF variable.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, error code otherwise.
 */
int set_var_chunk_cache_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    PIO_Offset size;
    PIO_Offset nelems;
    float preemption;
    int mpierr = MPI_SUCCESS;  /* Return code from MPI function codes. */
    int ret; /* Return code. */

    assert(ios);
    LOG((1, "set_var_chunk_cache_handler comproot = %d", ios->comproot));

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&size, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&nelems, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&preemption, 1, MPI_FLOAT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "set_var_chunk_cache_handler got params ncid = %d varid = %d size = %d "
         "nelems = %d preemption = %g", ncid, varid, size, nelems, preemption));

    /* Call the create file function. */
    if ((ret = PIOc_set_var_chunk_cache(ncid, varid, size, nelems, preemption)))
        return ret;

    LOG((1, "def_var_chunk_cache_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to define a netCDF
 * dimension.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int def_dim_handler(iosystem_desc_t *ios)
{
    int ncid;
    int len, namelen;
    int iotype;
    char *name;
    int mode;
    int mpierr;
    int ret;
    int dimid;

    LOG((1, "def_dim_handler comproot = %d", ios->comproot));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc(namelen + 1 * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, 0,
                            ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&len, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "def_dim_handler got parameters namelen = %d "
         "name = %s len = %d ncid = %d", namelen, name, len, ncid));

    /* Call the create file function. */
    if ((ret = PIOc_def_dim(ncid, name, len, &dimid)))
        return ret;

    /* Free resources. */
    free(name);

    LOG((1, "def_dim_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to rename a netCDF
 * dimension.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int rename_dim_handler(iosystem_desc_t *ios)
{
    int ncid;
    int len, namelen;
    int iotype;
    char *name;
    int mode;
    int mpierr;
    int ret;
    int dimid;
    char name1[NC_MAX_NAME + 1];

    LOG((1, "rename_dim_handler"));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&dimid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "rename_dim_handler got parameters namelen = %d "
         "name = %s ncid = %d dimid = %d", namelen, name, ncid, dimid));

    /* Call the create file function. */
    if ((ret = PIOc_rename_dim(ncid, dimid, name)))
        return ret;

    /* Free resources. */
    free(name);

    LOG((1, "rename_dim_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to rename a netCDF
 * dimension.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int rename_var_handler(iosystem_desc_t *ios)
{
    int ncid;
    int len, namelen;
    int iotype;
    char *name;
    int mode;
    int mpierr;
    int ret;
    int varid;
    char name1[NC_MAX_NAME + 1];

    LOG((1, "rename_var_handler"));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)name, namelen + 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "rename_var_handler got parameters namelen = %d "
         "name = %s ncid = %d varid = %d", namelen, name, ncid, varid));

    /* Call the create file function. */
    if ((ret = PIOc_rename_var(ncid, varid, name)))
        return ret;

    /* Free resources. */
    free(name);

    LOG((1, "rename_var_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to rename a netCDF
 * attribute.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int rename_att_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int namelen, newnamelen;
    char *name, *newname;
    int mpierr;
    int ret;

    LOG((1, "rename_att_handler"));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast(name, namelen + 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&newnamelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(newname = malloc((newnamelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast(newname, newnamelen + 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "rename_att_handler got parameters namelen = %d name = %s ncid = %d varid = %d "
         "newnamelen = %d newname = %s", namelen, name, ncid, varid, newnamelen, newname));

    /* Call the create file function. */
    if ((ret = PIOc_rename_att(ncid, varid, name, newname)))
        return ret;

    /* Free resources. */
    free(name);
    free(newname);

    LOG((1, "rename_att_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to delete a netCDF
 * attribute.
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int delete_att_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    int namelen, newnamelen;
    char *name, *newname;
    int mpierr;
    int ret;

    LOG((1, "delete_att_handler"));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&namelen, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(name = malloc((namelen + 1) * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast(name, namelen + 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "delete_att_handler namelen = %d name = %s ncid = %d varid = %d ",
         namelen, name, ncid, varid));

    /* Call the create file function. */
    if ((ret = PIOc_del_att(ncid, varid, name)))
        return ret;

    /* Free resources. */
    free(name);

    LOG((1, "delete_att_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to open a netCDF file.
 *
 *
 * @param ios pointer to the iosystem_desc_t.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int open_file_handler(iosystem_desc_t *ios)
{
    int ncid;
    int len;
    int iotype;
    char *filename;
    int mode;
    int mpierr;
    int ret;

    LOG((1, "open_file_handler comproot = %d", ios->comproot));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&len, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "open_file_handler got parameter len = %d", len));
    if (!(filename = malloc(len + 1 * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)filename, len + 1, MPI_CHAR, 0,
                            ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&iotype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&mode, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((2, "open_file_handler got parameters len = %d filename = %s iotype = %d mode = %d\n",
         len, filename, iotype, mode));

    /* Call the open file function. */
    if ((ret = PIOc_openfile(ios->iosysid, &ncid, &iotype, filename, mode)))
        return ret;

    /* Free resources. */
    free(filename);

    LOG((1, "open_file_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to delete a netCDF file.
 *
 * @param ios pointer to the iosystem_desc_t data.
 *
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int delete_file_handler(iosystem_desc_t *ios)
{
    int ncid;
    int len;
    char *filename;
    int mpierr;
    int ret;

    LOG((1, "delete_file_handler comproot = %d", ios->comproot));
    assert(ios);

    /* Get the parameters for this function that the he comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&len, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if (!(filename = malloc(len + 1 * sizeof(char))))
        return PIO_ENOMEM;
    if ((mpierr = MPI_Bcast((void *)filename, len + 1, MPI_CHAR, 0,
                            ios->intercomm)))
        return PIO_EIO;
    LOG((1, "delete_file_handler got parameters len = %d filename = %s\n",
         len, filename));

    /* Call the delete file function. */
    if ((ret = PIOc_deletefile(ios->iosysid, filename)))
        return ret;

    /* Free resources. */
    free(filename);

    LOG((1, "delete_file_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to...
 * NOTE: not yet implemented
 *
 * @param ios pointer to the iosystem_desc_t data.
 *
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int initdecomp_dof_handler(iosystem_desc_t *ios)
{
    assert(ios);
    return PIO_NOERR;
}

/** This function is run on the IO tasks to...
 * NOTE: not yet implemented
 *
 * @param ios pointer to the iosystem_desc_t data.
 *
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int writedarray_handler(iosystem_desc_t *ios)
{
    assert(ios);
    return PIO_NOERR;
}

/** This function is run on the IO tasks to...
 * NOTE: not yet implemented
 *
 * @param ios pointer to the iosystem_desc_t data.
 *
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int readdarray_handler(iosystem_desc_t *ios)
{
    assert(ios);
    return PIO_NOERR;
}

/** This function is run on the IO tasks to set the error handler.
 * NOTE: not yet implemented
 *
 * @param ios pointer to the iosystem_desc_t data.
 *
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int seterrorhandling_handler(iosystem_desc_t *ios)
{
    assert(ios);
    return PIO_NOERR;
}

/** 
 * This function is run on the IO tasks to set the chunk cache
 * parameters for netCDF-4.
 *
 * @param ios pointer to the iosystem_desc_t data.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 */
int set_chunk_cache_handler(iosystem_desc_t *ios)
{
    int iosysid;
    int iotype;
    PIO_Offset size;
    PIO_Offset nelems;
    float preemption;
    int mpierr = MPI_SUCCESS;  /* Return code from MPI function codes. */
    int ret; /* Return code. */
    
    LOG((1, "set_chunk_cache_handler called"));    
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&iosysid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&iotype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&size, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&nelems, 1, MPI_OFFSET, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&preemption, 1, MPI_FLOAT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "set_chunk_cache_handler got params iosysid = %d iotype = %d size = %d "
         "nelems = %d preemption = %g", iosysid, iotype, size, nelems, preemption));

    /* Call the function. */
    if ((ret = PIOc_set_chunk_cache(iosysid, iotype, size, nelems, preemption)))
        return ret;
    
    LOG((1, "set_chunk_cache_handler succeeded!"));
    return PIO_NOERR;
}

/** 
 * This function is run on the IO tasks to get the chunk cache
 * parameters for netCDF-4.
 *
 * @param ios pointer to the iosystem_desc_t data.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 */
int get_chunk_cache_handler(iosystem_desc_t *ios)
{
    int iosysid;
    int iotype;
    char size_present, nelems_present, preemption_present;    
    PIO_Offset size, *sizep;
    PIO_Offset nelems, *nelemsp;
    float preemption, *preemptionp;
    int mpierr = MPI_SUCCESS;  /* Return code from MPI function codes. */
    int ret; /* Return code. */
    
    LOG((1, "get_chunk_cache_handler called"));    
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&iosysid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&iotype, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&size_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;    
    if ((mpierr = MPI_Bcast(&nelems_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;    
    if ((mpierr = MPI_Bcast(&preemption_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;    
    LOG((1, "get_chunk_cache_handler got params iosysid = %d iotype = %d size_present = %d "
         "nelems_present = %d preemption_present = %g", iosysid, iotype, size_present,
         nelems_present, preemption_present));

    /* Set the non-NULL pointers. */
    if (size_present)
        sizep = &size;
    if (nelems_present)
        nelemsp = &nelems;
    if (preemption_present)
        preemptionp = &preemption;

    /* Call the function. */
    if ((ret = PIOc_get_chunk_cache(iosysid, iotype, sizep, nelemsp, preemptionp)))
        return ret;
    
    LOG((1, "get_chunk_cache_handler succeeded!"));
    return PIO_NOERR;
}

/** 
 * This function is run on the IO tasks to get the variable chunk
 * cache parameters for netCDF-4.
 *
 * @param ios pointer to the iosystem_desc_t data.
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 */
int get_var_chunk_cache_handler(iosystem_desc_t *ios)
{
    int ncid;
    int varid;
    char size_present, nelems_present, preemption_present;    
    PIO_Offset size, *sizep;
    PIO_Offset nelems, *nelemsp;
    float preemption, *preemptionp;
    int mpierr = MPI_SUCCESS;  /* Return code from MPI function codes. */
    int ret; /* Return code. */
    
    LOG((1, "get_var_chunk_cache_handler called"));    
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&ncid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&varid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    if ((mpierr = MPI_Bcast(&size_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;    
    if ((mpierr = MPI_Bcast(&nelems_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;    
    if ((mpierr = MPI_Bcast(&preemption_present, 1, MPI_CHAR, 0, ios->intercomm)))
        return PIO_EIO;    
    LOG((1, "get_var_chunk_cache_handler got params ncid = %d varid = %d size_present = %d "
         "nelems_present = %d preemption_present = %g", ncid, varid, size_present,
         nelems_present, preemption_present));

    /* Set the non-NULL pointers. */
    if (size_present)
        sizep = &size;
    if (nelems_present)
        nelemsp = &nelems;
    if (preemption_present)
        preemptionp = &preemption;

    /* Call the function. */
    if ((ret = PIOc_get_var_chunk_cache(ncid, varid, sizep, nelemsp, preemptionp)))
        return ret;
    
    LOG((1, "get_var_chunk_cache_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is run on the IO tasks to free the decomp hanlder.
 * NOTE: not yet implemented
 *
 * @param ios pointer to the iosystem_desc_t data.
 *
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int freedecomp_handler(iosystem_desc_t *ios)
{
    return PIO_NOERR;
}

/** Handle the finalize call.
 *
 * @param ios pointer to the iosystem info
 * @param index
 * @returns 0 for success, PIO_EIO for MPI Bcast errors, or error code
 * from netCDF base function.
 * @internal
 */
int finalize_handler(iosystem_desc_t *ios, int index)
{
    int iosysid;
    int mpierr;
    int ret;

    LOG((1, "finalize_handler called index = %d", index));
    assert(ios);

    /* Get the parameters for this function that the the comp master
     * task is broadcasting. */
    if ((mpierr = MPI_Bcast(&iosysid, 1, MPI_INT, 0, ios->intercomm)))
        return PIO_EIO;
    LOG((1, "finalize_handler got parameter iosysid = %d", iosysid));

    /* Call the close file function. */
    LOG((2, "finalize_handler calling PIOc_finalize for iosysid = %d",
         iosysid));
    if ((ret = PIOc_finalize(iosysid)))
        return ret;

    LOG((1, "finalize_handler succeeded!"));
    return PIO_NOERR;
}

/** This function is called if no other handler exists. I'm not
 * actually sure this function should exist.
 *
 * @param ios pointer to the iosystem info
 * @param msg the unhandled message
 * @returns always returns 0
 */
int pio_callback_handler(iosystem_desc_t *ios, int msg)
{
    assert(ios);
    return PIO_NOERR;
}

/** This function is called by the IO tasks.  This function will not
 * return, unless there is an error.
 *
 * @param io_rank
 * @param component_count number of computation components
 * @param iosys pointer to pointer to iosystem info
 * @param io_comm MPI communicator for IO
 * @returns 0 for success, error code otherwise.
 */
int pio_msg_handler2(int io_rank, int component_count, iosystem_desc_t **iosys,
                     MPI_Comm io_comm)
{
    iosystem_desc_t *my_iosys;
    int msg = 0;
    MPI_Request req[component_count];
    MPI_Status status;
    int index;
    int mpierr;
    int ret = PIO_NOERR;
    int open_components = component_count;

    LOG((1, "pio_msg_handler2 called"));
    assert(iosys);

    /* Have IO comm rank 0 (the ioroot) register to receive
     * (non-blocking) for a message from each of the comproots. */
    if (!io_rank)
    {
        for (int cmp = 0; cmp < component_count; cmp++)
        {
            my_iosys = iosys[cmp];
            LOG((1, "about to call MPI_Irecv union_comm = %d", my_iosys->union_comm));
            if ((mpierr = MPI_Irecv(&msg, 1, MPI_INT, my_iosys->comproot, MPI_ANY_TAG,
                                    my_iosys->union_comm, &req[cmp])))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            LOG((1, "MPI_Irecv req[%d] = %d", cmp, req[cmp]));
        }
    }

    /* If the message is not -1, keep processing messages. */
    while (msg != -1)
    {
        LOG((3, "pio_msg_handler2 at top of loop"));

        /* Wait until any one of the requests are complete. Once it
         * returns, the Waitany function automatically sets the
         * appropriate member of the req array to MPI_REQUEST_NULL. */
        if (!io_rank)
        {
            LOG((1, "about to call MPI_Waitany req[0] = %d MPI_REQUEST_NULL = %d\n",
                 req[0], MPI_REQUEST_NULL));
            for (int c = 0; c < component_count; c++)
                LOG((2, "req[%d] = %d", c, req[c]));
            if ((mpierr = MPI_Waitany(component_count, req, &index, &status)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            LOG((3, "Waitany returned index = %d req[%d] = %d", index, index, req[index]));
        }

        /* Broadcast the index of the computational component that
         * originated the request to the rest of the IO tasks. */
        LOG((3, "About to do Bcast of index = %d io_comm = %d", index, io_comm));
        if ((mpierr = MPI_Bcast(&index, 1, MPI_INT, 0, io_comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        LOG((3, "index MPI_Bcast complete index = %d", index));

        /* Set the correct iosys depending on the index. */
        my_iosys = iosys[index];

        /* Broadcast the msg value to the rest of the IO tasks. */
        LOG((3, "about to call msg MPI_Bcast my_iosys->io_comm = %d", my_iosys->io_comm));
        if ((mpierr = MPI_Bcast(&msg, 1, MPI_INT, 0, my_iosys->io_comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        LOG((1, "pio_msg_handler2 msg MPI_Bcast complete msg = %d", msg));

        /* Handle the message. This code is run on all IO tasks. */
        switch (msg)
        {
        case PIO_MSG_INQ_TYPE:
            inq_type_handler(my_iosys);
            break;
        case PIO_MSG_INQ_FORMAT:
            inq_format_handler(my_iosys);
            break;
        case PIO_MSG_CREATE_FILE:
            create_file_handler(my_iosys);
            LOG((2, "returned from create_file_handler"));
            break;
        case PIO_MSG_SYNC:
            sync_file_handler(my_iosys);
            break;
        case PIO_MSG_ENDDEF:
        case PIO_MSG_REDEF:
            LOG((2, "calling change_def_file_handler"));
            change_def_file_handler(my_iosys, msg);
            LOG((2, "returned from change_def_file_handler"));
            break;
        case PIO_MSG_OPEN_FILE:
            open_file_handler(my_iosys);
            break;
        case PIO_MSG_CLOSE_FILE:
            close_file_handler(my_iosys);
            break;
        case PIO_MSG_DELETE_FILE:
            delete_file_handler(my_iosys);
            break;
        case PIO_MSG_RENAME_DIM:
            rename_dim_handler(my_iosys);
            break;
        case PIO_MSG_RENAME_VAR:
            rename_var_handler(my_iosys);
            break;
        case PIO_MSG_RENAME_ATT:
            rename_att_handler(my_iosys);
            break;
        case PIO_MSG_DEL_ATT:
            delete_att_handler(my_iosys);
            break;
        case PIO_MSG_DEF_DIM:
            def_dim_handler(my_iosys);
            break;
        case PIO_MSG_DEF_VAR:
            def_var_handler(my_iosys);
            break;
        case PIO_MSG_DEF_VAR_CHUNKING:
            def_var_chunking_handler(my_iosys);
            break;
        case PIO_MSG_DEF_VAR_ENDIAN:
            def_var_endian_handler(my_iosys);
            break;
        case PIO_MSG_INQ_VAR_ENDIAN:
            inq_var_endian_handler(my_iosys);
            break;
        case PIO_MSG_SET_VAR_CHUNK_CACHE:
            set_var_chunk_cache_handler(my_iosys);
            break;
        case PIO_MSG_GET_VAR_CHUNK_CACHE:
            get_var_chunk_cache_handler(my_iosys);
            break;
        case PIO_MSG_INQ:
            inq_handler(my_iosys);
            break;
        case PIO_MSG_INQ_DIM:
            inq_dim_handler(my_iosys, msg);
            break;
        case PIO_MSG_INQ_DIMID:
            inq_dimid_handler(my_iosys);
            break;
        case PIO_MSG_INQ_VAR:
            inq_var_handler(my_iosys);
            break;
        case PIO_MSG_INQ_VAR_CHUNKING:
            inq_var_chunking_handler(my_iosys);
            break;
        case PIO_MSG_INQ_VAR_DEFLATE:
            inq_var_deflate_handler(my_iosys);
            break;
        case PIO_MSG_GET_ATT:
            ret = att_get_handler(my_iosys);
            break;
        case PIO_MSG_PUT_ATT:
            ret = att_put_handler(my_iosys);
            break;
        case PIO_MSG_INQ_VARID:
            inq_varid_handler(my_iosys);
            break;
        case PIO_MSG_INQ_ATT:
            inq_att_handler(my_iosys);
            break;
        case PIO_MSG_INQ_ATTNAME:
            inq_attname_handler(my_iosys);
            break;
        case PIO_MSG_INQ_ATTID:
            inq_attid_handler(my_iosys);
            break;
        case PIO_MSG_GET_VARS:
            get_vars_handler(my_iosys);
            break;
        case PIO_MSG_PUT_VARS:
            put_vars_handler(my_iosys);
            break;
        case PIO_MSG_INITDECOMP_DOF:
            initdecomp_dof_handler(my_iosys);
            break;
        case PIO_MSG_WRITEDARRAY:
            writedarray_handler(my_iosys);
            break;
        case PIO_MSG_READDARRAY:
            readdarray_handler(my_iosys);
            break;
        case PIO_MSG_SETERRORHANDLING:
            seterrorhandling_handler(my_iosys);
            break;
        case PIO_MSG_SET_CHUNK_CACHE:
            set_chunk_cache_handler(my_iosys);
            break;
        case PIO_MSG_GET_CHUNK_CACHE:
            get_chunk_cache_handler(my_iosys);
            break;
        case PIO_MSG_FREEDECOMP:
            freedecomp_handler(my_iosys);
            break;
        case PIO_MSG_EXIT:
            finalize_handler(my_iosys, index);
            msg = -1;
            break;
        default:
            pio_callback_handler(my_iosys, msg);
        }

        /* If an error was returned by the handler, do something! */
        LOG((3, "pio_msg_handler2 checking error ret = %d", ret));
        if (ret)
            MPI_Finalize();

        LOG((3, "pio_msg_handler2 getting ready to listen"));

        /* Unless finalize was called, listen for another msg from the
         * component whose message we just handled. */
        if (!io_rank && msg != -1)
        {
            my_iosys = iosys[index];
            LOG((3, "pio_msg_handler2 about to Irecv index = %d comproot = %d union_comm = %d",
                 index, my_iosys->comproot, my_iosys->union_comm));
            if ((mpierr = MPI_Irecv(&msg, 1, MPI_INT, my_iosys->comproot, MPI_ANY_TAG, my_iosys->union_comm,
                                    &req[index])))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            LOG((3, "pio_msg_handler2 called MPI_Irecv req[%d] = %d\n", index, req[index]));
        }

        LOG((3, "pio_msg_handler2 done msg = %d open_components = %d",
             msg, open_components));

        /* If there are no more open components, exit. */
        if (msg == -1)
            if (--open_components)
                msg = PIO_MSG_EXIT;
    }

    LOG((3, "returning from pio_msg_handler2"));
    return PIO_NOERR;
}

/** 
 * Library initialization used when IO tasks are distinct from compute
 * tasks.
 *
 * This is a collective call.  Input parameters are read on
 * comp_rank=0 values on other tasks are ignored.  This variation of
 * PIO_init sets up a distinct set of tasks to handle IO, these tasks
 * do not return from this call.  Instead they go to an internal loop
 * and wait to receive further instructions from the computational
 * tasks.
 *
 * Sequence of Events to do Asynch I/O
 * -----------------------------------
 *
 * Here is the sequence of events that needs to occur when an IO
 * operation is called from the collection of compute tasks.  I'm
 * going to use pio_put_var because write_darray has some special
 * characteristics that make it a bit more complicated...
 *
 * Compute tasks call pio_put_var with an integer argument
 *
 * The MPI_Send sends a message from comp_rank=0 to io_rank=0 on
 * union_comm (a comm defined as the union of io and compute tasks)
 * msg is an integer which indicates the function being called, in
 * this case the msg is PIO_MSG_PUT_VAR_INT
 *
 * The iotasks now know what additional arguments they should expect
 * to receive from the compute tasks, in this case a file handle, a
 * variable id, the length of the array and the array itself.
 *
 * The iotasks now have the information they need to complete the
 * operation and they call the pio_put_var routine.  (In pio1 this bit
 * of code is in pio_get_put_callbacks.F90.in)
 *
 * After the netcdf operation is completed (in the case of an inq or
 * get operation) the result is communicated back to the compute
 * tasks.
 *
 * @param world the communicator containing all the available tasks.
 *
 * @param num_io_procs the number of processes for the IO component.
 *
 * @param io_proc_list an array of lenth num_io_procs with the
 * processor number for each IO processor. If NULL then the IO
 * processes are assigned starting at processes 0.
 *
 * @param component_count number of computational components
 *
 * @param num_procs_per_comp an array of int, of length
 * component_count, with the number of processors in each computation
 * component.
 *
 * @param proc_list an array of arrays containing the processor
 * numbers for each computation component. If NULL then the
 * computation components are assigned processors sequentially
 * starting with processor num_io_procs.
 *
 * @param iosysidp pointer to array of length component_count that
 * gets the iosysid for each component.
 *
 * @return PIO_NOERR on success, error code otherwise.
 * @ingroup PIO_init
 */
int PIOc_Init_Async(MPI_Comm world, int num_io_procs, int *io_proc_list,
                    int component_count, int *num_procs_per_comp, int **proc_list,
                    int *iosysidp)
{
    int my_rank;
    MPI_Comm newcomm;
    int **my_proc_list;
    int *my_io_proc_list;
    int ret;

    /* Check input parameters. */
    if (num_io_procs < 1 || component_count < 1 || !num_procs_per_comp ||
        !iosysidp)
        return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

    /* Temporarily limit to one computational component. */
    if (component_count > 1)
        return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

    /* Turn on the logging system for PIO. */
    pio_init_logging();
    LOG((1, "PIOc_Init_Async component_count = %d", component_count));

    /* If the user did not supply a list of process numbers to use for
     * IO, create it. */
    if (!io_proc_list)
    {
        if (!(my_io_proc_list = malloc(num_io_procs * sizeof(int))))
            return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);
        for (int p = 0; p < num_io_procs; p++)
            my_io_proc_list[p] = p;
    }
    else
        my_io_proc_list = io_proc_list;

    /* If the user did not provide a list of processes for each
     * component, create one. */
    if (!proc_list)
    {
        int last_proc = 0;

        /* Allocate space for array of arrays. */
        if (!(my_proc_list = malloc((component_count + 1) * sizeof(int *))))
            return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);

        /* Fill the array of arrays. */
        for (int cmp = 0; cmp < component_count + 1; cmp++)
        {
            LOG((3, "calculating processors for component %d", cmp));

            /* Allocate space for each array. */
            if (!(my_proc_list[cmp] = malloc(num_procs_per_comp[cmp] * sizeof(int))))
                return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);

            int proc;
            for (proc = last_proc; proc < num_procs_per_comp[cmp] + last_proc; proc++)
            {
                my_proc_list[cmp][proc - last_proc] = proc;
                LOG((3, "my_proc_list[%d][%d] = %d", cmp, proc - last_proc, proc));
            }
            last_proc = proc;
        }
    }
    else
        my_proc_list = proc_list;

    /* Get rank of this task. */
    if ((ret = MPI_Comm_rank(world, &my_rank)))
        return check_mpi(NULL, ret, __FILE__, __LINE__);

    /* Is this process in the IO component? */
    int pidx;
    for (pidx = 0; pidx < num_procs_per_comp[0]; pidx++)
        if (my_rank == my_proc_list[0][pidx])
            break;
    int in_io = (pidx == num_procs_per_comp[0]) ? 0 : 1;
    LOG((3, "in_io = %d", in_io));

    /* Allocate struct to hold io system info for each computation component. */
    /* Allocate struct to hold io system info for each component. */
    iosystem_desc_t *iosys[component_count], *my_iosys;
    for (int cmp1 = 0; cmp1 < component_count; cmp1++)
        if (!(iosys[cmp1] = (iosystem_desc_t *)calloc(1, sizeof(iosystem_desc_t))))
            return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    /* Create group for world. */
    MPI_Group world_group;
    if ((ret = MPI_Comm_group(world, &world_group)))
        return check_mpi(NULL, ret, __FILE__, __LINE__);
    LOG((3, "world group created\n"));

    /* We will create a group for the IO component. */
    MPI_Group io_group;

    /* The shared IO communicator. */
    MPI_Comm io_comm;

    /* Rank of current process in IO communicator. */
    int io_rank = -1;

    /* Set to MPI_ROOT on master process, MPI_PROC_NULL on other
     * processes. */
    int iomaster;

    /* Create a group for the IO component. */
    if ((ret = MPI_Group_incl(world_group, num_io_procs, my_io_proc_list, &io_group)))
        return check_mpi(NULL, ret, __FILE__, __LINE__);
    LOG((3, "created IO group - io_group = %d group empty is %d", io_group, MPI_GROUP_EMPTY));
    for (int p = 0; p < num_io_procs; p++)
        LOG((3, "my_io_proc_list[%d] = %d", p, my_io_proc_list[p]));

    /* There is one shared IO comm. Create it. */
    if ((ret = MPI_Comm_create(world, io_group, &io_comm)))
        return check_mpi(NULL, ret, __FILE__, __LINE__);
    LOG((3, "created io comm io_comm = %d", io_comm));

    /* For processes in the IO component, get their rank within the IO
     * communicator. */
    if (in_io)
    {
        LOG((3, "about to get io rank"));
        if ((ret = MPI_Comm_rank(io_comm, &io_rank)))
            return check_mpi(NULL, ret, __FILE__, __LINE__);
        iomaster = !io_rank ? MPI_ROOT : MPI_PROC_NULL;
        LOG((3, "intracomm created for io_comm = %d io_rank = %d IO %s",
             io_comm, io_rank, iomaster == MPI_ROOT ? "MASTER" : "SERVANT"));
    }

    /* We will create a group for each component. */
    MPI_Group group[component_count + 1];

    /* We will also create a group for each component and the IO
     * component processes (i.e. a union of computation and IO
     * processes. */
    MPI_Group union_group[component_count];

    /* For each component, starting with the IO component. */
    for (int cmp = 0; cmp < component_count + 1; cmp++)
    {
        LOG((3, "processing component %d", cmp));

        /* Don't start initing iosys until after IO component. */
        if (cmp)
        {
            /* Get pointer to current iosys. */
            my_iosys = iosys[cmp - 1];

            /* Initialize some values. */
            my_iosys->io_comm = MPI_COMM_NULL;
            my_iosys->comp_comm = MPI_COMM_NULL;
            my_iosys->union_comm = MPI_COMM_NULL;
            my_iosys->intercomm = MPI_COMM_NULL;
            my_iosys->my_comm = MPI_COMM_NULL;
            my_iosys->async_interface = 1;
            my_iosys->error_handler = PIO_INTERNAL_ERROR;
            my_iosys->num_comptasks = num_procs_per_comp[cmp];
            my_iosys->num_iotasks = num_procs_per_comp[0];
            my_iosys->compgroup = MPI_GROUP_NULL;
            my_iosys->iogroup = MPI_GROUP_NULL;

            /* The rank of the computation leader in the union comm. */
            my_iosys->comproot = num_procs_per_comp[0];
            LOG((3, "my_iosys->comproot = %d", my_iosys->comproot));

            /* Create an MPI info object. */
            if ((ret = MPI_Info_create(&my_iosys->info)))
                return check_mpi(NULL, ret, __FILE__, __LINE__);
        }

        /* Create a group for this component. */
        if ((ret = MPI_Group_incl(world_group, num_procs_per_comp[cmp], my_proc_list[cmp],
                                  &group[cmp])))
            return check_mpi(NULL, ret, __FILE__, __LINE__);
        LOG((3, "created component MPI group - group[%d] = %d", cmp, group[cmp]));

        /* For all the computation components (i.e. cmp != 0), create
         * a union group with their processors and the processors of
         * the (shared) IO component. */
        if (cmp)
        {
            /* How many processors in the union comm? */
            int nprocs_union = num_procs_per_comp[0] + num_procs_per_comp[cmp];

            /* This will hold proc numbers from both computation and IO
             * components. */
            int proc_list_union[nprocs_union];

            /* Add proc numbers from IO. */
            for (int p = 0; p < num_procs_per_comp[0]; p++)
                proc_list_union[p] = my_proc_list[0][p];

            /* Add proc numbers from computation component. */
            for (int p = 0; p < num_procs_per_comp[cmp]; p++)
                proc_list_union[p + num_procs_per_comp[0]] = my_proc_list[cmp][p];

            /* Create the union group. */
            if ((ret = MPI_Group_incl(world_group, nprocs_union, proc_list_union,
                                      &union_group[cmp - 1])))
                return check_mpi(NULL, ret, __FILE__, __LINE__);
            LOG((3, "created union MPI_group - union_group[%d] = %d with %d procs", cmp, union_group[cmp-1], nprocs_union));
        }

        /* Remember whether this process is in the IO component. */
        if (cmp)
            my_iosys->ioproc = in_io;

        /* Is this process in this computation component (which is the
         * IO component if cmp == 0)? */
        int in_cmp = 0;
        for (pidx = 0; pidx < num_procs_per_comp[cmp]; pidx++)
            if (my_rank == my_proc_list[cmp][pidx])
                break;
        in_cmp = (pidx == num_procs_per_comp[cmp]) ? 0 : 1;
        LOG((3, "pidx = %d num_procs_per_comp[%d] = %d in_cmp = %d",
             pidx, cmp, num_procs_per_comp[cmp], in_cmp));

        /* Create an intracomm for this component. Only processes in
         * the component need to participate in the intracomm create
         * call. */
        /* Create the intracomm from the group. */
        LOG((3, "creating intracomm cmp = %d from group[%d] = %d", cmp, cmp, group[cmp]));

        /* We handle the IO comm differently (cmp == 0). */
        if (!cmp)
        {
            /* LOG((3, "about to create io comm")); */
            /* if ((ret = MPI_Comm_create_group(world, group[cmp], cmp, &io_comm))) */
            /*     return check_mpi(NULL, ret, __FILE__, __LINE__); */
            /* LOG((3, "about to get io rank"));                 */
            /* if ((ret = MPI_Comm_rank(io_comm, &io_rank))) */
            /*     return check_mpi(NULL, ret, __FILE__, __LINE__); */
            /* iomaster = !io_rank ? MPI_ROOT : MPI_PROC_NULL; */
            /* LOG((3, "intracomm created for cmp = %d io_comm = %d io_rank = %d IO %s", */
            /*      cmp, io_comm, io_rank, iomaster == MPI_ROOT ? "MASTER" : "SERVANT")); */
        }
        else
        {
            if ((ret = MPI_Comm_create(world, group[cmp], &my_iosys->comp_comm)))
                return check_mpi(NULL, ret, __FILE__, __LINE__);
            if (in_cmp)
            {
                if ((ret = MPI_Comm_rank(my_iosys->comp_comm, &my_iosys->comp_rank)))
                    return check_mpi(NULL, ret, __FILE__, __LINE__);
                my_iosys->compmaster = my_iosys->comp_rank ? MPI_PROC_NULL : MPI_ROOT;
                LOG((3, "intracomm created for cmp = %d comp_comm = %d comp_rank = %d comp %s",
                     cmp, my_iosys->comp_comm, my_iosys->comp_rank,
                     my_iosys->compmaster == MPI_ROOT ? "MASTER" : "SERVANT"));
            }
        }


        /* If this is the IO component, remember the
         * comm. Otherwise make a copy of the comm for each
         * component. */
        if (in_io)
            if (cmp)
            {
                LOG((3, "making a dup of io_comm = %d io_rank = %d", io_comm, io_rank));
                if ((ret = MPI_Comm_dup(io_comm, &my_iosys->io_comm)))
                    return check_mpi(NULL, ret, __FILE__, __LINE__);
                LOG((3, "dup of io_comm = %d io_rank = %d", my_iosys->io_comm, io_rank));
                my_iosys->iomaster = iomaster;
                my_iosys->io_rank = io_rank;
                my_iosys->ioroot = 0;
                my_iosys->comp_idx = cmp - 1;
            }

        /* All the processes in this component, and the IO component,
         * are part of the union_comm. */
        if (cmp)
        {
            if (in_io || in_cmp)
            {
                LOG((3, "my_iosys->io_comm = %d group = %d", my_iosys->io_comm, union_group[cmp-1]));
                /* Create a group for the union of the IO component
                 * and one of the computation components. */
                if ((ret = MPI_Comm_create(world, union_group[cmp - 1],
                                           &my_iosys->union_comm)))
                    return check_mpi(NULL, ret, __FILE__, __LINE__);

                if ((ret = MPI_Comm_rank(my_iosys->union_comm, &my_iosys->union_rank)))
                    return check_mpi(NULL, ret, __FILE__, __LINE__);

                /* Set my_comm to union_comm for async. */
                my_iosys->my_comm = my_iosys->union_comm;
                LOG((3, "intracomm created for union cmp = %d union_rank = %d union_comm = %d",
                     cmp, my_iosys->union_rank, my_iosys->union_comm));

                if (in_io)
                {
                    LOG((3, "my_iosys->io_comm = %d", my_iosys->io_comm));
                    /* Create the intercomm from IO to computation component. */
                    LOG((3, "about to create intercomm for IO component to cmp = %d "
                         "my_iosys->io_comm = %d", cmp, my_iosys->io_comm));
                    if ((ret = MPI_Intercomm_create(my_iosys->io_comm, 0, my_iosys->union_comm,
                                                    my_proc_list[cmp][0], 0,
                                                    &my_iosys->intercomm)))
                        return check_mpi(NULL, ret, __FILE__, __LINE__);
                }
                else
                {
                    /* Create the intercomm from computation component to IO component. */
                    LOG((3, "about to create intercomm for cmp = %d my_iosys->comp_comm = %d", cmp,
                         my_iosys->comp_comm));
                    if ((ret = MPI_Intercomm_create(my_iosys->comp_comm, 0, my_iosys->union_comm,
                                                    my_proc_list[0][0], 0, 
						    &my_iosys->intercomm)))
                        return check_mpi(NULL, ret, __FILE__, __LINE__);
                }
                LOG((3, "intercomm created for cmp = %d", cmp));
            }

            /* Add this id to the list of PIO iosystem ids. */
            iosysidp[cmp - 1] = pio_add_to_iosystem_list(my_iosys);
            LOG((2, "new iosys ID added to iosystem_list iosysid = %d\n", iosysidp[cmp - 1]));
        }
    }

    /* Now call the function from which the IO tasks will not return
     * until the PIO_MSG_EXIT message is sent. This will handle all
     * components. */
    if (in_io)
    {
        LOG((2, "Starting message handler io_rank = %d component_count = %d",
             io_rank, component_count));
        if ((ret = pio_msg_handler2(io_rank, component_count, iosys, io_comm)))
            return ret;
        LOG((2, "Returned from pio_msg_handler2() ret = %d", ret));
    }

    /* Free resources if needed. */
    LOG((2, "PIOc_Init_Async starting to free resources"));    
    if (!io_proc_list)
        free(my_io_proc_list);

    if (!proc_list)
    {
        for (int cmp = 0; cmp < component_count + 1; cmp++)
            free(my_proc_list[cmp]);
        free(my_proc_list);
    }

    /* Free MPI groups. */
    if ((ret = MPI_Group_free(&io_group)))
        return check_mpi(NULL, ret, __FILE__, __LINE__);

    for (int cmp = 0; cmp < component_count + 1; cmp++)
    {
        if ((ret = MPI_Group_free(&group[cmp])))
            return check_mpi(NULL, ret, __FILE__, __LINE__);
        if (cmp)
            if ((ret = MPI_Group_free(&union_group[cmp - 1])))
                return check_mpi(NULL, ret, __FILE__, __LINE__);
    }

    if ((ret = MPI_Group_free(&world_group)))
        return check_mpi(NULL, ret, __FILE__, __LINE__);

    LOG((2, "successfully done with PIO_Init_Async"));
    return PIO_NOERR;
}
