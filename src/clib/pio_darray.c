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

/** Set the PIO IO node data buffer size limit.
 *
 * The pio_buffer_size_limit will only apply to files opened after
 * the setting is changed.
 *
 * @param limit the size of the buffer on the IO nodes
 *
 * @return The previous limit setting.
 */
PIO_Offset PIOc_set_buffer_size_limit(const PIO_Offset limit)
{
    PIO_Offset oldsize;
    oldsize = pio_buffer_size_limit;
    if (limit > 0)
        pio_buffer_size_limit = limit;
    return oldsize;
}

/** Write one or more arrays with the same IO decomposition to the file.
 *
 * @param ncid identifies the netCDF file
 * @param vid: an array of the variable ids to be written
 * @param ioid: the I/O description ID as passed back by
 * PIOc_InitDecomp().
 * @param nvars the number of variables to be written with this
 * decomposition
 * @param arraylen: the length of the array to be written. This
 * is the length of the distrubited array. That is, the length of
 * the portion of the data that is on the processor.
 * @param array: pointer to the data to be written. This is a
 * pointer to the distributed portion of the array that is on this
 * processor.
 * @param frame the frame or record dimension for each of the nvars
 * variables in IOBUF
 * @param fillvalue: pointer to the fill value to be used for
 * missing data.
 * @param flushtodisk
 *
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_write_darray
 */
