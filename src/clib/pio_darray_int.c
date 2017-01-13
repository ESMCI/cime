/** @file
 *
 * Private functions to help read and write distributed arrays in PIO.
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
extern PIO_Offset pio_buffer_size_limit;

/* Initial size of compute buffer. */
bufsize pio_cnbuffer_limit = 33554432;

/* Global buffer pool pointer. */
extern void *CN_bpool;

/* Maximum buffer usage. */
extern PIO_Offset maxusage;

/** 
 * Initialize the compute buffer to size pio_cnbuffer_limit.
 *
 * This routine initializes the compute buffer pool if the bget memory
 * management is used. If malloc is used (that is, PIO_USE_MALLOC is
 * non zero), this function does nothing.
 *
 * @param ios the iosystem descriptor which will use the new buffer
 * @returns 0 for success, error code otherwise.
 */
int compute_buffer_init(iosystem_desc_t ios)
{
#if !PIO_USE_MALLOC

    if (!CN_bpool)
    {
        if (!(CN_bpool = malloc(pio_cnbuffer_limit)))
            return pio_err(&ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);            

        bpool(CN_bpool, pio_cnbuffer_limit);
        if (!CN_bpool) 
            return pio_err(&ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);            

        bectl(NULL, malloc, free, pio_cnbuffer_limit);
    }
#endif
    LOG((2, "compute_buffer_init CN_bpool = %d", CN_bpool));

    return PIO_NOERR;
}

/**
 * Write a single distributed field to output. This routine is only
 * used if aggregation is off.
 *
 * @param file a pointer to the open file descriptor for the file
 * that will be written to
 * @param iodesc a pointer to the defined iodescriptor for the buffer
 * @param vid the variable id to be written
 * @param iobuf the buffer to be written from this mpi task. May be
 * null. for example we have 8 ionodes and a distributed array with
 * global size 4, then at least 4 nodes will have a null iobuf. In
 * practice the box rearranger trys to have at least blocksize bytes
 * on each io task and so if the total number of bytes to write is
 * less than blocksize*numiotasks then some iotasks will have a NULL
 * iobuf.
 * @param fillvalue the optional fillvalue to be used for missing
 * data in this buffer. Ignored in all cases. (???)
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_write_darray
 */
int pio_write_darray_nc(file_desc_t *file, io_desc_t *iodesc, int vid,
                        void *iobuf, void *fillvalue)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    var_desc_t *vdesc;     /* Pointer to info about the var. */
    int ndims;             /* Number of dimensions according to iodesc. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int i;                 /* Loop counter. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int dsize;             /* Size of the type. */
    MPI_Status status;     /* Status from MPI_Recv calls. */
    int fndims;            /* Number of dims for variable according to netCDF. */
    PIO_Offset tdsize = 0; /* Total size. */

    LOG((1, "pio_write_array_nc vid = %d", vid));

    /* Check inputs. */
    pioassert(file && file->iosystem && iodesc && iobuf, "invalid input",
      __FILE__, __LINE__);

#ifdef TIMING
    /* Start timing this function. */
    GPTLstart("PIO:write_darray_nc");
