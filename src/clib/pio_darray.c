/** @file
 *
 * Public functions that read and write distributed arrays in PIO.
 *
 * When arrays are distributed, each processor holds some of the
 * array. Only by combining the distributed arrays from all processor
 * can the full array be obtained.
 *
 * @author Jim Edwards
 */
#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/* 10MB default limit. */
PIO_Offset pio_buffer_size_limit = 10485760;

/* Global buffer pool pointer. */
void *CN_bpool = NULL;

/* Maximum buffer usage. */
PIO_Offset maxusage = 0;

/**
 * Set the PIO IO node data buffer size limit.
 *
 * The pio_buffer_size_limit will only apply to files opened after
 * the setting is changed.
 *
 * @param limit the size of the buffer on the IO nodes
 * @return The previous limit setting.
 */
PIO_Offset PIOc_set_buffer_size_limit(PIO_Offset limit)
{
    PIO_Offset oldsize = pio_buffer_size_limit;

    /* If the user passed a valid size, use it. */
    if (limit > 0)
        pio_buffer_size_limit = limit;

    return oldsize;
}

/**
 * Write one or more arrays with the same IO decomposition to the
 * file.
 *
 * This funciton is similar to PIOc_write_darray(), but allows the
 * caller to use their own data buffering (instead of using the
 * buffering implemented in PIOc_write_darray()).
 *
 * @param ncid identifies the netCDF file.
 * @param varids an array of length nvars containing the variable ids to
 * be written.
 * @param ioid the I/O description ID as passed back by
 * PIOc_InitDecomp().
 * @param nvars the number of variables to be written with this
 * call.
 * @param arraylen the length of the array to be written. This is the
 * length of the distrubited array. That is, the length of the portion
 * of the data that is on the processor. The same arraylen is used for
 * all variables in the call.
 * @param array pointer to the data to be written. This is a pointer
 * to an array of arrays with the distributed portion of the array
 * that is on this processor. There are nvars arrays of data, and each
 * array of data contains one record worth of data for that variable.
 * @param frame an array of length nvars with the frame or record
 * dimension for each of the nvars variables in IOBUF. NULL if this
 * iodesc contains non-record vars.
 * @param fillvalue pointer an array (of length nvars) of pointers to
 * the fill value to be used for missing data.
 * @param flushtodisk non-zero to cause buffers to be flushed to disk.
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_write_darray
 */