int PIOc_write_darray_multi(const int ncid, const int *vid, const int ioid,
                            const int nvars, const PIO_Offset arraylen,
                            void *array, const int *frame, void **fillvalue,
                            bool flushtodisk)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;
    io_desc_t *iodesc;
    int vsize, rlen;
    int ierr = PIO_NOERR;
    var_desc_t *vdesc0;

    /* Check inputs. */
    if (nvars <= 0)
        return PIO_EINVAL;

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Check that we can write to this file. */
    if (! (file->mode & PIO_WRITE))
        return PIO_EPERM;

    /* Get iodesc. */
    if (!(iodesc = pio_get_iodesc_from_id(ioid)))
        return PIO_EBADID;

    vdesc0 = file->varlist + vid[0];

    //   rlen = iodesc->llen*nvars;
    rlen=0;
    if (iodesc->llen > 0)
        rlen = iodesc->maxiobuflen*nvars;

    if (vdesc0->iobuf)
        piodie("Attempt to overwrite existing io buffer",__FILE__,__LINE__);

    if (iodesc->rearranger > 0)
    {
        if (rlen > 0)
        {
            MPI_Type_size(iodesc->basetype, &vsize);

            vdesc0->iobuf = bget((size_t)vsize * (size_t)rlen);
            if (!vdesc0->iobuf)
                piomemerror(*ios, (size_t)rlen * (size_t)vsize, __FILE__, __LINE__);

            if (iodesc->needsfill && iodesc->rearranger == PIO_REARR_BOX)
            {
                if (vsize == 4)
                    for (int nv = 0; nv < nvars; nv++)
                        for (int i = 0; i < iodesc->maxiobuflen; i++)
                            ((float *) vdesc0->iobuf)[i + nv * (iodesc->maxiobuflen)] = ((float *)fillvalue)[nv];
                else if (vsize == 8)
                    for (int nv = 0; nv < nvars; nv++)
                        for (int i = 0; i < iodesc->maxiobuflen; i++)
                            ((double *)vdesc0->iobuf)[i+nv*(iodesc->maxiobuflen)] = ((double *)fillvalue)[nv];
            }
        }

        ierr = rearrange_comp2io(*ios, iodesc, array, vdesc0->iobuf, nvars);
    }/*  this is wrong, need to think about it
         else{
         vdesc0->iobuf = array;
         } */

    /* Write the darray based on the iotype. */
    switch(file->iotype)
    {
    case PIO_IOTYPE_NETCDF4P:
    case PIO_IOTYPE_PNETCDF:
        ierr = pio_write_darray_multi_nc(file, nvars, vid,
                                         iodesc->ndims, iodesc->basetype, iodesc->gsize,
                                         iodesc->maxregions, iodesc->firstregion, iodesc->llen,
                                         iodesc->maxiobuflen, iodesc->num_aiotasks,
                                         vdesc0->iobuf, frame);
        break;
    case PIO_IOTYPE_NETCDF4C:
    case PIO_IOTYPE_NETCDF:
        ierr = pio_write_darray_multi_nc_serial(file, nvars, vid,
                                                iodesc->ndims, iodesc->basetype, iodesc->gsize,
                                                iodesc->maxregions, iodesc->firstregion, iodesc->llen,
                                                iodesc->maxiobuflen, iodesc->num_aiotasks,
                                                vdesc0->iobuf, frame);

        break;
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

    if (iodesc->rearranger == PIO_REARR_SUBSET && iodesc->needsfill &&
        iodesc->holegridsize > 0)
    {
        if (vdesc0->fillbuf)
            piodie("Attempt to overwrite existing buffer",__FILE__,__LINE__);

        /* Get a buffer. */
        vdesc0->fillbuf = bget(iodesc->holegridsize * vsize * nvars);

        if (vsize == 4)
            for (int nv = 0; nv < nvars; nv++)
                for (int i = 0; i < iodesc->holegridsize; i++)
                    ((float *)vdesc0->fillbuf)[i + nv * iodesc->holegridsize] = ((float *)fillvalue)[nv];
        else if (vsize == 8)
            for (int nv = 0; nv < nvars; nv++)
                for (int i = 0; i < iodesc->holegridsize; i++)
                    ((double *)vdesc0->fillbuf)[i + nv * iodesc->holegridsize] = ((double *)fillvalue)[nv];

        /* Write the darray based on the iotype. */
        switch(file->iotype)
        {
        case PIO_IOTYPE_PNETCDF:
        case PIO_IOTYPE_NETCDF4P:
            ierr = pio_write_darray_multi_nc(file, nvars, vid,
                                             iodesc->ndims, iodesc->basetype, iodesc->gsize,
                                             iodesc->maxfillregions, iodesc->fillregion, iodesc->holegridsize,
                                             iodesc->holegridsize, iodesc->num_aiotasks,
                                             vdesc0->fillbuf, frame);
            break;
        case PIO_IOTYPE_NETCDF4C:
        case PIO_IOTYPE_NETCDF:
            ierr = pio_write_darray_multi_nc_serial(file, nvars, vid,
                                                    iodesc->ndims, iodesc->basetype, iodesc->gsize,
                                                    iodesc->maxfillregions, iodesc->fillregion, iodesc->holegridsize,
                                                    iodesc->holegridsize, iodesc->num_aiotasks,
                                                    vdesc0->fillbuf, frame);
            break;
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
    if(file->iotype == PIO_IOTYPE_PNETCDF)
        flush_output_buffer(file, flushtodisk, 0);

    return ierr;
}

/** Write a distributed array to the output file.
 *
 * This routine aggregates output on the compute nodes and only sends
 * it to the IO nodes when the compute buffer is full or when a flush
 * is triggered.
 *
 * @param ncid: the ncid of the open netCDF file.
 * @param vid: the variable ID returned by PIOc_def_var().
 * @param ioid: the I/O description ID as passed back by
 * PIOc_InitDecomp().
 * @param arraylen: the length of the array to be written. This
 * is the length of the distrubited array. That is, the length of
 * the portion of the data that is on the processor.
 * @param array: pointer to the data to be written. This is a
 * pointer to the distributed portion of the array that is on this
 * processor.
 * @param fillvalue: pointer to the fill value to be used for
 * missing data.
 *
 * @returns 0 for success, non-zero error code for failure.
 * @ingroup PIO_write_darray
 */
int PIOc_write_darray(const int ncid, const int vid, const int ioid,
                      const PIO_Offset arraylen, void *array, void *fillvalue)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;  /* Info about file we are writing to. */
    io_desc_t *iodesc;  /* The IO description. */
    var_desc_t *vdesc;  /* Info about the var being written. */
    void *bufptr;       /* A data buffer. */
    MPI_Datatype vtype; /* The MPI type of the variable. */
    wmulti_buffer *wmb; /* The write multi buffer for one or more vars. */
    int tsize;          /* Size of MPI type. */
    bool recordvar;     /* True if this is a record variable. */
    int needsflush = 0; /* True if we need to flush buffer. */
    bufsize totfree;    /* Amount of free space in the buffer. */
    bufsize maxfree;    /* Max amount of free space in buffer. */
    int ierr = PIO_NOERR; /* Return code. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */

    LOG((1, "PIOc_write_darray ncid = %d vid = %d ioid = %d arraylen = %d",
	 ncid, vid, ioid, arraylen));

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Can we write to this file? */
    if (!(file->mode & PIO_WRITE))
        return PIO_EPERM;

    /* Get iodesc. */
    if (!(iodesc = pio_get_iodesc_from_id(ioid)))
        return PIO_EBADID;

    /* Get var description. */
    if (!(vdesc = file->varlist + vid))
        return PIO_EBADID;

    /* Is this a record variable? */
    recordvar = vdesc->record >= 0 ? true : false;
    LOG((3, "recordvar = %d", recordvar));

    /* Check that the local size of the variable passed in matches the
     * size expected by the io descriptor. */
    if (iodesc->ndof != arraylen)
        piodie("ndof != arraylen",__FILE__,__LINE__);

    /* Get a pointer to the buffer space for this file. It will hold
     * data from one or more variables that fit the same
     * description. */
    wmb = &file->buffer;

    /* If the ioid is not initialized, set it. For non record vars,
     * use the negative?? */
    if (wmb->ioid == -1)
    {
        if (recordvar)
            wmb->ioid = ioid;
        else
            wmb->ioid = -(ioid);
    }
    else
    {
        /* Handle record and non-record variables differently. */
        if (recordvar)
        {
	    /* Moving to the end of the wmb linked list to add the
	     * current variable. */
            while(wmb->next && wmb->ioid != ioid)
                if (wmb->next)
                    wmb = wmb->next;
#ifdef _PNETCDF
            /* flush the previous record before starting a new one. this is collective */
            /*       if (vdesc->request != NULL && (vdesc->request[0] != NC_REQ_NULL) ||
                     (wmb->frame != NULL && vdesc->record != wmb->frame[0])){
                     needsflush = 2;  // flush to disk
                     } */
#endif
        }
        else
        {
            while(wmb->next && wmb->ioid != -(ioid))
                if (wmb->next)
                    wmb = wmb->next;
        }
    }

    /* ?? */
    if ((recordvar && wmb->ioid != ioid) || (!recordvar && wmb->ioid != -(ioid)))
    {
	/* Allocate a buffer. */
        if (!(wmb->next = (wmulti_buffer *)bget((bufsize)sizeof(wmulti_buffer))))
            piomemerror(*ios,sizeof(wmulti_buffer), __FILE__,__LINE__);

	/* Set pointer to newly allocated buffer and initialize.*/
        wmb = wmb->next;
        wmb->next = NULL;
        if (recordvar)
            wmb->ioid = ioid;
        else
            wmb->ioid = -(ioid);
        wmb->validvars = 0;
        wmb->arraylen = arraylen;
        wmb->vid = NULL;
        wmb->data = NULL;
        wmb->frame = NULL;
        wmb->fillvalue = NULL;
    }

    /* Get the size of the MPI type. */
    if ((mpierr = MPI_Type_size(iodesc->basetype, &tsize)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    LOG((2, "wmb->validvars = %d arraylen = %d tsize = %d\n", wmb->validvars,
	 arraylen, tsize));

    /* At this point wmb should be pointing to a new or existing buffer
       so we can add the data. */
    bfreespace(&totfree, &maxfree);

    /* ??? */
    if (needsflush == 0)
        needsflush = (maxfree <= 1.1 * (1 + wmb->validvars) * arraylen * tsize);

    /* Tell all tests on the computation communicator whether we need
     * to flush data. */
    if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &needsflush, 1,  MPI_INT,  MPI_MAX, ios->comp_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    /* Flush data if needed. */
    if (needsflush > 0)
    {
        LOG((2, "maxfree = %ld wmb->validvars = %d (1 + wmb->validvars) * arraylen * tsize = %ld totfree = %ld\n",
	     maxfree, wmb->validvars, (1 + wmb->validvars) * arraylen * tsize, totfree));

	/* Collect a debug report about buffer. (Shouldn't we be able to turn this off??) */
        cn_buffer_report(*ios, true);

        /* If needsflush == 2 flush to disk otherwise just flush to io node. */
        flush_buffer(ncid, wmb, needsflush == 2);
    }

    /* Get memory for data. */
    if (arraylen > 0)
        if (!(wmb->data = bgetr(wmb->data, (1 + wmb->validvars) * arraylen * tsize)))
            piomemerror(*ios, (1 + wmb->validvars) * arraylen * tsize, __FILE__, __LINE__);

    /* vid is an array of variable ids in the wmb list, grow the list
     * and add the new entry. */
    if (!(wmb->vid = (int *)bgetr(wmb->vid, sizeof(int) * (1 + wmb->validvars))))
        piomemerror(*ios, (1 + wmb->validvars) * sizeof(int), __FILE__, __LINE__);

    /* wmb->frame is the record number, we assume that the variables
     * in the wmb list may not all have the same unlimited dimension
     * value although they usually do. */
    if (vdesc->record >= 0)
        if (!(wmb->frame = (int *)bgetr(wmb->frame, sizeof(int) * (1 + wmb->validvars))))
            piomemerror(*ios, (1 + wmb->validvars) * sizeof(int), __FILE__, __LINE__);

    /* Get memory to hold fill value. */
    if (iodesc->needsfill)
        if (!(wmb->fillvalue = bgetr(wmb->fillvalue, tsize * (1 + wmb->validvars))))
            piomemerror(*ios, (1 + wmb->validvars) * tsize, __FILE__, __LINE__);

    /* If we need a fill value, get it. */
    if (iodesc->needsfill)
    {
	/* If the user passed a fill value, use that, otherwise use
	 * the default fill value of the netCDF type. Copy the fill
	 * value to the buffer. */
        if (fillvalue)
            memcpy((char *)wmb->fillvalue + tsize * wmb->validvars, fillvalue, tsize);
        else
        {
            vtype = (MPI_Datatype)iodesc->basetype;
            if (vtype == MPI_INTEGER)
            {
                int fill = PIO_FILL_INT;
                memcpy((char *)wmb->fillvalue + tsize * wmb->validvars, &fill, tsize);
            }
            else if (vtype == MPI_FLOAT || vtype == MPI_REAL4)
            {
                float fill = PIO_FILL_FLOAT;
                memcpy((char *)wmb->fillvalue + tsize * wmb->validvars, &fill, tsize);
            }
            else if (vtype == MPI_DOUBLE || vtype == MPI_REAL8)
            {
                double fill = PIO_FILL_DOUBLE;
                memcpy((char *)wmb->fillvalue + tsize * wmb->validvars, &fill, tsize);
            }
            else if (vtype == MPI_CHARACTER)
            {
                char fill = PIO_FILL_CHAR;
                memcpy((char *)wmb->fillvalue + tsize * wmb->validvars, &fill, tsize);
            }
            else
            {
		return PIO_EBADTYPE;
            }
        }
    }

    /* Tell the buffer about the data it is getting. */
    wmb->arraylen = arraylen;
    wmb->vid[wmb->validvars] = vid;

    /* Copy the user-provided data to the buffer. */
    bufptr = (void *)((char *)wmb->data + arraylen * tsize * wmb->validvars);
    if (arraylen > 0)
        memcpy(bufptr, array, arraylen * tsize);

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

    return ierr;
}

/** Read a field from a file to the IO library.
 * @ingroup PIO_read_darray
 *
 * @param ncid identifies the netCDF file
 * @param vid the variable ID to be read
 * @param ioid: the I/O description ID as passed back by
 * PIOc_InitDecomp().
 * @param arraylen: the length of the array to be read. This
 * is the length of the distrubited array. That is, the length of
 * the portion of the data that is on the processor.
 * @param array: pointer to the data to be read. This is a
 * pointer to the distributed portion of the array that is on this
 * processor.
 *
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_read_darray
 */
int PIOc_read_darray(const int ncid, const int vid, const int ioid,
                     const PIO_Offset arraylen, void *array)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;
    io_desc_t *iodesc;
    void *iobuf = NULL;
    size_t rlen = 0;
    int tsize; /* Total size. */
    MPI_Datatype vtype; /* MPI type of this var. */
    int ierr; /* Return code. */

    /* Get the file info. */
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    ios = file->iosystem;

    /* Get the iodesc. */
    if (!(iodesc = pio_get_iodesc_from_id(ioid)))
        return PIO_EBADID;

    if (ios->iomaster)
        rlen = iodesc->maxiobuflen;
    else
        rlen = iodesc->llen;

    /* Is a rearranger in use? */
    if (iodesc->rearranger > 0)
    {
        if (ios->ioproc && rlen > 0)
        {
            /* Get the MPI type size. */
            MPI_Type_size(iodesc->basetype, &tsize);

            /* Allocate a buffer for one record. */
            if (!(iobuf = bget((size_t)tsize * rlen)))
                piomemerror(*ios, rlen * (size_t)tsize, __FILE__, __LINE__);
        }
    }
    else
    {
        iobuf = array;
    }

    /* Call the correct darray read function based on iotype. */
    switch(file->iotype)
    {
    case PIO_IOTYPE_NETCDF:
    case PIO_IOTYPE_NETCDF4C:
        ierr = pio_read_darray_nc_serial(file, iodesc, vid, iobuf);
        break;
    case PIO_IOTYPE_PNETCDF:
    case PIO_IOTYPE_NETCDF4P:
        ierr = pio_read_darray_nc(file, iodesc, vid, iobuf);
        break;
    default:
        ierr = iotype_error(file->iotype,__FILE__,__LINE__);
    }

    /* If a rearranger was specified, rearrange the data. */
    if (iodesc->rearranger > 0)
    {
        ierr = rearrange_io2comp(*ios, iodesc, iobuf, array);

        /* Free the buffer. */
        if (rlen > 0)
            brel(iobuf);
    }

    return ierr;
}