#endif

    /* Get the IO system info. */
    ios = file->iosystem;

    /* Get pointer to variable information. */
    if (!(vdesc = file->varlist + vid))
        return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);

    ndims = iodesc->ndims;

    /* Get the number of dims for this var from netcdf. */
    ierr = PIOc_inq_varndims(file->pio_ncid, vid, &fndims);

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = 0;

            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&file->pio_ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, write the data. */
    if (ios->ioproc)
    {
        io_region *region;
        int regioncnt;
        int rrcnt;
        void *bufptr;
        void *tmp_buf = NULL;
        int tsize;            /* Type size. */
        size_t start[fndims]; /* Local start array for this task. */
        size_t count[fndims]; /* Local count array for this task. */
        int buflen;
        int j;                /* Loop counter. */

        PIO_Offset *startlist[iodesc->maxregions];
        PIO_Offset *countlist[iodesc->maxregions];

        /* Get the type size (again?) */
        if ((mpierr = MPI_Type_size(iodesc->basetype, &tsize)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

        region = iodesc->firstregion;

        /* If this is a var with an unlimited dimension, and the
         * iodesc ndims doesn't contain it, then add it to ndims. */
        if (vdesc->record >= 0 && ndims < fndims)
            ndims++;

#ifdef _PNETCDF
        /* Make sure we have room in the buffer. */
        if (file->iotype == PIO_IOTYPE_PNETCDF)
            flush_output_buffer(file, false, tsize * (iodesc->maxiobuflen));
#endif

        rrcnt = 0;
        /* For each region, figure out start/count arrays. */
        for (regioncnt = 0; regioncnt < iodesc->maxregions; regioncnt++)
        {
            /* Init arrays to zeros. */
            for (i = 0; i < ndims; i++)
            {
                start[i] = 0;
                count[i] = 0;
            }

            if (region)
            {
                bufptr = (void *)((char *)iobuf + tsize * region->loffset);
                if (vdesc->record >= 0)
                {
                    /* This is a record based multidimensional array. */

                    /* This does not look correct, but will work if
                     * unlimited dim is dim 0. */
                    start[0] = vdesc->record;

                    /* Set the local start and count arrays. */
                    for (i = 1; i < ndims; i++)
                    {
                        start[i] = region->start[i - 1];
                        count[i] = region->count[i - 1];
                    }

                    /* If there is data to be written, write one timestep. */
                    if (count[1] > 0)
                        count[0] = 1;
                }
                else
                {
                    /* Array without unlimited dimension. */
                    for (i = 0; i < ndims; i++)
                    {
                        start[i] = region->start[i];
                        count[i] = region->count[i];
                    }
                }
            }

            switch (file->iotype)
            {
#ifdef _NETCDF
#ifdef _NETCDF4
            case PIO_IOTYPE_NETCDF4P:

                /* Use collective writes with this variable. */
                ierr = nc_var_par_access(file->fh, vid, NC_COLLECTIVE);

                /* Write the data. */
                if (iodesc->basetype == MPI_DOUBLE || iodesc->basetype == MPI_REAL8)
                    ierr = nc_put_vara_double(file->fh, vid, (size_t *)start, (size_t *)count,
                                              (const double *)bufptr);
                else if (iodesc->basetype == MPI_INTEGER)
                    ierr = nc_put_vara_int(file->fh, vid, (size_t *)start, (size_t *)count,
                                           (const int *)bufptr);
                else if (iodesc->basetype == MPI_FLOAT || iodesc->basetype == MPI_REAL4)
                    ierr = nc_put_vara_float(file->fh, vid, (size_t *)start, (size_t *)count,
                                             (const float *)bufptr);
                else
                    fprintf(stderr,"Type not recognized %d in pioc_write_darray\n",
                            (int)iodesc->basetype);
                break;
            case PIO_IOTYPE_NETCDF4C:
#endif /* _NETCDF4 */
            case PIO_IOTYPE_NETCDF:
            {
                /* Find the type size (again?) */
                if ((mpierr = MPI_Type_size(iodesc->basetype, &dsize)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);

                size_t tstart[ndims], tcount[ndims];

                /* When using the serial netcdf PIO acts like a
                 * funnel. Data is moved from compute tasks to IO
                 * tasks then from IO tasks to IO task 0 for
                 * write. For read data the opposite happens, data is
                 * read on IO task 0 distributed to all io tasks and
                 * then to compute tasks. We could optimize these data
                 * paths but serial netcdf is not the primary mode for
                 * PIO. */
                if (ios->io_rank == 0)
                {
                    for (i = 0; i < iodesc->num_aiotasks; i++)
                    {
                        if (i == 0)
                        {
                            buflen = 1;
                            for (j = 0; j < ndims; j++)
                            {
                                tstart[j] =  start[j];
                                tcount[j] =  count[j];
                                buflen *= tcount[j];
                                tmp_buf = bufptr;
                            }
                        }
                        else
                        {
                            /* Handshake - tell the sending task I'm ready. */
                            if ((mpierr = MPI_Send(&ierr, 1, MPI_INT, i, 0, ios->io_comm)))
                                return check_mpi(file, mpierr, __FILE__, __LINE__);

                            if ((mpierr = MPI_Recv(&buflen, 1, MPI_INT, i, 1, ios->io_comm, &status)))
                                return check_mpi(file, mpierr, __FILE__, __LINE__);

                            if (buflen > 0)
                            {
                                if ((mpierr = MPI_Recv(tstart, ndims, MPI_OFFSET, i, ios->num_iotasks + i,
                                                       ios->io_comm, &status)))
                                    return check_mpi(file, mpierr, __FILE__, __LINE__);

                                if ((mpierr = MPI_Recv(tcount, ndims, MPI_OFFSET, i, 2 * ios->num_iotasks + i,
                                                       ios->io_comm, &status)))
                                    return check_mpi(file, mpierr, __FILE__, __LINE__);

                                if (!(tmp_buf = malloc(buflen * dsize)))
                                    return pio_err(NULL, file, PIO_ENOMEM, __FILE__, __LINE__);
                                if ((mpierr = MPI_Recv(tmp_buf, buflen, iodesc->basetype, i, i, ios->io_comm, &status)))
                                    return check_mpi(file, mpierr, __FILE__, __LINE__);

                            }
                        }

                        if (buflen > 0)
                        {
                            /* Write the data. */
                            if (iodesc->basetype == MPI_INTEGER)
                                ierr = nc_put_vara_int(file->fh, vid, tstart, tcount, (const int *)tmp_buf);
                            else if (iodesc->basetype == MPI_DOUBLE || iodesc->basetype == MPI_REAL8)
                                ierr = nc_put_vara_double(file->fh, vid, tstart, tcount, (const double *)tmp_buf);
                            else if (iodesc->basetype == MPI_FLOAT || iodesc->basetype == MPI_REAL4)
                                ierr = nc_put_vara_float(file->fh, vid, tstart, tcount, (const float *)tmp_buf);
                            else
                                fprintf(stderr,"Type not recognized %d in pioc_write_darray\n",
                                        (int)iodesc->basetype);

                            /* Was there an error from netCDF? */
                            if (ierr == PIO_EEDGE)
                                for (i = 0; i < ndims; i++)
                                    fprintf(stderr,"dim %d start %ld count %ld\n", i, tstart[i], tcount[i]);

                            /* Free the temporary buffer, if we don't need it any more. */
                            if (tmp_buf != bufptr)
                                free(tmp_buf);
                        }
                    }
                }
                else if (ios->io_rank < iodesc->num_aiotasks)
                {
                    buflen = 1;
                    for (i = 0; i < ndims; i++)
                    {
                        tstart[i] = (size_t) start[i];
                        tcount[i] = (size_t) count[i];
                        buflen *= tcount[i];
                    }
                    /*       printf("%s %d %d %d %d %d %d %d %d %d\n",__FILE__,__LINE__,ios->io_rank,tstart[0],
                             tstart[1],tcount[0],tcount[1],buflen,ndims,fndims);*/

		    /* task0 is ready to recieve */
                    if ((mpierr = MPI_Recv(&ierr, 1, MPI_INT, 0, 0, ios->io_comm, &status)))
                        return check_mpi(file, mpierr, __FILE__, __LINE__);

                    if ((mpierr = MPI_Rsend(&buflen, 1, MPI_INT, 0, 1, ios->io_comm)))
                        return check_mpi(file, mpierr, __FILE__, __LINE__);

                    if (buflen > 0)
                    {
                        if ((mpierr = MPI_Rsend(tstart, ndims, MPI_OFFSET, 0, ios->num_iotasks+ios->io_rank, ios->io_comm)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                        if ((mpierr = MPI_Rsend(tcount, ndims, MPI_OFFSET, 0,2*ios->num_iotasks+ios->io_rank, ios->io_comm)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                        if ((mpierr = MPI_Rsend(bufptr, buflen, iodesc->basetype, 0, ios->io_rank, ios->io_comm)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                    }
                }
                break;
            }
            break;
#endif /* _NETCDF */
#ifdef _PNETCDF
            case PIO_IOTYPE_PNETCDF:
                for (i = 0, dsize = 1; i < ndims; i++)
                    dsize *= count[i];

                tdsize += dsize;

                if (dsize > 0)
                {
                    if (!(startlist[rrcnt] = calloc(fndims, sizeof(PIO_Offset))))
                        return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
                    if (!(countlist[rrcnt] = calloc(fndims, sizeof(PIO_Offset))))
                        return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
                    for (i = 0; i < fndims; i++)
                    {
                        startlist[rrcnt][i] = start[i];
                        countlist[rrcnt][i] = count[i];
                    }
                    rrcnt++;
                }
                if (regioncnt == iodesc->maxregions - 1)
                {
                    /* printf("%s %d %d %ld %ld\n",__FILE__,__LINE__,ios->io_rank,iodesc->llen, tdsize);
                         ierr = ncmpi_put_varn_all(file->fh, vid, iodesc->maxregions, startlist, countlist,
                                           iobuf, iodesc->llen, iodesc->basetype); */
                    int reqn = 0;

                    if (vdesc->nreqs % PIO_REQUEST_ALLOC_CHUNK == 0 )
                    {
                        if (!(vdesc->request = realloc(vdesc->request,
                                                       sizeof(int) * (vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK))))
                            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

                        for (int i = vdesc->nreqs; i < vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK; i++)
                            vdesc->request[i] = NC_REQ_NULL;
                        reqn = vdesc->nreqs;
                    }
                    else
                        while(vdesc->request[reqn] != NC_REQ_NULL)
                            reqn++;

                    ierr = ncmpi_bput_varn(file->fh, vid, rrcnt, startlist, countlist, iobuf, iodesc->llen,
                                           iodesc->basetype, vdesc->request+reqn);

                    if (vdesc->request[reqn] == NC_REQ_NULL)
                        vdesc->request[reqn] = PIO_REQ_NULL;  /* keeps wait calls in sync */
                    vdesc->nreqs = reqn;

		    /* Free memory. */
                    for (i = 0; i < rrcnt; i++)
                    {
                        free(startlist[i]);
                        free(countlist[i]);
                    }
                }
                break;
#endif /* _PNETCDF */
            default:
                return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
            }

            /* Move to the next region. */
            if (region)
                region = region->next;
        } /* next regioncnt */
    } /* endif (ios->ioproc) */

    /* Broadcast and check the return code. */
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);

#ifdef TIMING
    /* Stop timing this function. */
    GPTLstop("PIO:write_darray_nc");
#endif

    return ierr;
}

/**
 * Write a set of one or more aggregated arrays to output file.
 *
 * This routine is used if aggregation is enabled, data is already on
 * the io-tasks
 *
 * @param file a pointer to the open file descriptor for the file
 * that will be written to
 * @param nvars the number of variables to be written with this
 * decomposition
 * @param vid: an array of the variable ids to be written
 * @param iodesc_ndims: the number of dimensions explicitly in the
 * iodesc
 * @param basetype the basic type of the minimal data unit
 * @param gsize array of the global sizes of all dimensions of the
 * field to be written
 * @param maxregions max number of blocks to be written from
 * this iotask
 * @param firstregion pointer to the first element of a linked
 * list of region descriptions. May be NULL.
 * @param llen length of the iobuffer on this task for a single
 * field
 * @param maxiobuflen maximum llen participating
 * @param num_aiotasks actual number of iotasks participating
 * @param iobuf the buffer to be written from this mpi task. May be
 * null. for example we have 8 ionodes and a distributed array with
 * global size 4, then at least 4 nodes will have a null iobuf. In
 * practice the box rearranger trys to have at least blocksize bytes
 * on each io task and so if the total number of bytes to write is
 * less than blocksize*numiotasks then some iotasks will have a NULL
 * iobuf.
 * @param frame the frame or record dimension for each of the nvars
 * variables in iobuf
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_write_darray
 */
int pio_write_darray_multi_nc(file_desc_t *file, int nvars, const int *vid, int iodesc_ndims,
                              MPI_Datatype basetype, const PIO_Offset *gsize, int maxregions,
                              io_region *firstregion, PIO_Offset llen, int maxiobuflen,
                              int num_aiotasks, void *iobuf, const int *frame)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    var_desc_t *vdesc;
    int ierr;
    int i;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int dsize;
    int fndims;
    PIO_Offset tdsize;
    int tsize;
    int ncid;
    tdsize=0;
    ierr = PIO_NOERR;

    /* Check inputs. */
    pioassert(file && file->iosystem, "invalid input", __FILE__, __LINE__);

#ifdef TIMING
    /* Start timing this function. */
    GPTLstart("PIO:write_darray_multi_nc");
#endif

    /* Get file and variable info. */
    ios = file->iosystem;
    if (!(vdesc = file->varlist + vid[0]))
        return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);
    ncid = file->fh;

    /* If async is in use, send message to IO master task. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = 0;
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&file->pio_ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* Find out how many dims this variable has. */
    if ((ierr = PIOc_inq_varndims(file->pio_ncid, vid[0], &fndims)))
        return pio_err(ios, file, ierr, __FILE__, __LINE__);

    /* Find out the size of the MPI type. */
    if ((mpierr = MPI_Type_size(basetype, &tsize)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    /* If this is an IO task write the data. */
    if (ios->ioproc)
    {
        io_region *region;
        int regioncnt;
        int rrcnt;
        void *bufptr;
        int j;
        size_t start[fndims];
        size_t count[fndims];
        int ndims = iodesc_ndims;

        PIO_Offset *startlist[maxregions];
        PIO_Offset *countlist[maxregions];

        ncid = file->fh;
        region = firstregion;

        rrcnt = 0;
        for (regioncnt = 0; regioncnt < maxregions; regioncnt++)
        {
            for (i = 0; i < fndims; i++)
            {
                start[i] = 0;
                count[i] = 0;
            }
            if (region)
            {
                /* this is a record based multidimensional array */
                if (vdesc->record >= 0)
                {
                    for (i = fndims - ndims; i < fndims; i++)
                    {
                        start[i] = region->start[i-(fndims-ndims)];
                        count[i] = region->count[i-(fndims-ndims)];
                    }

                    if (fndims>1 && ndims<fndims && count[1]>0)
                    {
                        count[0] = 1;
                        start[0] = frame[0];
                    }
                    else if (fndims==ndims)
                    {
                        start[0] += vdesc->record;
                    }
                    /* Non-time dependent array */
                }
                else
                {
                    for (i = 0; i < ndims; i++)
                    {
                        start[i] = region->start[i];
                        count[i] = region->count[i];
                    }
                }
            }

            switch (file->iotype)
            {
#ifdef _NETCDF4
            case PIO_IOTYPE_NETCDF4P:
                for (int nv = 0; nv < nvars; nv++)
                {
                    if (vdesc->record >= 0 && ndims < fndims)
                        start[0] = frame[nv];

                    if (region)
                        bufptr = (void *)((char *)iobuf + tsize * (nv * llen + region->loffset));

                    ierr = nc_var_par_access(ncid, vid[nv], NC_COLLECTIVE);

                    if (basetype == MPI_DOUBLE || basetype == MPI_REAL8)
                        ierr = nc_put_vara_double(ncid, vid[nv], (size_t *)start, (size_t *)count,
                                                  (const double *)bufptr);
                    else if (basetype == MPI_INTEGER)
                        ierr = nc_put_vara_int(ncid, vid[nv], (size_t *)start, (size_t *)count,
                                               (const int *)bufptr);
                    else if (basetype == MPI_FLOAT || basetype == MPI_REAL4)
                        ierr = nc_put_vara_float(ncid, vid[nv], (size_t *)start, (size_t *)count,
                                                 (const float *)bufptr);
                    else
                        fprintf(stderr,"Type not recognized %d in pioc_write_darray\n",
                                (int)basetype);
                }
                break;
#endif
#ifdef _PNETCDF
            case PIO_IOTYPE_PNETCDF:
                for (i = 0, dsize = 1; i < fndims; i++)
                    dsize *= count[i];
                tdsize += dsize;

                if (dsize > 0)
                {
                    if (!(startlist[rrcnt] = calloc(fndims, sizeof(PIO_Offset))))
                        return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
                    if (!(countlist[rrcnt] = calloc(fndims, sizeof(PIO_Offset))))
                        return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
                    for (i = 0; i < fndims; i++)
                    {
                        startlist[rrcnt][i] = start[i];
                        countlist[rrcnt][i] = count[i];
                    }
                    rrcnt++;
                }
                if (regioncnt == maxregions - 1)
                {
                    /*printf("%s %d %d %ld %ld\n",__FILE__,__LINE__,ios->io_rank,iodesc->llen, tdsize);
                         ierr = ncmpi_put_varn_all(ncid, vid, iodesc->maxregions, startlist, countlist,
                                           iobuf, iodesc->llen, iodesc->basetype);*/

                    for (int nv = 0; nv < nvars; nv++)
                    {
                        vdesc = (file->varlist) + vid[nv];
                        if (vdesc->record >= 0 && ndims<fndims)
                            for (int rc = 0; rc < rrcnt; rc++)
                                startlist[rc][0] = frame[nv];

                        bufptr = (void *)((char *)iobuf + nv * tsize * llen);

                        int reqn = 0;
                        if (vdesc->nreqs % PIO_REQUEST_ALLOC_CHUNK == 0 )
                        {
                            if (!(vdesc->request = realloc(vdesc->request,
                                                           sizeof(int)*(vdesc->nreqs+PIO_REQUEST_ALLOC_CHUNK))))
                                return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

                            for (int i = vdesc->nreqs; i < vdesc->nreqs + PIO_REQUEST_ALLOC_CHUNK; i++)
                                vdesc->request[i] = NC_REQ_NULL;
                            reqn = vdesc->nreqs;
                        }
                        else
                            while(vdesc->request[reqn] != NC_REQ_NULL)
                                reqn++;

                        ierr = ncmpi_iput_varn(ncid, vid[nv], rrcnt, startlist, countlist,
                                               bufptr, llen, basetype, vdesc->request+reqn);
                        /*
                          ierr = ncmpi_bput_varn(ncid, vid[nv], rrcnt, startlist, countlist,
                          bufptr, llen, basetype, &(vdesc->request));
                        */
                        /* keeps wait calls in sync */
                        if (vdesc->request[reqn] == NC_REQ_NULL)
                            vdesc->request[reqn] = PIO_REQ_NULL;

                        vdesc->nreqs += reqn+1;

                    }
                    for (i = 0; i < rrcnt; i++)
                    {
                        if (ierr != PIO_NOERR)
                        {
                            for (j = 0; j < fndims; j++)
                            {
                                LOG((2, "pio_darray: %d %d %ld %ld \n", i, j, startlist[i][j],
                                     countlist[i][j]));
                            }
                        }
                        free(startlist[i]);
                        free(countlist[i]);
                    }
                }
                break;
#endif
            default:
                return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
            }

            /* Go to next region. */
            if (region)
                region = region->next;
        } /* next regioncnt */
    } /* endif (ios->ioproc) */

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

#ifdef TIMING
    /* Stop timing this function. */
    GPTLstop("PIO:write_darray_multi_nc");
#endif

    return ierr;
}

/**
 * Write a set of one or more aggregated arrays to output file in
 * serial mode.
 *
 * This routine is used if aggregation is enabled, data is already on the
 * io-tasks
 *
 * @param file: a pointer to the open file descriptor for the file
 * that will be written to
 * @param nvars: the number of variables to be written with this
 * decomposition
 * @param vid: an array of the variable ids to be written
 * @param iodesc_ndims: the number of dimensions explicitly in the
 * iodesc
 * @param basetype : the basic type of the minimal data unit
 * @param gsize : array of the global dimensions of the field to be
 * written. (Not used ???)
 * @param maxregions : max number of blocks to be written from this
 * iotask
 * @param firstregion : pointer to the first element of a linked
 * list of region descriptions. May be NULL.
 * @param llen : length of the iobuffer on this task for a single
 * field
 * @param maxiobuflen : maximum llen participating
 * @param num_aiotasks : actual number of iotasks participating
 * @param iobuf the buffer to be written from this mpi task. May be
 * null. for example we have 8 ionodes and a distributed array with
 * global size 4, then at least 4 nodes will have a null iobuf. In
 * practice the box rearranger trys to have at least blocksize bytes
 * on each io task and so if the total number of bytes to write is
 * less than blocksize*numiotasks then some iotasks will have a NULL
 * iobuf.
 * @param frame : the frame or record dimension for each of the
 * nvars variables in iobuf
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_write_darray
 */
int pio_write_darray_multi_nc_serial(file_desc_t *file, int nvars, const int *vid, int iodesc_ndims,
                                     MPI_Datatype basetype, const PIO_Offset *gsize, int maxregions,
                                     io_region *firstregion, PIO_Offset llen, int maxiobuflen,
                                     int num_aiotasks, void *iobuf, const int *frame)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    var_desc_t *vdesc;
    int ierr = PIO_NOERR;
    int i;
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI function codes. */
    int dsize;
    MPI_Status status;
    int fndims;
    int tsize;
    int ncid;

    /* Check inputs. */
    pioassert(file && file->iosystem, "invalid input", __FILE__, __LINE__);

#ifdef TIMING
    /* Start timing this function. */
    GPTLstart("PIO:write_darray_multi_nc_serial");
#endif

    ios = file->iosystem;
    ncid = file->fh;

    /* Get the var info. */
    if (!(vdesc = (file->varlist) + vid[0]))
        return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = 0;

            if (ios->comp_rank==0)
                mpierr = MPI_Send(&msg, 1,MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&file->pio_ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* Get the number of dimensions. */
    if ((ierr = PIOc_inq_varndims(file->pio_ncid, vid[0], &fndims)))
        return pio_err(ios, file, ierr, __FILE__, __LINE__);
    if ((mpierr = MPI_Type_size(basetype, &tsize)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    if (ios->ioproc)
    {
        io_region *region;
        int regioncnt;
        void *bufptr;
        size_t tmp_start[fndims*maxregions];
        size_t tmp_count[fndims*maxregions];
        int ndims = iodesc_ndims;

        ncid = file->fh;
        region = firstregion;

        for (regioncnt = 0; regioncnt < maxregions; regioncnt++)
        {
            for (i = 0; i < fndims; i++)
            {
                tmp_start[i + regioncnt * fndims] = 0;
                tmp_count[i + regioncnt * fndims] = 0;
            }
            if (region)
            {
                /* this is a record based multidimensional array */
                if (vdesc->record >= 0)
                {
                    for (i = fndims - ndims; i < fndims; i++)
                    {
                        tmp_start[i + regioncnt * fndims] = region->start[i - (fndims - ndims)];
                        tmp_count[i + regioncnt * fndims] = region->count[i - (fndims - ndims)];
                    }
                    /* Non-time dependent array */
                }
                else
                {
                    for (i = 0; i < ndims; i++)
                    {
                        tmp_start[i + regioncnt * fndims] = region->start[i];
                        tmp_count[i + regioncnt * fndims] = region->count[i];
                    }
                }
                region = region->next;
            }
        }

        if (ios->io_rank > 0)
        {
            /* task0 is ready to recieve */
            if ((mpierr = MPI_Recv(&ierr, 1, MPI_INT, 0, 0, ios->io_comm, &status)))
                return check_mpi(file, mpierr, __FILE__, __LINE__);
            if ((mpierr = MPI_Send((void *)&llen, 1, MPI_OFFSET, 0, ios->io_rank, ios->io_comm)))
                return check_mpi(file, mpierr, __FILE__, __LINE__);

            if (llen > 0)
            {
                if ((mpierr = MPI_Send((void *)&maxregions, 1, MPI_INT, 0, ios->io_rank+ios->num_iotasks, ios->io_comm)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);
                if ((mpierr = MPI_Send(tmp_start, maxregions * fndims, MPI_OFFSET, 0, ios->io_rank + 2 * ios->num_iotasks,
                                       ios->io_comm)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);
                if ((mpierr = MPI_Send(tmp_count, maxregions * fndims, MPI_OFFSET, 0, ios->io_rank + 3 * ios->num_iotasks,
                                       ios->io_comm)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);
                if ((mpierr = MPI_Send(iobuf, nvars * llen, basetype, 0, ios->io_rank + 4 * ios->num_iotasks, ios->io_comm)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);
            }
        }
        else
        {
            size_t rlen;
            int rregions;
            size_t start[fndims], count[fndims];
            size_t loffset;
            if ((mpierr = MPI_Type_size(basetype, &dsize)))
                return check_mpi(file, mpierr, __FILE__, __LINE__);

            for (int rtask = 0; rtask < ios->num_iotasks; rtask++)
            {
                if (rtask > 0)
                {
                    /* handshake - tell the sending task I'm ready */
                    if ((mpierr = MPI_Send(&ierr, 1, MPI_INT, rtask, 0, ios->io_comm)))
                        return check_mpi(file, mpierr, __FILE__, __LINE__);
                    if ((mpierr = MPI_Recv(&rlen, 1, MPI_OFFSET, rtask, rtask, ios->io_comm, &status)))
                        return check_mpi(file, mpierr, __FILE__, __LINE__);

                    if (rlen > 0)
                    {
                        if ((mpierr = MPI_Recv(&rregions, 1, MPI_INT, rtask, rtask + ios->num_iotasks,
                                               ios->io_comm, &status)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                        if ((mpierr = MPI_Recv(tmp_start, rregions * fndims, MPI_OFFSET, rtask, rtask + 2 * ios->num_iotasks,
                                               ios->io_comm, &status)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                        if ((mpierr = MPI_Recv(tmp_count, rregions * fndims, MPI_OFFSET, rtask, rtask + 3 * ios->num_iotasks,
                                               ios->io_comm, &status)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                        if ((mpierr = MPI_Recv(iobuf, nvars * rlen, basetype, rtask, rtask + 4 * ios->num_iotasks, ios->io_comm,
                                               &status)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                    }
                }
                else
                {
                    rlen = llen;
                    rregions = maxregions;
                }
                if (rlen > 0)
                {
                    loffset = 0;
                    for (regioncnt = 0; regioncnt < rregions; regioncnt++)
                    {
                        for (int i = 0; i < fndims; i++)
                        {
                            start[i] = tmp_start[i + regioncnt * fndims];
                            count[i] = tmp_count[i + regioncnt * fndims];
                        }

                        for (int nv = 0; nv < nvars; nv++)
                        {
                            bufptr = (void *)((char *)iobuf+ tsize * (nv * rlen + loffset));

                            if (vdesc->record >= 0)
                            {
                                if (fndims > 1 && ndims < fndims && count[1] > 0)
                                {
                                    count[0] = 1;
                                    start[0] = frame[nv];
                                }
                                else if (fndims == ndims)
                                {
                                    start[0] += vdesc->record;
                                }
                            }

                            if (basetype == MPI_INTEGER)
                                ierr = nc_put_vara_int(ncid, vid[nv], start, count, (const int *)bufptr);
                            else if (basetype == MPI_DOUBLE || basetype == MPI_REAL8)
                                ierr = nc_put_vara_double(ncid, vid[nv], start, count, (const double *)bufptr);
                            else if (basetype == MPI_FLOAT || basetype == MPI_REAL4)
                                ierr = nc_put_vara_float(ncid,vid[nv], start, count, (const float *)bufptr);
                            else
                                fprintf(stderr, "Type not recognized %d in pioc_write_darray\n", (int)basetype);

                            if (ierr != PIO_NOERR)
                            {
                                for (i = 0; i < fndims; i++)
                                    fprintf(stderr, "vid %d dim %d start %ld count %ld \n", vid[nv], i,
                                            start[i], count[i]);
                            }
                        }
                        size_t tsize;
                        tsize = 1;

                        /* Calculate the total size. */
                        for (int i = 0; i < fndims; i++)
                            tsize *= count[i];

                        loffset += tsize;
                    } /* next regioncnt */
                } /* endif (rlen > 0) */
            } /* next rtask */
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

#ifdef TIMING
    /* Stop timing this function. */
    GPTLstop("PIO:write_darray_multi_nc_serial");
#endif

    return ierr;
}

/**
 * Read an array of data from a file to the (parallel) IO library.
 *
 * @param file a pointer to the open file descriptor for the file
 * that will be written to
 * @param iodesc a pointer to the defined iodescriptor for the buffer
 * @param vid the variable id to be read
 * @param iobuf the buffer to be written from this mpi task. May be
 * null. for example we have 8 ionodes and a distributed array with
 * global size 4, then at least 4 nodes will have a null iobuf. In
 * practice the box rearranger trys to have at least blocksize bytes
 * on each io task and so if the total number of bytes to write is
 * less than blocksize*numiotasks then some iotasks will have a NULL
 * iobuf.
 * @return 0 on success, error code otherwise.
 * @ingroup PIO_read_darray
 */
int pio_read_darray_nc(file_desc_t *file, io_desc_t *iodesc, int vid, void *iobuf)
{
    int ierr = PIO_NOERR;
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    var_desc_t *vdesc;
    int ndims, fndims;
    int i;
    int mpierr;  /* Return code from MPI functions. */

    /* Check inputs. */
    pioassert(file && file->iosystem && iodesc, "invalid input", __FILE__, __LINE__);

#ifdef TIMING
    /* Start timing this function. */
    GPTLstart("PIO:read_darray_nc");
#endif

    ios = file->iosystem;

    if (!(vdesc = (file->varlist) + vid))
        return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);

    ndims = iodesc->ndims;

    /* Get the number of dims for this var. */
    if ((ierr = PIOc_inq_varndims(file->pio_ncid, vid, &fndims)))
        return pio_err(ios, file, ierr, __FILE__, __LINE__);

    /* Is this a record var? */
    if (fndims == ndims)
        vdesc->record = -1;

    if (ios->ioproc)
    {
        io_region *region;
        size_t start[fndims];
        size_t count[fndims];
        size_t tmp_bufsize = 1;
        int regioncnt;
        void *bufptr;
        int tsize;

        int rrlen = 0;
        PIO_Offset *startlist[iodesc->maxregions];
        PIO_Offset *countlist[iodesc->maxregions];

        /* buffer is incremented by byte and loffset is in terms of
	   the iodessc->basetype so we need to multiply by the size of
	   the basetype We can potentially allow for one iodesc to
	   have multiple datatypes by allowing the calling program to
	   change the basetype. */
        region = iodesc->firstregion;

	/* Get the size of the MPI type. */
        if ((mpierr = MPI_Type_size(iodesc->basetype, &tsize)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

        if (fndims > ndims)
        {
            ndims++;
            if (vdesc->record < 0)
                vdesc->record = 0;
        }
        for (regioncnt = 0; regioncnt < iodesc->maxregions; regioncnt++)
        {
            tmp_bufsize = 1;
            if (region == NULL || iodesc->llen == 0)
            {
                for (i = 0; i < fndims; i++)
                {
                    start[i] = 0;
                    count[i] = 0;
                }
                bufptr = NULL;
            }
            else
            {
                if (regioncnt == 0 || region == NULL)
                    bufptr = iobuf;
                else
                    bufptr=(void *)((char *)iobuf + tsize * region->loffset);

                LOG((2, "%d %d %d", iodesc->llen - region->loffset, iodesc->llen, region->loffset));

                if (vdesc->record >= 0 && fndims > 1)
                {
                    start[0] = vdesc->record;
                    for (i = 1; i < ndims; i++)
                    {
                        start[i] = region->start[i-1];
                        count[i] = region->count[i-1];
                    }
                    if (count[1] > 0)
                        count[0] = 1;
                }
                else
                {
                    /* Non-time dependent array */
                    for (i = 0; i < ndims; i++)
                    {
                        start[i] = region->start[i];
                        count[i] = region->count[i];
                    }
                }
            }

            switch (file->iotype)
            {
#ifdef _NETCDF4
            case PIO_IOTYPE_NETCDF4P:
                if (iodesc->basetype == MPI_DOUBLE || iodesc->basetype == MPI_REAL8)
                    ierr = nc_get_vara_double(file->fh, vid, start, count, bufptr);
                else if (iodesc->basetype == MPI_INTEGER)
                    ierr = nc_get_vara_int(file->fh, vid, start, count, bufptr);
                else if (iodesc->basetype == MPI_FLOAT || iodesc->basetype == MPI_REAL4)
                    ierr = nc_get_vara_float(file->fh, vid, start, count, bufptr);
                else
                    fprintf(stderr, "Type not recognized %d in pioc_read_darray\n",
                            (int)iodesc->basetype);
                break;
#endif
#ifdef _PNETCDF
            case PIO_IOTYPE_PNETCDF:
            {
                tmp_bufsize = 1;
                for (int j = 0; j < fndims; j++)
                    tmp_bufsize *= count[j];

                if (tmp_bufsize > 0)
                {
                    startlist[rrlen] = bget(fndims * sizeof(PIO_Offset));
                    countlist[rrlen] = bget(fndims * sizeof(PIO_Offset));

                    for (int j = 0; j < fndims; j++)
                    {
                        startlist[rrlen][j] = start[j];
                        countlist[rrlen][j] = count[j];
                    }
                    rrlen++;
                }

                /* Is this is the last region to process? */
                if (regioncnt == iodesc->maxregions - 1)
                {
                    ierr = ncmpi_get_varn_all(file->fh, vid, rrlen, startlist,
                                              countlist, iobuf, iodesc->llen, iodesc->basetype);

                    /* Release the start and count arrays. */
                    for (i = 0; i < rrlen; i++)
                    {
                        brel(startlist[i]);
                        brel(countlist[i]);
                    }
                }
            }
            break;
#endif
            default:
                return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
            }
            if (region)
                region = region->next;
        } /* next regioncnt */
    }

    ierr = check_netcdf(file, ierr, __FILE__,__LINE__);

#ifdef TIMING
    /* Stop timing this function. */
    GPTLstop("PIO:read_darray_nc");
#endif

    return ierr;
}

/**
 * Read an array of data from a file to the (serial) IO library.
 *
 * @param file a pointer to the open file descriptor for the file
 * that will be written to
 * @param iodesc a pointer to the defined iodescriptor for the buffer
 * @param vid the variable id to be read.
 * @param iobuf the buffer to be written from this mpi task. May be
 * null. for example we have 8 ionodes and a distributed array with
 * global size 4, then at least 4 nodes will have a null iobuf. In
 * practice the box rearranger trys to have at least blocksize bytes
 * on each io task and so if the total number of bytes to write is
 * less than blocksize*numiotasks then some iotasks will have a NULL
 * iobuf.
 * @returns 0 for success, error code otherwise.
 * @ingroup PIO_read_darray
 */
int pio_read_darray_nc_serial(file_desc_t *file, io_desc_t *iodesc, int vid,
                              void *iobuf)
{
    int ierr = PIO_NOERR;
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    var_desc_t *vdesc;
    int ndims, fndims;
    MPI_Status status;
    int i;
    int mpierr;  /* Return code from MPI functions. */

    /* Check inputs. */
    pioassert(file && file->iosystem && iodesc, "invalid input", __FILE__, __LINE__);

#ifdef TIMING
    /* Start timing this function. */
    GPTLstart("PIO:read_darray_nc_serial");
#endif
    ios = file->iosystem;

    if (!(vdesc = (file->varlist) + vid))
        return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);

    ndims = iodesc->ndims;

    /* Get number of dims for this var. */
    if ((ierr = PIOc_inq_varndims(file->pio_ncid, vid, &fndims)))
        return pio_err(ios, file, ierr, __FILE__, __LINE__);

    /* Is this a record var? */
    if (fndims == ndims)
        vdesc->record = -1;

    if (ios->ioproc)
    {
        io_region *region;
        size_t start[fndims];
        size_t count[fndims];
        size_t tmp_start[fndims * iodesc->maxregions];
        size_t tmp_count[fndims * iodesc->maxregions];
        size_t tmp_bufsize;
        int regioncnt;
        void *bufptr;
        int tsize;

        /* buffer is incremented by byte and loffset is in terms of
           the iodessc->basetype so we need to multiply by the size of
           the basetype We can potentially allow for one iodesc to have
           multiple datatypes by allowing the calling program to change
           the basetype. */
        region = iodesc->firstregion;

	/* Get the size of the MPI type. */
        if ((mpierr = MPI_Type_size(iodesc->basetype, &tsize)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);

        if (fndims > ndims)
        {
            if (vdesc->record < 0)
                vdesc->record = 0;
        }

        for (regioncnt = 0; regioncnt < iodesc->maxregions; regioncnt++)
        {
            if (!region || iodesc->llen == 0)
            {
                for (i = 0; i < fndims; i++)
                {
                    tmp_start[i + regioncnt * fndims] = 0;
                    tmp_count[i + regioncnt * fndims] = 0;
                }
                bufptr = NULL;
            }
            else
            {
                if (vdesc->record >= 0 && fndims > 1)
                {
                    tmp_start[regioncnt*fndims] = vdesc->record;
                    for (i = 1; i < fndims; i++)
                    {
                        tmp_start[i+regioncnt * fndims] = region->start[i - 1];
                        tmp_count[i+regioncnt * fndims] = region->count[i - 1];
                    }
                    if (tmp_count[1 + regioncnt * fndims] > 0)
                        tmp_count[regioncnt * fndims] = 1;
                }
                else
                {
                    /* Non-time dependent array */
                    for (i = 0; i < fndims; i++)
                    {
                        tmp_start[i + regioncnt * fndims] = region->start[i];
                        tmp_count[i + regioncnt * fndims] = region->count[i];
                    }
                }
                /*      for (i=0;i<fndims;i++){
                        printf("%d %d %d %ld %ld\n",__LINE__,regioncnt,i,tmp_start[i+regioncnt*fndims],
                        tmp_count[i+regioncnt*fndims]);
                        }*/

            }
            if (region)
                region = region->next;
        } /* next regioncnt */

        if (ios->io_rank > 0)
        {
            if ((mpierr = MPI_Send(&iodesc->llen, 1, MPI_OFFSET, 0, ios->io_rank, ios->io_comm)))
                return check_mpi(file, mpierr, __FILE__, __LINE__);

            if (iodesc->llen > 0)
            {
                if ((mpierr = MPI_Send(&(iodesc->maxregions), 1, MPI_INT, 0,
                                       ios->num_iotasks + ios->io_rank, ios->io_comm)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);
                if ((mpierr = MPI_Send(tmp_count, iodesc->maxregions*fndims, MPI_OFFSET, 0,
                                       2 * ios->num_iotasks + ios->io_rank, ios->io_comm)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);
                if ((mpierr = MPI_Send(tmp_start, iodesc->maxregions*fndims, MPI_OFFSET, 0,
                                       3 * ios->num_iotasks + ios->io_rank, ios->io_comm)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);
                if ((mpierr = MPI_Recv(iobuf, iodesc->llen, iodesc->basetype, 0,
                                       4 * ios->num_iotasks+ios->io_rank, ios->io_comm, &status)))
                    return check_mpi(file, mpierr, __FILE__, __LINE__);
            }
        }
        else if (ios->io_rank == 0)
        {
            int maxregions = 0;
            size_t loffset, regionsize;
            size_t this_start[fndims*iodesc->maxregions];
            size_t this_count[fndims*iodesc->maxregions];

            for (int rtask = 1; rtask <= ios->num_iotasks; rtask++)
            {
                if (rtask < ios->num_iotasks)
                {
                    if ((mpierr = MPI_Recv(&tmp_bufsize, 1, MPI_OFFSET, rtask, rtask, ios->io_comm, &status)))
                        return check_mpi(file, mpierr, __FILE__, __LINE__);

                    if (tmp_bufsize > 0)
                    {
                        if ((mpierr = MPI_Recv(&maxregions, 1, MPI_INT, rtask, ios->num_iotasks + rtask,
                                               ios->io_comm, &status)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                        if ((mpierr = MPI_Recv(this_count, maxregions*fndims, MPI_OFFSET, rtask,
                                               2 * ios->num_iotasks + rtask, ios->io_comm, &status)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                        if ((mpierr = MPI_Recv(this_start, maxregions*fndims, MPI_OFFSET, rtask,
                                               3 * ios->num_iotasks + rtask, ios->io_comm, &status)))
                            return check_mpi(file, mpierr, __FILE__, __LINE__);
                    }
                }
                else
                {
                    maxregions = iodesc->maxregions;
                    tmp_bufsize = iodesc->llen;
                }

                loffset = 0;

                for (regioncnt = 0; regioncnt < maxregions; regioncnt++)
                {
                    bufptr=(void *)((char *)iobuf + tsize * loffset);
                    regionsize = 1;

                    if (rtask < ios->num_iotasks)
                    {
                        for (int m = 0; m < fndims; m++)
                        {
                            start[m] = this_start[m + regioncnt * fndims];
                            count[m] = this_count[m + regioncnt * fndims];
                            regionsize *= count[m];
                        }
                    }
                    else
                    {
                        for (int m = 0; m < fndims; m++)
                        {
                            start[m] = tmp_start[m + regioncnt * fndims];
                            count[m] = tmp_count[m + regioncnt * fndims];
                            regionsize *= count[m];
                        }
                    }
                    loffset += regionsize;

#ifdef _NETCDF
                    /* Cant use switch here because MPI_DATATYPE may not be simple (openmpi). */
                    if (iodesc->basetype == MPI_DOUBLE || iodesc->basetype == MPI_REAL8)
                        ierr = nc_get_vara_double(file->fh, vid,start, count, bufptr);
                    else if (iodesc->basetype == MPI_INTEGER)
                        ierr = nc_get_vara_int(file->fh, vid, start, count,  bufptr);
                    else if (iodesc->basetype == MPI_FLOAT || iodesc->basetype == MPI_REAL4)
                        ierr = nc_get_vara_float(file->fh, vid, start, count,  bufptr);
                    else
                        return pio_err(ios, NULL, PIO_EBADTYPE, __FILE__, __LINE__);

                    if (ierr)
                        for (int i = 0; i < fndims; i++)
                            fprintf(stderr,"vid %d dim %d start %ld count %ld err %d\n",
                                    vid, i, start[i], count[i], ierr);
#endif
                }

                if (rtask < ios->num_iotasks)
                    if ((mpierr = MPI_Send(iobuf, tmp_bufsize, iodesc->basetype, rtask,
                                           4 * ios->num_iotasks + rtask, ios->io_comm)))
                        return check_mpi(file, mpierr, __FILE__, __LINE__);
            }
        }
    }

    ierr = check_netcdf(file, ierr, __FILE__, __LINE__);

#ifdef TIMING
    /* Stop timing this function. */
    GPTLstop("PIO:read_darray_nc_serial");
#endif

    return ierr;
}

/**
 * Flush the output buffer. This is only relevant for files opened
 * with pnetcdf.
 *
 * @param file a pointer to the open file descriptor for the file
 * that will be written to
 * @param force true to force the flushing of the buffer
 * @param addsize additional size to add to buffer (in bytes)
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_write_darray
 */
int flush_output_buffer(file_desc_t *file, bool force, PIO_Offset addsize)
{
    int mpierr;  /* Return code from MPI functions. */
    int ierr = PIO_NOERR;

#ifdef _PNETCDF
    var_desc_t *vdesc;
    PIO_Offset usage = 0;

    /* Check inputs. */
    pioassert(file, "invalid input", __FILE__, __LINE__);

    /* Find out the buffer usage. If I check the turn code, some tests fail. ??? */
    if ((ierr = ncmpi_inq_buffer_usage(file->fh, &usage)))
        return ierr;
    /*return pio_err(ios, file, PIO_EBADID, __FILE__, __LINE__);*/
    
    /* If we are not forcing a flush, spread the usage to all IO
     * tasks. */
    if (!force && file->iosystem->io_comm != MPI_COMM_NULL)
    {
        usage += addsize;
        if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &usage, 1,  MPI_OFFSET,  MPI_MAX,
                                    file->iosystem->io_comm)))
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* Keep track of the maximum usage. */
    if (usage > maxusage)
        maxusage = usage;

    /* If the user forces it, or the buffer has exceeded the size
     * limit, then flush to disk. */
    if (force || usage >= pio_buffer_size_limit)
    {
        int rcnt;
        int  maxreq;
        int reqcnt;
        maxreq = 0;
        reqcnt = 0;
        rcnt = 0;
        for (int i = 0; i < PIO_MAX_VARS; i++)
        {
            vdesc = file->varlist + i;
            reqcnt += vdesc->nreqs;
            if (vdesc->nreqs > 0)
                maxreq = i;
        }
        int request[reqcnt];
        int status[reqcnt];

        for (int i = 0; i <= maxreq; i++)
        {
            vdesc = file->varlist + i;
#ifdef MPIO_ONESIDED
            /*onesided optimization requires that all of the requests in a wait_all call represent
              a contiguous block of data in the file */
            if (rcnt > 0 && (prev_record != vdesc->record || vdesc->nreqs==0))
            {
                ierr = ncmpi_wait_all(file->fh, rcnt, request, status);
                rcnt = 0;
            }
            prev_record = vdesc->record;
#endif
            for (reqcnt = 0; reqcnt < vdesc->nreqs; reqcnt++)
                request[rcnt++] = max(vdesc->request[reqcnt], NC_REQ_NULL);

            if (vdesc->request != NULL)
                free(vdesc->request);
            vdesc->request = NULL;
            vdesc->nreqs = 0;

#ifdef FLUSH_EVERY_VAR
            ierr = ncmpi_wait_all(file->fh, rcnt, request, status);
            rcnt = 0;
#endif
        }

        if (rcnt > 0)
            ierr = ncmpi_wait_all(file->fh, rcnt, request, status);

        /* Release resources. */
        for (int i = 0; i < PIO_MAX_VARS; i++)
        {
            vdesc = file->varlist + i;
            if (vdesc->iobuf)
            {
                brel(vdesc->iobuf);
                vdesc->iobuf = NULL;
            }
            if (vdesc->fillbuf)
            {
                brel(vdesc->fillbuf);
                vdesc->fillbuf = NULL;
            }
        }
    }

#endif /* _PNETCDF */
    return ierr;
}

/**
 * Print out info about the buffer for debug purposes.
 *
 * @param ios the IO system structure
 * @param collective true if collective report is desired
 * @ingroup PIO_write_darray
 */
void cn_buffer_report(iosystem_desc_t ios, bool collective)
{
    int mpierr;  /* Return code from MPI functions. */

    LOG((2, "cn_buffer_report ios.iossysid = %d collective = %d CN_bpool = %d",
         ios.iosysid, collective, CN_bpool));
    if (CN_bpool)
    {
        long bget_stats[5];
        long bget_mins[5];
        long bget_maxs[5];

        bstats(bget_stats, bget_stats+1,bget_stats+2,bget_stats+3,bget_stats+4);
        if (collective)
        {
            LOG((3, "cn_buffer_report calling MPI_Reduce ios.comp_comm = %d", ios.comp_comm));
            if ((mpierr = MPI_Reduce(bget_stats, bget_maxs, 5, MPI_LONG, MPI_MAX, 0, ios.comp_comm)))
                check_mpi(NULL, mpierr, __FILE__, __LINE__);
            LOG((3, "cn_buffer_report calling MPI_Reduce"));
            if ((mpierr = MPI_Reduce(bget_stats, bget_mins, 5, MPI_LONG, MPI_MIN, 0, ios.comp_comm)))
                check_mpi(NULL, mpierr, __FILE__, __LINE__);
            if (ios.compmaster == MPI_ROOT)
            {
                printf("PIO: Currently allocated buffer space %ld %ld\n",
                       bget_mins[0], bget_maxs[0]);
                printf("PIO: Currently available buffer space %ld %ld\n",
                       bget_mins[1], bget_maxs[1]);
                printf("PIO: Current largest free block %ld %ld\n",
                       bget_mins[2], bget_maxs[2]);
                printf("PIO: Number of successful bget calls %ld %ld\n",
                       bget_mins[3], bget_maxs[3]);
                printf("PIO: Number of successful brel calls  %ld %ld\n",
                       bget_mins[4], bget_maxs[4]);
            }
        }
        else
        {
            printf("%d: PIO: Currently allocated buffer space %ld \n",
                   ios.union_rank, bget_stats[0]) ;
            printf("%d: PIO: Currently available buffer space %ld \n",
                   ios.union_rank, bget_stats[1]);
            printf("%d: PIO: Current largest free block %ld \n",
                   ios.union_rank, bget_stats[2]);
            printf("%d: PIO: Number of successful bget calls %ld \n",
                   ios.union_rank, bget_stats[3]);
            printf("%d: PIO: Number of successful brel calls  %ld \n",
                   ios.union_rank, bget_stats[4]);
        }
    }
}

/**
 * Free the buffer pool. If malloc is used (that is, PIO_USE_MALLOC is
 * non zero), this function does nothing.
 *
 * @param ios the IO system structure
 * @ingroup PIO_write_darray
 */
void free_cn_buffer_pool(iosystem_desc_t ios)
{
#if !PIO_USE_MALLOC
    LOG((2, "free_cn_buffer_pool CN_bpool = %d", CN_bpool));
    if (CN_bpool)
    {
        cn_buffer_report(ios, false);
        bpoolrelease(CN_bpool);
        LOG((2, "free_cn_buffer_pool done!"));
        free(CN_bpool);
        CN_bpool = NULL;
    }
#endif /* !PIO_USE_MALLOC */
}

/**
 * Flush the buffer.
 *
 * @param ncid identifies the netCDF file
 * @param wmb May be NULL, in which case function returns.
 * @param flushtodisk
 * @ingroup PIO_write_darray
 */
void flush_buffer(int ncid, wmulti_buffer *wmb, bool flushtodisk)
{
    /* Check inputs. */
    if (!wmb)
        return;

    if (wmb->validvars > 0)
    {
        PIOc_write_darray_multi(ncid, wmb->vid,  wmb->ioid, wmb->validvars,
                                wmb->arraylen, wmb->data, wmb->frame,
                                wmb->fillvalue, flushtodisk);
        wmb->validvars = 0;
        brel(wmb->vid);
        wmb->vid = NULL;
        brel(wmb->data);
        wmb->data = NULL;
        if (wmb->fillvalue)
            brel(wmb->fillvalue);
        if (wmb->frame)
            brel(wmb->frame);
        wmb->fillvalue = NULL;
        wmb->frame = NULL;
    }
}

/**
 * Compute the maximum aggregate number of bytes.
 *
 * @param ios the IO system structure
 * @param iodesc a pointer to the defined iodescriptor for the
 * buffer. If NULL, function returns immediately.
 */
void compute_maxaggregate_bytes(iosystem_desc_t ios, io_desc_t *iodesc)
{
    int maxbytesoniotask = INT_MAX;
    int maxbytesoncomputetask = INT_MAX;
    int maxbytes;
    int mpierr;  /* Return code from MPI functions. */

    /* Check inputs. */
    if (!iodesc)
        return;

    LOG((2, "compute_maxaggregate_bytes iodesc->maxiobuflen = %d iodesc->ndof = %d",
	 iodesc->maxiobuflen, iodesc->ndof));

    if (ios.ioproc && iodesc->maxiobuflen > 0)
        maxbytesoniotask = pio_buffer_size_limit / iodesc->maxiobuflen;

    if (ios.comp_rank >= 0 && iodesc->ndof > 0)
        maxbytesoncomputetask = pio_cnbuffer_limit / iodesc->ndof;

    maxbytes = min(maxbytesoniotask, maxbytesoncomputetask);
    LOG((2, "compute_maxaggregate_bytes maxbytesoniotask = %d maxbytesoncomputetask = %d",
	 maxbytesoniotask, maxbytesoncomputetask));

    if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &maxbytes, 1, MPI_INT, MPI_MIN,
                                ios.union_comm)))
        check_mpi(NULL, mpierr, __FILE__, __LINE__);
    iodesc->maxbytes = maxbytes;
}