int PIOc_write_darray_multi(int ncid, const int *varids, int ioid, int nvars,
                            PIO_Offset arraylen, void *array, const int *frame,
                            void **fillvalue, bool flushtodisk)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    io_desc_t *iodesc;     /* Pointer to IO description information. */
    int vsize;             /* size in bytes of the given data. */
    int rlen;              /* total data buffer size. */
    var_desc_t *vdesc0;    /* pointer to var_desc structure for each var. */
    int mpierr;            /* Return code from MPI functions. */
    int ierr;              /* Return code. */

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);
    ios = file->iosystem;

    /* Check inputs. */
    if (nvars <= 0 || !varids)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);
    for (int v = 0; v < nvars; v++)
        if (varids[v] < 0 || varids[v] > PIO_MAX_VARS)
            return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    LOG((1, "PIOc_write_darray_multi ncid = %d ioid = %d nvars = %d arraylen = %ld "
         "flushtodisk = %d",
         ncid, ioid, nvars, arraylen, flushtodisk));

    /* Check that we can write to this file. */
    if (!(file->mode & PIO_WRITE))
        return pio_err(ios, file, PIO_EPERM, __FILE__, __LINE__);

    /* Get iodesc. */
    if (!(iodesc = pio_get_iodesc_from_id(ioid)))
        return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);
    pioassert(iodesc->rearranger == PIO_REARR_BOX || iodesc->rearranger == PIO_REARR_SUBSET,
              "unknown rearranger", __FILE__, __LINE__);

    /* For netcdf serial writes we collect the data on io nodes and
     * then move that data one node at a time to the io master node
     * and write (or read). The buffer size on io task 0 must be as
     * large as the largest used to accommodate this serial io
     * method.  */
    vdesc0 = file->varlist + varids[0];

    /* if the buffer is already in use in pnetcdf we need to flush first */
    if (file->iotype == PIO_IOTYPE_PNETCDF && vdesc0->iobuf)
	flush_output_buffer(file, 1, 0);

    pioassert(!vdesc0->iobuf, "buffer overwrite",__FILE__, __LINE__);

    /* Determine total size of aggregated data (all vars/records). */
    rlen = 0;
    if (iodesc->llen > 0)
        rlen = iodesc->maxiobuflen * nvars;

    /* Currently there are two rearrangers box=1 and subset=2. */
    LOG((2, "iodesc->rearranger = %d iodesc->needsfill = %d\n", iodesc->rearranger,
         iodesc->needsfill));
    if (rlen > 0)
    {
        /* Get the size of the MPI type. */
        if ((mpierr = MPI_Type_size(iodesc->basetype, &vsize)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
        LOG((3, "rlen = %d vsize = %d", rlen, vsize));

        /* Allocate memory for the buffer for all vars/records. */
        if (!(vdesc0->iobuf = bget((size_t)vsize * (size_t)rlen)))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
        LOG((3, "allocated %lld bytes for variable buffer", (size_t)rlen * (size_t)vsize));

        /* If fill values are desired, and we're using the BOX
         * rearranger, insert fill values. */
        if (iodesc->needsfill && iodesc->rearranger == PIO_REARR_BOX)
            for (int nv = 0; nv < nvars; nv++)
                for (int i = 0; i < iodesc->maxiobuflen; i++)
                    memcpy(&((char *)vdesc0->iobuf)[vsize * (i + nv * iodesc->maxiobuflen)],
                           &((char *)fillvalue)[nv * vsize], vsize);
    }else if(file->iotype == PIO_IOTYPE_PNETCDF){
	/* this assures that iobuf is allocated on all iotasks thus assuring that the flush_output_buffer call
	 above is called collectively (from all iotasks) */
        if (!(vdesc0->iobuf = bget(1)))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
        LOG((3, "allocated %lld bytes for variable buffer", (size_t)rlen * (size_t)vsize));
    }

    /* Move data from compute to IO tasks. */
    if ((ierr = rearrange_comp2io(ios, iodesc, array, vdesc0->iobuf, nvars)))
        return pio_err(ios, file, ierr, __FILE__, __LINE__);

    /* Write the darray based on the iotype. */
    LOG((2, "about to write darray for iotype = %d", file->iotype));
    switch (file->iotype)
    {
    case PIO_IOTYPE_NETCDF4P:
    case PIO_IOTYPE_PNETCDF:
        if ((ierr = pio_write_darray_multi_nc(file, nvars, varids, iodesc->ndims, iodesc->basetype,
                                              iodesc->maxregions, iodesc->firstregion, iodesc->llen,
                                              iodesc->num_aiotasks, vdesc0->iobuf, frame)))
            return pio_err(ios, file, ierr, __FILE__, __LINE__);
        break;
    case PIO_IOTYPE_NETCDF4C:
    case PIO_IOTYPE_NETCDF:
        if ((ierr = pio_write_darray_multi_nc_serial(file, nvars, varids, iodesc->ndims, iodesc->basetype,
                                                     iodesc->maxregions, iodesc->firstregion, iodesc->llen,
                                                     iodesc->num_aiotasks, vdesc0->iobuf, frame)))
            return pio_err(ios, file, ierr, __FILE__, __LINE__);

        break;
    default:
        return pio_err(NULL, NULL, PIO_EBADIOTYPE, __FILE__, __LINE__);
    }

    /* For PNETCDF the iobuf is freed in flush_output_buffer() */
    if (file->iotype != PIO_IOTYPE_PNETCDF)
    {
        /* Release resources. */
        if (vdesc0->iobuf)
        {
            brel(vdesc0->iobuf);
            vdesc0->iobuf = NULL;
        }
    }

    /* The box rearranger will always have data (it could be fill
     * data) to fill the entire array - that is the aggregate start
     * and count values will completely describe one unlimited
     * dimension unit of the array. For the subset method this is not
     * necessarily the case, areas of missing data may never be
     * written. In order to make sure that these areas are given the
     * missing value a 'holegrid' is used to describe the missing
     * points. This is generally faster than the netcdf method of
     * filling the entire array with missing values before overwriting
     * those values later. */
    if (iodesc->rearranger == PIO_REARR_SUBSET && iodesc->needsfill)
    {
        LOG((2, "nvars = %d holegridsize = %ld iodesc->needsfill = %d\n", nvars,
             iodesc->holegridsize, iodesc->needsfill));

	pioassert(!vdesc0->fillbuf, "buffer overwrite",__FILE__, __LINE__);

        /* Get a buffer. */
	if (ios->io_rank == 0)
	    vdesc0->fillbuf = bget(iodesc->maxholegridsize * vsize * nvars);
	else if (iodesc->holegridsize > 0)
	    vdesc0->fillbuf = bget(iodesc->holegridsize * vsize * nvars);

        /* copying the fill value into the data buffer for the box
         * rearranger. This will be overwritten with data where
         * provided. */
        for (int nv = 0; nv < nvars; nv++)
            for (int i = 0; i < iodesc->holegridsize; i++)
                memcpy(&((char *)vdesc0->fillbuf)[vsize * (i + nv * iodesc->holegridsize)],
                       &((char *)fillvalue)[vsize * nv], vsize);

        /* Write the darray based on the iotype. */
        switch (file->iotype)
        {
        case PIO_IOTYPE_PNETCDF:
        case PIO_IOTYPE_NETCDF4P:
            if ((ierr = pio_write_darray_multi_nc(file, nvars, varids,
                                                  iodesc->ndims, iodesc->basetype, iodesc->maxfillregions,
                                                  iodesc->fillregion, iodesc->holegridsize,
                                                  iodesc->num_aiotasks, vdesc0->fillbuf, frame)))
                return pio_err(ios, file, ierr, __FILE__, __LINE__);
            break;
        case PIO_IOTYPE_NETCDF4C:
        case PIO_IOTYPE_NETCDF:
            if ((ierr = pio_write_darray_multi_nc_serial(file, nvars, varids, iodesc->ndims, iodesc->basetype,
                                                         iodesc->maxfillregions, iodesc->fillregion,
                                                         iodesc->holegridsize,
                                                         iodesc->num_aiotasks, vdesc0->fillbuf, frame)))
                return pio_err(ios, file, ierr, __FILE__, __LINE__);
            break;
        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }

        /* For PNETCDF fillbuf is freed in flush_output_buffer() */
        if (file->iotype != PIO_IOTYPE_PNETCDF)
        {
            /* Free resources. */
            if (vdesc0->fillbuf)
            {
                brel(vdesc0->fillbuf);
                vdesc0->fillbuf = NULL;
            }
        }
    }

    /* Flush data to disk. */
    if (ios->ioproc && file->iotype == PIO_IOTYPE_PNETCDF)
        if ((ierr = flush_output_buffer(file, flushtodisk, 0)))
            return pio_err(ios, file, ierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * Write a distributed array to the output file.
 *
 * This routine aggregates output on the compute nodes and only sends
 * it to the IO nodes when the compute buffer is full or when a flush
 * is triggered.
 *
 * @param ncid the ncid of the open netCDF file.
 * @param varid the ID of the variable that these data will be written
 * to.
 * @param ioid the I/O description ID as passed back by
 * PIOc_InitDecomp().
 * @param arraylen the length of the array to be written.  This should
 * be at least the length of the local component of the distrubited
 * array. (Any values beyond length of the local component will be
 * ignored.)
 * @param array pointer to an array of length arraylen with the data
 * to be written. This is a pointer to the distributed portion of the
 * array that is on this task.
 * @param fillvalue pointer to the fill value to be used for
 * missing data.
 * @returns 0 for success, non-zero error code for failure.
 * @ingroup PIO_write_darray
 */
int PIOc_write_darray(int ncid, int varid, int ioid, PIO_Offset arraylen, void *array,
                      void *fillvalue)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Info about file we are writing to. */
    io_desc_t *iodesc;     /* The IO description. */
    var_desc_t *vdesc;     /* Info about the var being written. */
    void *bufptr;          /* A data buffer. */
    MPI_Datatype vtype;    /* The MPI type of the variable. */
    wmulti_buffer *wmb;    /* The write multi buffer for one or more vars. */
    int tsize;             /* Size of MPI type. */
    bool recordvar;        /* True if this is a record variable. */
    int needsflush = 0;    /* True if we need to flush buffer. */
    bufsize totfree;       /* Amount of free space in the buffer. */
    bufsize maxfree;       /* Max amount of free space in buffer. */
    int mpierr = MPI_SUCCESS;  /* Return code from MPI functions. */
    int ierr = PIO_NOERR;  /* Return code. */

    LOG((1, "PIOc_write_darray ncid = %d varid = %d ioid = %d arraylen = %d",
         ncid, varid, ioid, arraylen));

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);
    ios = file->iosystem;

    /* Can we write to this file? */
    if (!(file->mode & PIO_WRITE))
        return pio_err(ios, file, PIO_EPERM, __FILE__, __LINE__);

    /* Get decomposition information. */
    if (!(iodesc = pio_get_iodesc_from_id(ioid)))
        return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);

    /* Get var description. */
    vdesc = file->varlist + varid;
    LOG((2, "vdesc record %d ndims %d nreqs %d", vdesc->record, vdesc->ndims, vdesc->nreqs));

    /* Is this a record variable? */
    recordvar = vdesc->record >= 0 ? true : false;
    LOG((3, "recordvar = %d", recordvar));

    /* Check that the local size of the variable passed in matches the
     * size expected by the io descriptor. */
    if (arraylen < iodesc->ndof)
        return pio_err(ios, file, PIO_EINVAL, __FILE__, __LINE__);

    if (iodesc->ndof != arraylen)
        LOG((1, "User supplied array is larger than expected, arraylen != iodesc->ndof"));

    /* Get the size of the MPI type. */
    if ((mpierr = MPI_Type_size(iodesc->basetype, &tsize)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    /* The write multi buffer wmulti_buffer is the cache on compute
       nodes that will collect and store multiple variables before
       sending them to the io nodes. Aggregating variables in this way
       leads to a considerable savings in communication
       expense. Variables in the wmb array must have the same
       decomposition and base data size and we also need to keep track
       of whether each is a recordvar (has an unlimited dimension) or
       not. */

    /* Move to end of list or the entry that matches this ioid. */
    for (wmb = &file->buffer; wmb->next && wmb->ioid != ioid; wmb = wmb->next)
        ;

    /* If this is a new wmb entry, initialize it. */
    if (wmb->ioid != ioid)
    {
        /* Allocate a buffer. */
        if (!(wmb->next = bget((bufsize)sizeof(wmulti_buffer))))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
        LOG((3, "allocated multi-buffer"));

        /* Set pointer to newly allocated buffer and initialize.*/
        wmb = wmb->next;
        wmb->next = NULL;
        wmb->ioid = ioid;
        wmb->validvars = 0;
        wmb->arraylen = arraylen;
        wmb->vid = NULL;
        wmb->data = NULL;
        wmb->frame = NULL;
        wmb->fillvalue = NULL;
    }

    /* At this point wmb should be pointing to a new or existing buffer
       so we can add the data. */
    LOG((2, "wmb->validvars = %d arraylen = %d tsize = %d\n", wmb->validvars,
         arraylen, tsize));

    /* Find out how much free, contiguous space is available. */
    bfreespace(&totfree, &maxfree);

    /* maxfree is the available memory. If that is < 10% greater than
     * the size of the current request needsflush is true. */
    if (needsflush == 0)
        needsflush = (maxfree <= 1.1 * (1 + wmb->validvars) * arraylen * tsize);

    /* Tell all tasks on the computation communicator whether we need
     * to flush data. */
    if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &needsflush, 1,  MPI_INT,  MPI_MAX,
                                ios->comp_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    LOG((2, "needsflush = %d", needsflush));

    /* Flush data if needed. */
    if (needsflush > 0)
    {
        LOG((2, "maxfree = %ld wmb->validvars = %d (1 + wmb->validvars) * arraylen * tsize = %ld "
             "totfree = %ld\n", maxfree, wmb->validvars, (1 + wmb->validvars) * arraylen * tsize,
             totfree));

#ifdef PIO_ENABLE_LOGGING
        /* Collect a debug report about buffer. */
        cn_buffer_report(ios, true);
#endif /* PIO_ENABLE_LOGGING */

        /* If needsflush == 2 flush to disk otherwise just flush to io node. */
        if ((ierr = flush_buffer(ncid, wmb, needsflush == 2)))
            return pio_err(ios, file, ierr, __FILE__, __LINE__);
    }

    /* Get memory for data. */
    if (arraylen > 0)
    {
        if (!(wmb->data = bgetr(wmb->data, (1 + wmb->validvars) * arraylen * tsize)))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
        LOG((2, "got %ld bytes for data", (1 + wmb->validvars) * arraylen * tsize));
    }

    /* vid is an array of variable ids in the wmb list, grow the list
     * and add the new entry. */
    if (!(wmb->vid = bgetr(wmb->vid, sizeof(int) * (1 + wmb->validvars))))
        return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

    /* wmb->frame is the record number, we assume that the variables
     * in the wmb list may not all have the same unlimited dimension
     * value although they usually do. */
    if (vdesc->record >= 0)
        if (!(wmb->frame = bgetr(wmb->frame, sizeof(int) * (1 + wmb->validvars))))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

    /* If we need a fill value, get it. If we are using the subset
     * rearranger and not using the netcdf fill mode then we need to
     * do an extra write to fill in the holes with the fill value. */
    if (iodesc->needsfill)
    {
        /* Get memory to hold fill value. */
        if (!(wmb->fillvalue = bgetr(wmb->fillvalue, tsize * (1 + wmb->validvars))))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

        /* If the user passed a fill value, use that, otherwise use
         * the default fill value of the netCDF type. Copy the fill
         * value to the buffer. */
        if (fillvalue)
        {
            memcpy((char *)wmb->fillvalue + tsize * wmb->validvars, fillvalue, tsize);
            LOG((3, "copied user-provided fill value tsize = %d", tsize));
        }
        else
        {
            void *fill;
            signed char byte_fill = PIO_FILL_BYTE;
            char char_fill = PIO_FILL_CHAR;
            short short_fill = PIO_FILL_SHORT;
            int int_fill = PIO_FILL_INT;
            float float_fill = PIO_FILL_FLOAT;
            double double_fill = PIO_FILL_DOUBLE;
#ifdef _NETCDF4
            unsigned char ubyte_fill = PIO_FILL_UBYTE;
            unsigned short ushort_fill = PIO_FILL_USHORT;
            unsigned int uint_fill = PIO_FILL_UINT;
            long long int64_fill = PIO_FILL_INT64;
            long long uint64_fill = PIO_FILL_UINT64;
#endif /* _NETCDF4 */
            vtype = (MPI_Datatype)iodesc->basetype;
            LOG((3, "caller did not provide fill value vtype = %d", vtype));
            switch (vtype)
            {
            case MPI_BYTE:
                fill = &byte_fill;
                break;
            case MPI_CHAR:
                fill = &char_fill;
                break;
            case MPI_SHORT:
                fill = &short_fill;
                break;
            case MPI_INT:
                fill = &int_fill;
                break;
            case MPI_FLOAT:
                fill = &float_fill;
                break;
            case MPI_DOUBLE:
                fill = &double_fill;
                break;
#ifdef _NETCDF4
            case MPI_UNSIGNED_CHAR:
                fill = &ubyte_fill;
                break;
            case MPI_UNSIGNED_SHORT:
                fill = &ushort_fill;
                break;
            case MPI_UNSIGNED:
                fill = &uint_fill;
                break;
            case MPI_LONG_LONG:
                fill = &int64_fill;
                break;
            case MPI_UNSIGNED_LONG_LONG:
                fill = &uint64_fill;
                break;
#endif /* _NETCDF4 */
            default:
                return pio_err(ios, file, PIO_EBADTYPE, __FILE__, __LINE__);
            }
            memcpy((char *)wmb->fillvalue + tsize * wmb->validvars, fill, tsize);
            LOG((3, "copied fill value"));
        }
    }

    LOG((3, "here we are"));
    /* Tell the buffer about the data it is getting. */
    wmb->arraylen = arraylen;
    wmb->vid[wmb->validvars] = varid;
    LOG((3, "wmb->validvars = %d wmb->vid[wmb->validvars] = %d", wmb->validvars,
         wmb->vid[wmb->validvars]));

    /* Copy the user-provided data to the buffer. */
    bufptr = (void *)((char *)wmb->data + arraylen * tsize * wmb->validvars);
    if (arraylen > 0)
    {
        memcpy(bufptr, array, arraylen * tsize);
        LOG((3, "copied %ld bytes of user data", arraylen * tsize));
    }

    /* Add the unlimited dimension value of this variable to the frame
     * array in wmb. */
    if (wmb->frame)
        wmb->frame[wmb->validvars] = vdesc->record;
    wmb->validvars++;

    LOG((2, "wmb->validvars = %d iodesc->maxbytes / tsize = %d iodesc->ndof = %d iodesc->llen = %d",
         wmb->validvars, iodesc->maxbytes / tsize, iodesc->ndof, iodesc->llen));

    /* Call the sync when ??? */
    if (wmb->validvars >= iodesc->maxbytes / tsize)
        PIOc_sync(ncid);

    return PIO_NOERR;
}

/**
 * Read a field from a file to the IO library.
 *
 * @param ncid identifies the netCDF file
 * @param varid the variable ID to be read
 * @param ioid: the I/O description ID as passed back by
 * PIOc_InitDecomp().
 * @param arraylen: the length of the array to be read. This
 * is the length of the distrubited array. That is, the length of
 * the portion of the data that is on the processor.
 * @param array: pointer to the data to be read. This is a
 * pointer to the distributed portion of the array that is on this
 * processor.
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_read_darray
 */
int PIOc_read_darray(int ncid, int varid, int ioid, PIO_Offset arraylen,
                     void *array)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    io_desc_t *iodesc;     /* Pointer to IO description information. */
    void *iobuf = NULL;    /* holds the data as read on the io node. */
    size_t rlen = 0;       /* the length of data in iobuf. */
    int tsize;          /* Total size. */
    int mpierr;         /* Return code from MPI functions. */
    int ierr;           /* Return code. */

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);
    ios = file->iosystem;

    /* Get the iodesc. */
    if (!(iodesc = pio_get_iodesc_from_id(ioid)))
        return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);
    pioassert(iodesc->rearranger == PIO_REARR_BOX || iodesc->rearranger == PIO_REARR_SUBSET,
              "unknown rearranger", __FILE__, __LINE__);

    /* ??? */
    if (ios->iomaster == MPI_ROOT)
        rlen = iodesc->maxiobuflen;
    else
        rlen = iodesc->llen;

    if (ios->ioproc && rlen > 0)
    {
        /* Get the MPI type size. */
        if ((mpierr = MPI_Type_size(iodesc->basetype, &tsize)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

        /* Allocate a buffer for one record. */
        if (!(iobuf = bget((size_t)tsize * rlen)))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
    }

    /* Call the correct darray read function based on iotype. */
    switch (file->iotype)
    {
    case PIO_IOTYPE_NETCDF:
    case PIO_IOTYPE_NETCDF4C:
        if ((ierr = pio_read_darray_nc_serial(file, iodesc, varid, iobuf)))
                return pio_err(ios, file, ierr, __FILE__, __LINE__);
        break;
    case PIO_IOTYPE_PNETCDF:
    case PIO_IOTYPE_NETCDF4P:
        if ((ierr = pio_read_darray_nc(file, iodesc, varid, iobuf)))
            return pio_err(ios, file, ierr, __FILE__, __LINE__);
        break;
    default:
        return pio_err(NULL, NULL, PIO_EBADIOTYPE, __FILE__, __LINE__);
    }

    /* Rearrange the data. */
    if ((ierr = rearrange_io2comp(ios, iodesc, iobuf, array)))
        return pio_err(ios, file, ierr, __FILE__, __LINE__);

    /* Free the buffer. */
    if (rlen > 0)
        brel(iobuf);

    return PIO_NOERR;
}
