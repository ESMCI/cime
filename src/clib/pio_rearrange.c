/** @file
 * Code to map IO to model decomposition.
 *
 * @author Jim Edwards
 */
#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/**
 * Internal library util function to initialize rearranger
 * options. This is used in PIOc_Init_Intracomm().
 *
 * @param iosys pointer to iosystem descriptor
 */
void init_rearr_opts(iosystem_desc_t *iosys)
{
    /* The old default for max pending requests was 64 - we no longer use it*/

    /* Disable handshake /isend and set max_pend_req = 0 to turn of throttling */
    const rearr_comm_fc_opt_t def_coll_comm_fc_opts = { false, false, 0 };

    pioassert(iosys, "invalid input", __FILE__, __LINE__);

    /* Default to coll - i.e., no flow control */
    iosys->rearr_opts.comm_type = PIO_REARR_COMM_COLL;
    iosys->rearr_opts.fcd = PIO_REARR_COMM_FC_2D_DISABLE;
    iosys->rearr_opts.comm_fc_opts_comp2io = def_coll_comm_fc_opts;
    iosys->rearr_opts.comm_fc_opts_io2comp = def_coll_comm_fc_opts;
}

/**
 * Convert an index into a list of dimensions. E.g., for index 4 into a
 * array defined as a[3][2], will return 1 1.
 *
 * @param ndims number of dimensions.
 * @param gdimlen array of length ndims with the dimension sizes.
 * @param idx the index to convert.
 * @param dim_list array of length ndims that will get the dimensions
 * corresponding to this index.
 */
void idx_to_dim_list(int ndims, const int *gdimlen, PIO_Offset idx,
                     PIO_Offset *dim_list)
{
    int curr_idx = idx;
    int next_idx;

    /* Check inputs. */
    pioassert(gdimlen && dim_list, "invalid input", __FILE__,
              __LINE__);
    LOG((2, "idx_to_dim_list ndims = %d idx = %d"));
    /* This fails sometimes! Under investigation... */
    /* pioassert(gdimlen && dim_list && idx >= 0, "invalid input", __FILE__, */
    /*           __LINE__); */
    
    /* Easiest to start from the right and move left. */
    for (int i = ndims - 1; i >= 0; --i)
    {
        /* This way of doing div/mod is slightly faster than using "/"
         * and "%". */
        next_idx = curr_idx / gdimlen[i];
        dim_list[i] = curr_idx - (next_idx * gdimlen[i]);
        curr_idx = next_idx;
    }
}

/**
 * Expand a region along dimension dim, by incrementing count[i] as
 * much as possible, consistent with the map.
 *
 * Once max_size is reached, the map is exhausted, or the next entries fail
 * to match, expand_region updates the count and calls itself with the next
 * outermost dimension, until the region has been expanded as much as
 * possible along all dimensions.
 *
 * Precondition: maplen >= region_size (thus loop runs at least
 * once). 
 *
 * @param dim the dimension number to start with.
 * @param gdimlen array of global dimension lengths.
 * @param maplen the length of the map.
 * @param map ???
 * @param region_size ???
 * @param region_stride amount incremented along dimension.
 * @param max_size array of size dim + 1 that contains the maximum
 * sizes along that dimension.
 * @param count array of size dim + 1 that gets the new counts.
 */
void expand_region(int dim, const int *gdimlen, int maplen, const PIO_Offset *map,
                   int region_size, int region_stride, const int *max_size,
                   PIO_Offset *count)
{
    /* Flag used to signal that we can no longer expand the region
       along dimension dim. */
    int expansion_done = 0;

    /* Check inputs. */
    pioassert(dim >= 0 && gdimlen && maplen >= 0 && map && region_size >= 0 &&
              maplen >= region_size && region_stride >= 0 && max_size && count,
              "invalid input", __FILE__, __LINE__);
    
    /* Expand no greater than max_size along this dimension. */
    for (int i = 1; i <= max_size[dim]; ++i)
    {
        /* Count so far is at least i. */
        count[dim] = i;

        /* Now see if we can expand to i+1 by checking that the next
           region_size elements are ahead by exactly region_stride.
           Assuming monotonicity in the map, we could skip this for the
           innermost dimension, but it's necessary past that because the
           region does not necessarily comprise contiguous values. */
        for (int j = 0; j < region_size; j++)
        {
            int test_idx; /* Index we are testing. */
            
            test_idx = j + i * region_size;

            /* If we have exhausted the map, or the map no longer matches,
               we are done, break out of both loops. */
            if (test_idx >= maplen || map[test_idx] != map[j] + i * region_stride)
            {
                expansion_done = 1;
                break;
            }
        }
        if (expansion_done)
            break;
    }

    /* Move on to next outermost dimension if there are more left,
     * else return. */
    if (dim > 0)
        expand_region(dim - 1, gdimlen, maplen, map, region_size * count[dim],
                      region_stride * gdimlen[dim], max_size, count);
}

/**
 * Set start and count so that they describe the first region in map.
 *
 * Preconditions
 * 
 * ndims is > 0
 *
 * maplen is > 0
 *
 * All elements of map are inside the bounds specified by gdimlen.
 * 
 * Note that the map array is 1 based, but calculations are 0 based.
 *
 * @param ndims the number of dimensions.
 * @param gdimlen an array length ndims with the sizes of the global
 * dimensions.
 * @param maplen the length of the map.
 * @param map
 * @param start array of length ndims with start indicies.
 * @param count array of length ndims with counts.
 * @returns length of the region found.
 */
PIO_Offset find_region(int ndims, const int *gdimlen, int maplen, const PIO_Offset *map,
                       PIO_Offset *start, PIO_Offset *count)
{
    int max_size[ndims];
    PIO_Offset regionlen = 1;

    /* Check inputs. */
    pioassert(ndims > 0 && gdimlen && maplen > 0 && map && start && count,
              "invalid input", __FILE__, __LINE__);

    LOG((2, "find_region ndims = %d maplen = %d", ndims, maplen));

    idx_to_dim_list(ndims, gdimlen, map[0] - 1, start);

    /* Can't expand beyond the array edge.*/
    for (int dim = 0; dim < ndims; ++dim)
    {
        max_size[dim] = gdimlen[dim] - start[dim];
        LOG((3, "max_size[%d] = %d", max_size[dim]));
    }

    /* For each dimension, figure out how far we can expand in that dimension
       while staying contiguous in the input array.

       Start with the innermost dimension (ndims-1), and it will recurse
       through to the outermost dimensions. */
    expand_region(ndims - 1, gdimlen, maplen, map, 1, 1, max_size, count);

    for (int dim = 0; dim < ndims; dim++)
        regionlen *= count[dim];

    return regionlen;
}

/**
 * Convert a global coordinate value into a local array index.
 *
 * @param ndims the number of dimensions.
 * @param lcoord pointer to an offset.
 * @param count array of counts.
 * @returns the local array index.
 */
PIO_Offset coord_to_lindex(int ndims, const PIO_Offset *lcoord, const PIO_Offset *count)
{
    PIO_Offset lindex = 0;
    PIO_Offset stride = 1;

    /* Check inputs. */
    pioassert(ndims > 0 && lcoord && count, "invalid input", __FILE__, __LINE__);

    for (int i = ndims - 1; i >= 0; i--)
    {
        lindex += lcoord[i] * stride;
        stride = stride * count[i];
    }
    return lindex;
}

/**
 * Compute the max io buffer size needed for an iodesc. It is the
 * combined size (in number of data elements) of all the regions of
 * data stored in the buffer of this iodesc. The max size is then set
 * in the iodesc.
 *
 * @param io_comm the IO communicator
 * @param iodesc a pointer to the io_desc_t struct.
 * @returns 0 for success, error code otherwise.
 */
int compute_maxIObuffersize(MPI_Comm io_comm, io_desc_t *iodesc)
{
    PIO_Offset totiosize = 0;
    int mpierr; /* Return code from MPI calls. */

    pioassert(iodesc, "need iodesc", __FILE__, __LINE__);

    /*  compute the max io buffer size, for conveneance it is the
     *  combined size of all regions */
    for (io_region *region = iodesc->firstregion; region; region = region->next)
    {
        if (region->count[0] > 0)
        {
            PIO_Offset iosize = 1;
            for (int i = 0; i < iodesc->ndims; i++)
                iosize *= region->count[i];
            totiosize += iosize;
        }
    }
    LOG((2, "compute_maxIObuffersize got totiosize = %lld", totiosize));

    /* Share the max io buffer size with all io tasks. */
    if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &totiosize, 1, MPI_OFFSET, MPI_MAX, io_comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    LOG((2, "after allreduce compute_maxIObuffersize got totiosize = %lld", totiosize));
    iodesc->maxiobuflen = totiosize;

    if (iodesc->maxiobuflen <= 0)
        return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);
    LOG((2, "compute_maxIObuffersize got totiosize = %lld", totiosize));

    return PIO_NOERR;
}

/**
 * Create the derived MPI datatypes used for comp2io and io2comp
 * transfers. Used in define_iodesc_datatypes().
 *
 * @param basetype The MPI type of data (MPI_INT, etc.).
 * @param msgcnt This is the number of MPI types that are created.
 * @param mindex An array (length numinds) of indexes into the data
 * array from the comp map.
 * @param mcount An array (length msgcnt) with the number of indexes
 * to be put on each mpi message/task.
 * @param mfrom A pointer to the previous structure in the read/write
 * list. This is always NULL for the BOX rearranger.
 * @param mtype pointer to an array of length msgcnt which gets the
 * created datatypes.
 * @returns 0 on success, error code otherwise.
 */
int create_mpi_datatypes(MPI_Datatype basetype, int msgcnt,
                         const PIO_Offset *mindex, const int *mcount, int *mfrom,
                         MPI_Datatype *mtype)
{
    PIO_Offset bsizeT[msgcnt];
    int blocksize;
    int numinds = 0;
    PIO_Offset *lindex = NULL;
    int mpierr; /* Return code from MPI functions. */

    pioassert(mcount && numinds >= 0, "invalid input", __FILE__, __LINE__);

    LOG((1, "create_mpi_datatypes basetype = %d msgcnt = %d", basetype, msgcnt));
    LOG((2, "MPI_BYTE = %d MPI_CHAR = %d MPI_SHORT = %d MPI_INT = %d MPI_DOUBLE = %d",
         MPI_BYTE, MPI_CHAR, MPI_SHORT, MPI_INT, MPI_DOUBLE));

    /* How many indicies in the array? */
    for (int j = 0; j < msgcnt; j++)
        numinds += mcount[j];
    LOG((2, "numinds = %d", numinds));

    if (mindex)
    {
        if (!(lindex = malloc(numinds * sizeof(PIO_Offset))))
            return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);
        memcpy(lindex, mindex, (size_t)(numinds * sizeof(PIO_Offset)));
        LOG((3, "allocated lindex, copied mindex"));
    }

    bsizeT[0] = 0;
    mtype[0] = PIO_DATATYPE_NULL;
    int pos = 0;
    int ii = 0;

    /* If there are no messages don't need to create any datatypes. */
    if (msgcnt > 0)
    {
        if (mfrom == NULL)
        {
            LOG((3, "mfrom is NULL"));
            for (int i = 0; i < msgcnt; i++)
            {
                if (mcount[i] > 0)
                {
                    /* Look for the largest block of data for io which
                     * can be expressed in terms of start and
                     * count. */
                    bsizeT[ii] = GCDblocksize(mcount[i], lindex + pos);
                    ii++;
                    pos += mcount[i];
                }
            }
            blocksize = (int)lgcd_array(ii, bsizeT);
        }
        else
        {
            blocksize = 1;
        }
        LOG((3, "blocksize = %d", blocksize));

        /* pos is an index to the start of each message block. */
        pos = 0;
        for (int i = 0; i < msgcnt; i++)
        {
            if (mcount[i] > 0)
            {
                int len = mcount[i] / blocksize;
                int displace[len];
                if (blocksize == 1)
                {
                    if (!mfrom)
                    {
                        for (int j = 0; j < len; j++)
                            displace[j] = (int)(lindex[pos + j]);
                    }
                    else
                    {
                        int k = 0;
                        for (int j = 0; j < numinds; j++)
                            if (mfrom[j] == i)
                                displace[k++] = (int)(lindex[j]);
                    }

                }
                else
                {
                    for (int j = 0; j < mcount[i]; j++)
                        (lindex + pos)[j]++;

                    for (int j = 0; j < len; j++)
                        displace[j] = ((lindex + pos)[j * blocksize] - 1);
                }

#ifdef PIO_ENABLE_LOGGING
                for (int j = 0; j <len; j++)
                    LOG((3, "displace[%d] = %d", j, displace[j]));
#endif /* PIO_ENABLE_LOGGING */

                LOG((3, "calling MPI_Type_create_indexed_block len = %d blocksize = %d "
                     "basetype = %d", len, blocksize, basetype));
                /* Create an indexed datatype with constant-sized blocks. */
                if ((mpierr = MPI_Type_create_indexed_block(len, blocksize, displace,
                                                            basetype, &mtype[i])))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);

                if (mtype[i] == PIO_DATATYPE_NULL)
                    return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

                /* Commit the MPI data type. */
                LOG((3, "about to commit type"));
                if ((mpierr = MPI_Type_commit(mtype + i)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                pos += mcount[i];
            }
        }

        /* Free resources. */
        if (lindex)
            free(lindex);
    }

    return PIO_NOERR;
}

/**
 * Create the derived MPI datatypes used for comp2io and io2comp
 * transfers.
 *
 * NOTE from Jim: I am always oriented toward write so recieve
 * always means io tasks and send always means comp tasks. The
 * opposite relationship is actually the case for reading. I've
 * played with different ways of referring to things to get rid of
 * this orientation bias in the documentation as well as in
 * variable names, but I haven't found anything that I found more
 * satisfactory.
 *
 * @param ios pointer to the iosystem_desc_t struct.
 * @param iodesc a pointer to the io_desc_t struct.
 * @returns 0 on success, error code otherwise.
 */
int define_iodesc_datatypes(iosystem_desc_t *ios, io_desc_t *iodesc)
{
    int ret; /* Return value. */

    pioassert(ios && iodesc, "invalid input", __FILE__, __LINE__);
    LOG((1, "define_iodesc_datatypes ios->ioproc = %d iodesc->rtype = %d iodesc->stype = %d",
         ios->ioproc, iodesc->rtype, iodesc->stype));

    /* Set up the to transfer data to and from the IO tasks. */
    if (ios->ioproc)
    {
        if (!iodesc->rtype)
        {
            if (iodesc->nrecvs > 0)
            {
                /* Allocate memory for array of MPI types for the IO tasks. */
                if (!(iodesc->rtype = malloc(iodesc->nrecvs * sizeof(MPI_Datatype))))
                    return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
                LOG((2, "allocated memory for IO task MPI types iodesc->nrecvs = %d "
                     "iodesc->rearranger = %d", iodesc->nrecvs, iodesc->rearranger));

                /* Initialize data types to NULL. */
                for (int i = 0; i < iodesc->nrecvs; i++)
                    iodesc->rtype[i] = PIO_DATATYPE_NULL;

                /* Create the datatypes, which will be used both to
                 * receive and to send data. */
                LOG((3, "about to call create_mpi_datatypes for IO MPI types"));
                if (iodesc->rearranger == PIO_REARR_SUBSET)
                {
                    if ((ret = create_mpi_datatypes(iodesc->basetype, iodesc->nrecvs, iodesc->rindex,
                                                    iodesc->rcount, iodesc->rfrom, iodesc->rtype)))
                        return pio_err(ios, NULL, ret, __FILE__, __LINE__);
                }
                else
                {
                    if ((ret = create_mpi_datatypes(iodesc->basetype, iodesc->nrecvs, iodesc->rindex,
                                                    iodesc->rcount, NULL, iodesc->rtype)))
                        return pio_err(ios, NULL, ret, __FILE__, __LINE__);
                }
            }
        }
    }

    /* Define the datatypes for the computation components if they
     * don't exist. (These will be the send side in a write
     * operation.) */
    if (!iodesc->stype)
    {
        int ntypes;

        /* Subset rearranger gets one type; box rearranger gets one
         * type per IO task. */
        if (iodesc->rearranger == PIO_REARR_SUBSET)
            ntypes = 1;
        else
            ntypes = ios->num_iotasks;

        /* Allocate memory for array of MPI types for the computation tasks. */
        if (!(iodesc->stype = malloc(ntypes * sizeof(MPI_Datatype))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
        LOG((3, "allocated memory for computation MPI types ntypes = %d", ntypes));

        /* Initialize send types to NULL. */
        for (int i = 0; i < ntypes; i++)
            iodesc->stype[i] = PIO_DATATYPE_NULL;

        /* Remember how many types we created for the send side. */
        iodesc->num_stypes = ntypes;

        /* Create the MPI data types. */
        LOG((3, "about to call create_mpi_datatypes for computation MPI types"));
        if ((ret = create_mpi_datatypes(iodesc->basetype, ntypes, iodesc->sindex,
                                        iodesc->scount, NULL, iodesc->stype)))
            return pio_err(ios, NULL, ret, __FILE__, __LINE__);
    }

    return PIO_NOERR;
}

/**
 *  Completes the mapping for the box rearranger.
 *
 * @param ios pointer to the iosystem_desc_t struct.
 * @param iodesc a pointer to the io_desc_t struct.
 * @param maplen the length of the map.
 * @param dest_ioproc an array of IO task numbers.
 * @param dest_ioindex
 * @param mycomm an MPI communicator.
 * @returns 0 on success, error code otherwise.
 */
int compute_counts(iosystem_desc_t *ios, io_desc_t *iodesc, int maplen,
                   const int *dest_ioproc, const PIO_Offset *dest_ioindex,
                   MPI_Comm mycomm)
{
    int i;
    int iorank;
    int rank;
    int ntasks;
    int mpierr; /* Return call from MPI functions. */

    /* Check inputs. */
    pioassert(ios && iodesc && maplen >= 0 && dest_ioproc && dest_ioindex,
              "invalid input", __FILE__, __LINE__);

    /* Find size of communicator, and task rank. */
    if ((mpierr = MPI_Comm_rank(mycomm, &rank)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    if ((mpierr = MPI_Comm_size(mycomm, &ntasks)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    MPI_Datatype sr_types[ntasks];
    int send_counts[ntasks];
    int send_displs[ntasks];
    int recv_counts[ntasks];
    int recv_displs[ntasks];
    int *recv_buf = NULL;
    int nrecvs;
    int ierr;
    int io_comprank;
    int ioindex;
    int tsize;
    int numiotasks;
    PIO_Offset s2rindex[iodesc->ndof];

    /* Subset rearranger always gets 1 IO task. */
    if (iodesc->rearranger == PIO_REARR_BOX)
        numiotasks = ios->num_iotasks;
    else
        numiotasks = 1;

    /* Allocate memory for the array of counts. */
    if (!(iodesc->scount = malloc(numiotasks * sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    /* Initialize counts to zero. */
    for (i = 0; i < numiotasks; i++)
        iodesc->scount[i] = 0;

    /* iodesc->scount is the amount of data sent to each task from the
     * current task */
    for (i = 0; i < maplen; i++)
        if (dest_ioindex[i] >= 0)
            (iodesc->scount[dest_ioproc[i]])++;

    /* Initialize arrays. */
    for (i = 0; i < ntasks; i++)
    {
        send_counts[i] = 0;
        send_displs[i] = 0;
        recv_counts[i] = 0;
        recv_displs[i] = 0;
        sr_types[i] = MPI_INT;
    }

    /* Setup for the swapm call at line 550 iodesc->scount is the
     * amount of data this compute task will transfer to/from each
     * iotask. For the subset rearranger there is only one io task per
     * compute task, for the box rearranger there can be more than
     * one. This provides enough information to know the size of data
     * on the iotask, so at line 557 we allocate arrays to hold the
     * map on the iotasks. iodesc->rcount is an array of the amount of
     * data to expect from each compute task and iodesc->rfrom is the
     * rank of that task. */
    for (i = 0; i < numiotasks; i++)
    {
        int io_comprank;
        if (iodesc->rearranger == PIO_REARR_SUBSET)
            io_comprank = 0;
        else
            io_comprank = ios->ioranks[i];
        send_counts[io_comprank] = 1;
        send_displs[io_comprank] = i * sizeof(int);
    }

    /* ??? */
    if (ios->ioproc)
    {
        /* Allocate memory to hold array of tasks that have recieved
         * data ??? */
        if (!(recv_buf = calloc(ntasks, sizeof(int))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

        /* Initialize arrays that keep track of receives. */
        for (i = 0; i < ntasks; i++)
        {
            recv_counts[i] = 1;
            recv_displs[i] = i * sizeof(int);
        }
    }

    /* Share the iodesc->scount from each compute task to all io tasks. */
    if ((ierr = pio_swapm(iodesc->scount, send_counts, send_displs, sr_types,
                          recv_buf, recv_counts, recv_displs, sr_types, mycomm,
                          iodesc->rearr_opts.comm_fc_opts_comp2io.enable_hs,
                          iodesc->rearr_opts.comm_fc_opts_comp2io.enable_isend,
                          iodesc->rearr_opts.comm_fc_opts_comp2io.max_pend_req)))
        return pio_err(ios, NULL, ierr, __FILE__, __LINE__);        

    /* ??? */
    nrecvs = 0;
    if (ios->ioproc)
    {
        for (i = 0; i < ntasks; i++)
            if (recv_buf[i] != 0)
                nrecvs++;

        /* Get memory to hold the count of data receives. */
        if (!(iodesc->rcount = malloc(max(1, nrecvs) * sizeof(int))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

        /* Get memory to hold the list of task data was from. */
        if (!(iodesc->rfrom = malloc(max(1, nrecvs) * sizeof(int))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

        for (i = 0; i < max(1, nrecvs); i++)
        {
            iodesc->rcount[i] = 0;
            iodesc->rfrom[i] = 0;
        }

        nrecvs = 0;
        for (i = 0; i < ntasks; i++)
        {
            if (recv_buf[i] != 0)
            {
                iodesc->rcount[nrecvs] = recv_buf[i];
                iodesc->rfrom[nrecvs] = i;
                nrecvs++;
            }
        }
        free(recv_buf);
    }

    /* ??? */
    iodesc->nrecvs = nrecvs;

    /* Allocate an array for indicies on the computation tasks (the
     * send side when writing). */
    if (iodesc->sindex == NULL && iodesc->ndof > 0)
        if (!(iodesc->sindex = malloc(iodesc->ndof * sizeof(PIO_Offset))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    int tempcount[numiotasks];
    int spos[numiotasks];

    /* ??? */
    spos[0] = 0;
    tempcount[0] = 0;
    for (i = 1; i < numiotasks; i++)
    {
        spos[i] = spos[i - 1] + iodesc->scount[i - 1];
        tempcount[i] = 0;
    }

    /* ??? */
    for (i = 0; i < maplen; i++)
    {
        iorank = dest_ioproc[i];
        ioindex = dest_ioindex[i];
        if (iorank > -1)
        {
            /* this should be moved to create_box */
            if (iodesc->rearranger == PIO_REARR_BOX)
                iodesc->sindex[spos[iorank] + tempcount[iorank]] = i;

            s2rindex[spos[iorank] + tempcount[iorank]] = ioindex;
            (tempcount[iorank])++;
        }
    }

    /* Initialize arrays to zeros. */
    for (i = 0; i < ntasks; i++)
    {
        send_counts[i] = 0;
        send_displs[i] = 0;
        recv_counts[i] = 0;
        recv_displs[i] = 0;
    }

    /* Find the size of the offset type. */
    if ((mpierr = MPI_Type_size(MPI_OFFSET, &tsize)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    for (i = 0; i < ntasks; i++)
        sr_types[i] = MPI_OFFSET;

    /* ??? */
    for (i = 0; i < numiotasks; i++)
    {
        /* Subset rearranger needs one type, box rearranger needs one for
         * each IO task. */
        if (iodesc->rearranger == PIO_REARR_BOX)
            io_comprank = ios->ioranks[i];
        else
            io_comprank = 0;

        send_counts[io_comprank] = iodesc->scount[i];
        if (send_counts[io_comprank] > 0)
            send_displs[io_comprank] = spos[i] * tsize;
    }

    /* Only do this on IO tasks. */
    if (ios->ioproc)
    {
        int totalrecv = 0;
        for (i = 0; i < nrecvs; i++)
        {
            recv_counts[iodesc->rfrom[i]] = iodesc->rcount[i];
            totalrecv += iodesc->rcount[i];
        }
        recv_displs[0] = 0;
        for (i = 1; i < nrecvs; i++)
            recv_displs[iodesc->rfrom[i]] = recv_displs[iodesc->rfrom[i - 1]] +
                iodesc->rcount[i - 1] * tsize;

        /*  rindex is an array of the indices of the data to be sent from
            this io task to each compute task. */
        if (totalrecv > 0)
        {
            totalrecv = iodesc->llen;  /* can reduce memory usage here */
            if (!(iodesc->rindex = calloc(totalrecv, sizeof(PIO_Offset))))
                return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
        }
    }

    /* Here we are sending the mapping from the index on the compute
     * task to the index on the io task. */
    /* s2rindex is the list of indeces on each compute task */
    ierr = pio_swapm(s2rindex, send_counts, send_displs, sr_types, iodesc->rindex,
                     recv_counts, recv_displs, sr_types, mycomm,
                     iodesc->rearr_opts.comm_fc_opts_comp2io.enable_hs,
                     iodesc->rearr_opts.comm_fc_opts_comp2io.enable_isend,
                     iodesc->rearr_opts.comm_fc_opts_comp2io.max_pend_req);


    return ierr;
}

/**
 * Moves data from compute tasks to IO tasks.
 *
 * @param ios pointer to the iosystem_desc_t struct
 * @param iodesc a pointer to the io_desc_t struct.
 * @param sbuf send buffer.
 * @param rbuf receive buffer.
 * @param nvars number of variables.
 * @returns 0 on success, error code otherwise.
 */
int rearrange_comp2io(iosystem_desc_t *ios, io_desc_t *iodesc, void *sbuf,
                      void *rbuf, int nvars)
{
    int ntasks;
    int niotasks;
    int *scount = iodesc->scount;
    int i, tsize;
    int *sendcounts;
    int *recvcounts;
    int *sdispls;
    int *rdispls;
    MPI_Datatype *sendtypes;
    MPI_Datatype *recvtypes;
    MPI_Comm mycomm;
    int mpierr; /* Return code from MPI calls. */
    int ret;

#ifdef TIMING
    GPTLstart("PIO:rearrange_comp2io");
#endif

    /* Caller must provide these. */
    pioassert(iodesc && nvars > 0, "invalid input", __FILE__, __LINE__);

    LOG((2, "rearrange_comp2io nvars = %d iodesc->rearranger = %d", nvars,
         iodesc->rearranger));

    if (iodesc->rearranger == PIO_REARR_BOX)
    {
        mycomm = ios->union_comm;
        niotasks = ios->num_iotasks;
    }
    else
    {
        mycomm = iodesc->subset_comm;
        niotasks = 1;
    }

    /* Get the number of tasks. */
    if ((mpierr = MPI_Comm_size(mycomm, &ntasks)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    /* Get the size of the MPI type. */
    if ((mpierr = MPI_Type_size(iodesc->basetype, &tsize)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    LOG((3, "ntasks = %d tsize = %d", ntasks, tsize));

    /* Define the MPI data types that will be used for this
     * io_desc_t. */
    if ((ret = define_iodesc_datatypes(ios, iodesc)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    /* Allocate arrays needed by the pio_swapm() function. */
    if (!(sendcounts = calloc(ntasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(recvcounts = calloc(ntasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(sdispls = calloc(ntasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(rdispls = calloc(ntasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(sendtypes = malloc(ntasks * sizeof(MPI_Datatype))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(recvtypes = malloc(ntasks * sizeof(MPI_Datatype))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    /* Initialize arrays. */
    for (i = 0; i < ntasks; i++)
    {
        recvtypes[i] = PIO_DATATYPE_NULL;
        sendtypes[i] =  PIO_DATATYPE_NULL;
    }

    /* If this io proc will exchange data with compute tasks create a
     * MPI DataType for that exchange. */
    if (ios->ioproc && iodesc->nrecvs > 0)
    {
        for (i = 0; i < iodesc->nrecvs; i++)
        {
            if (iodesc->rtype[i] != PIO_DATATYPE_NULL)
            {
                if (iodesc->rearranger == PIO_REARR_SUBSET)
                {
                    recvcounts[ i ] = 1;

                    /*  The stride here is the length of the collected array (llen) */

                    if ((mpierr = MPI_Type_hvector(nvars, 1, (MPI_Aint) iodesc->llen * tsize, iodesc->rtype[i],
                                                   recvtypes + i)))
                        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

                    if (recvtypes[i] == PIO_DATATYPE_NULL)
                        return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

                    if ((mpierr = MPI_Type_commit(recvtypes + i)))
                        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

                    /*recvtypes[ i ] = iodesc->rtype[i]; */
                }
                else
                {
                    recvcounts[iodesc->rfrom[i]] = 1;

                    if ((mpierr = MPI_Type_hvector(nvars, 1, (MPI_Aint)iodesc->llen * tsize, iodesc->rtype[i],
                                                   recvtypes + iodesc->rfrom[i])))
                        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

                    if (recvtypes[iodesc->rfrom[i]] == PIO_DATATYPE_NULL)
                        return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

                    if ((mpierr = MPI_Type_commit(recvtypes+iodesc->rfrom[i])))
                        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

                    /* recvtypes[ iodesc->rfrom[i] ] = iodesc->rtype[i]; */
                    rdispls[iodesc->rfrom[i]] = 0;
                }
            }
        }
    }

    /* On compute tasks loop over iotasks and create a data type for
     * each exchange.  */
    for (i = 0; i < niotasks; i++)
    {
        int io_comprank = ios->ioranks[i];
        if (iodesc->rearranger == PIO_REARR_SUBSET)
            io_comprank=0;

        if (scount[i] > 0 && sbuf != NULL)
        {
            sendcounts[io_comprank] = 1;
            if ((mpierr = MPI_Type_hvector(nvars, 1, (MPI_Aint)iodesc->ndof * tsize, iodesc->stype[i],
                                           sendtypes + io_comprank)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);

            if (sendtypes[io_comprank] == PIO_DATATYPE_NULL)
                return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

            if ((mpierr = MPI_Type_commit(sendtypes + io_comprank)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        }
        else
        {
            sendcounts[io_comprank]=0;
        }
    }
    /* Data in sbuf on the compute nodes is sent to rbuf on the ionodes */
    pio_swapm(sbuf, sendcounts, sdispls, sendtypes,
              rbuf, recvcounts, rdispls, recvtypes, mycomm,
              iodesc->rearr_opts.comm_fc_opts_comp2io.enable_hs,
              iodesc->rearr_opts.comm_fc_opts_comp2io.enable_isend,
              iodesc->rearr_opts.comm_fc_opts_comp2io.max_pend_req);

    /* Free the MPI types. */
    for (i = 0; i < ntasks; i++)
    {
        if (sendtypes[i] != PIO_DATATYPE_NULL)
            if ((mpierr = MPI_Type_free(sendtypes + i)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);

        if (recvtypes[i] != PIO_DATATYPE_NULL)
            if ((mpierr = MPI_Type_free(recvtypes + i)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    }

    /* Free memory. */
    free(sendcounts);
    free(recvcounts);
    free(sdispls);
    free(rdispls);
    free(sendtypes);
    free(recvtypes);

#ifdef TIMING
    GPTLstop("PIO:rearrange_comp2io");
#endif

    return PIO_NOERR;
}

/**
 * Moves data from IO tasks to compute tasks.
 *
 * @param ios pointer to the iosystem_desc_t struct.
 * @param iodesc a pointer to the io_desc_t struct.
 * @param sbuf send buffer.
 * @param rbuf receive buffer.
 * @returns 0 on success, error code otherwise.
 */
int rearrange_io2comp(iosystem_desc_t *ios, io_desc_t *iodesc, void *sbuf,
                      void *rbuf)
{
    MPI_Comm mycomm;
    int ntasks;
    int niotasks;
    int *scount = iodesc->scount;
    int *sendcounts;
    int *recvcounts;
    int *sdispls;
    int *rdispls;
    MPI_Datatype *sendtypes;
    MPI_Datatype *recvtypes;
    int i;
    int mpierr; /* Return code from MPI calls. */
    int ret;

    /* Check inputs. */
    pioassert(iodesc, "invalid input", __FILE__, __LINE__);

#ifdef TIMING
    GPTLstart("PIO:rearrange_io2comp");
#endif

    /* Different rearrangers use different communicators and number of
     * IO tasks. */
    if (iodesc->rearranger == PIO_REARR_BOX)
    {
        mycomm = ios->union_comm;
        niotasks = ios->num_iotasks;
    }
    else
    {
        mycomm = iodesc->subset_comm;
        niotasks=1;
    }

    /* Get the size of this communicator. */
    if ((mpierr = MPI_Comm_size(mycomm, &ntasks)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);

    /* Define the MPI data types that will be used for this
     * io_desc_t. */
    if ((ret = define_iodesc_datatypes(ios, iodesc)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    /* Allocate arrays needed by the pio_swapm() function. */
    if (!(sendcounts = calloc(ntasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(recvcounts = calloc(ntasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(sdispls = calloc(ntasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(rdispls = calloc(ntasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(sendtypes = malloc(ntasks * sizeof(MPI_Datatype))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if (!(recvtypes = malloc(ntasks * sizeof(MPI_Datatype))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    /* Initialize arrays. */
    for (i = 0; i < ntasks; i++)
    {
        sendtypes[i] = PIO_DATATYPE_NULL;
        recvtypes[i] = PIO_DATATYPE_NULL;
    }

    /* In IO tasks ??? */
    if (ios->ioproc)
        for (i = 0; i < iodesc->nrecvs; i++)
            if (iodesc->rtype[i] != PIO_DATATYPE_NULL)
            {
                if (iodesc->rearranger == PIO_REARR_SUBSET)
                {
                    if (sbuf)
                    {
                        sendcounts[i] = 1;
                        sendtypes[i] = iodesc->rtype[i];
                    }
                }
                else
                {
                    sendcounts[iodesc->rfrom[i]] = 1;
                    sendtypes[iodesc->rfrom[i]] = iodesc->rtype[i];
                }
            }

    /* In the box rearranger each comp task may communicate with
     * multiple IO tasks here we are setting the count and data type
     * of the communication of a given compute task with each io
     * task. */
    for (i = 0; i < niotasks; i++)
    {
        int io_comprank = ios->ioranks[i];
        if (iodesc->rearranger == PIO_REARR_SUBSET)
            io_comprank = 0;

        if (scount[i] > 0 && iodesc->stype[i] != PIO_DATATYPE_NULL)
        {
            recvcounts[io_comprank] = 1;
            recvtypes[io_comprank] = iodesc->stype[i];
        }
    }

    /* Data in sbuf on the ionodes is sent to rbuf on the compute nodes */
    pio_swapm(sbuf, sendcounts, sdispls, sendtypes,
              rbuf, recvcounts, rdispls, recvtypes, mycomm,
              iodesc->rearr_opts.comm_fc_opts_io2comp.enable_hs,
              iodesc->rearr_opts.comm_fc_opts_io2comp.enable_isend,
              iodesc->rearr_opts.comm_fc_opts_io2comp.max_pend_req);

    /* Release memory. */
    free(sendcounts);
    free(recvcounts);
    free(sdispls);
    free(rdispls);
    free(sendtypes);
    free(recvtypes);

#ifdef TIMING
    GPTLstop("PIO:rearrange_io2comp");
#endif

    return PIO_NOERR;
}

/**
 * Determine whether fill values are needed. If we have enough data to
 * completely fill the variable, then fill is not needed. This
 * function compares how much data we have to how much data is in a
 * record (or non-record var).
 *
 * @param ios pointer to the iosystem_desc_t struct.
 * @param iodesc a pointer to the io_desc_t struct.
 * @param gsize pointer to an array length iodesc->ndims with the
 * global array sizes for one record (for record vars) or for the
 * entire var (for non-record vars).
 * @param compmap only used for the box communicator.
 * @returns 0 on success, error code otherwise.
 */
int determine_fill(iosystem_desc_t *ios, io_desc_t *iodesc, const int *gsize,
                   const PIO_Offset *compmap)
{
    PIO_Offset totalllen = 0;
    PIO_Offset totalgridsize = 1;
    int mpierr; /* Return code from MPI calls. */

    /* Check inputs. */
    pioassert(iodesc, "invalid input", __FILE__, __LINE__);

    /* Determine size of data space. */
    for (int i = 0; i < iodesc->ndims; i++)
        totalgridsize *= gsize[i];

    /* Determine how many values we have locally. */
    if (iodesc->rearranger == PIO_REARR_SUBSET)
        totalllen = iodesc->llen;
    else
        for (int i = 0; i < iodesc->ndof; i++)
            if (compmap[i] > 0)
                totalllen++;

    /* Add results accross communicator. */
    LOG((2, "determine_fill before allreduce totalllen = %d totalgridsize = %d",
         totalllen, totalgridsize));
    if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &totalllen, 1, PIO_OFFSET, MPI_SUM,
                                ios->union_comm)))
        check_mpi(NULL, mpierr, __FILE__, __LINE__);
    LOG((2, "after allreduce totalllen = %d", totalllen));

    /* If the total size of the data provided to be written is < the
     * total data size then we need fill values. */
    if (totalllen < totalgridsize)
        iodesc->needsfill = true;
    else
        iodesc->needsfill = false;

    /*  TURN OFF FILL for timing test
        iodesc->needsfill=false; */

    return PIO_NOERR;
}

/**
 * Prints the IO desc information to stdout.
 *
 * @param iodesc a pointer to the io_desc_t struct.
 * @returns 0 on success, error code otherwise.
 */
void iodesc_dump(io_desc_t *iodesc)
{
    pioassert(iodesc, "invalid input", __FILE__, __LINE__);

    printf("ioid= %d\n", iodesc->ioid);
/*    printf("async_id= %d\n",iodesc->async_id);*/
    printf("nrecvs= %d\n", iodesc->nrecvs);
    printf("ndof= %d\n", iodesc->ndof);
    printf("ndims= %d\n", iodesc->ndims);
    printf("num_aiotasks= %d\n", iodesc->num_aiotasks);
    printf("rearranger= %d\n", iodesc->rearranger);
    printf("maxregions= %d\n", iodesc->maxregions);
    printf("needsfill= %d\n", (int)iodesc->needsfill);

    printf("llen= %lld\n", iodesc->llen);
    printf("maxiobuflen= %d\n", iodesc->maxiobuflen);

    printf("rindex= ");
    for (int j = 0; j < iodesc->llen; j++)
        printf(" %lld ", iodesc->rindex[j]);
    printf("\n");
}

/**
 * The box rearranger computes a mapping between IO tasks and compute
 * tasks such that the data on io tasks can be written with a single
 * call to the underlying netcdf library.  This may involve an all to
 * all rearrangement in the mapping, but should minimize data movement
 * in lower level libraries
 *
 * @param ios pointer to the iosystem_desc_t struct
 * @param maplen the length of the map
 * @param compmap
 * @param gsize pointer to an array of sizes
 * @param ndims the number of dimensions
 * @param iodesc a pointer to the io_desc_t struct.
 * @returns 0 on success, error code otherwise.
 */
int box_rearrange_create(iosystem_desc_t *ios, int maplen, const PIO_Offset *compmap,
                         const int *gsize, int ndims, io_desc_t *iodesc)
{
    int nprocs = ios->num_comptasks;
    int nioprocs = ios->num_iotasks;
    PIO_Offset gstride[ndims];
    PIO_Offset start[ndims], count[ndims];
    int  tsize;
    int dest_ioproc[maplen];
    PIO_Offset dest_ioindex[maplen];
    int sndlths[nprocs];
    int sdispls[nprocs];
    int recvlths[nprocs];
    int rdispls[nprocs];
    MPI_Datatype dtypes[nprocs];
    PIO_Offset iomaplen[nioprocs];
    int mpierr; /* Return code from MPI functions. */
    int ret;

    /* Check inputs. */
    pioassert(ios && maplen >= 0 && compmap && gsize && ndims > 0 && iodesc,
              "invalid input", __FILE__, __LINE__);

    LOG((1, "box_rearrange_create maplen = %d ndims = %d", maplen, ndims));

    iodesc->rearranger = PIO_REARR_BOX;

    iodesc->ndof = maplen;
    gstride[ndims - 1] = 1;
    for (int i = ndims - 2; i >= 0; i--)
        gstride[i] = gstride[i + 1] * gsize[i + 1];

    if ((mpierr = MPI_Type_size(MPI_OFFSET, &tsize)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    for (int i = 0; i < maplen; i++)
    {
        dest_ioproc[i] = -1;
        dest_ioindex[i] = -1;
    }
    for (int i = 0; i < nprocs; i++)
    {
        sndlths[i] = 0;
        sdispls[i] = 0;
        recvlths[i] = 0;
        rdispls[i] = 0;
        dtypes[i] = MPI_OFFSET;
    }
    iodesc->llen = 0;
    if (ios->ioproc)
    {
        for (int i = 0; i < nprocs; i++)
            sndlths[i] = 1;

        /* llen here is the number that will be read on each io task */
        iodesc->llen = 1;
        for (int i = 0; i < ndims; i++)
            iodesc->llen *= iodesc->firstregion->count[i];
    }

    /* Determine whether fill values will be needed. */
    if ((ret = determine_fill(ios, iodesc, gsize, compmap)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    /*
      if (ios->ioproc){
      for (i = 0; i<ndims; i++){
      printf("%d %d %d ",i,iodesc->firstregion->start[i],iodesc->firstregion->count[i]);
      }
      printf("\n%s %d\n",__FILE__,__LINE__);
      }
    */

    for (int i = 0; i < nioprocs; i++)
    {
        int io_comprank = ios->ioranks[i];
        recvlths[io_comprank] = 1;
        rdispls[io_comprank] = i * tsize;
    }

    /*  The length of each iomap
        iomaplen = calloc(nioprocs, sizeof(PIO_Offset)); */
    if ((ret = pio_swapm(&(iodesc->llen), sndlths, sdispls, dtypes,
                         iomaplen, recvlths, rdispls, dtypes,
                         ios->union_comm,
                         iodesc->rearr_opts.comm_fc_opts_io2comp.enable_hs,
                         iodesc->rearr_opts.comm_fc_opts_io2comp.enable_isend,
                         iodesc->rearr_opts.comm_fc_opts_io2comp.max_pend_req)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    for (int i = 0; i < nioprocs; i++)
    {

        if (iomaplen[i] > 0)
        {
            int io_comprank = ios->ioranks[i];
            for (int j = 0; j < nprocs; j++)
            {
                sndlths[j] = 0;
                sdispls[j] = 0;
                rdispls[j] = 0;
                recvlths[j] = 0;
                if (ios->union_rank == io_comprank)
                    sndlths[j] = ndims;
            }
            recvlths[io_comprank] = ndims;

            /* The count from iotask i is sent to all compute tasks */
            if ((ret = pio_swapm(iodesc->firstregion->count,  sndlths, sdispls, dtypes,
                                 count, recvlths, rdispls, dtypes, ios->union_comm,
                                 iodesc->rearr_opts.comm_fc_opts_io2comp.enable_hs,
                                 iodesc->rearr_opts.comm_fc_opts_io2comp.enable_isend,
                                 iodesc->rearr_opts.comm_fc_opts_io2comp.max_pend_req)))
                return pio_err(ios, NULL, ret, __FILE__, __LINE__);                

            /* The start from iotask i is sent to all compute tasks. */
            if ((ret = pio_swapm(iodesc->firstregion->start,  sndlths, sdispls, dtypes,
                                 start, recvlths, rdispls, dtypes, ios->union_comm,
                                 iodesc->rearr_opts.comm_fc_opts_io2comp.enable_hs,
                                 iodesc->rearr_opts.comm_fc_opts_io2comp.enable_isend,
                                 iodesc->rearr_opts.comm_fc_opts_io2comp.max_pend_req)))
                return pio_err(ios, NULL, ret, __FILE__, __LINE__);

            for (int k = 0; k < maplen; k++)
            {
                PIO_Offset gcoord[ndims], lcoord[ndims];
                bool found = true;
                /* The compmap array is 1 based but calculations are 0 based */
                idx_to_dim_list(ndims, gsize, compmap[k] - 1, gcoord);

                for (int j = 0; j < ndims; j++)
                {
                    if (gcoord[j] >= start[j] && gcoord[j] < start[j] + count[j])
                    {
                        lcoord[j] = gcoord[j] - start[j];
                    }
                    else
                    {
                        found = false;
                        break;
                    }
                }
                if (found)
                {
                    dest_ioindex[k] = coord_to_lindex(ndims, lcoord, count);
                    dest_ioproc[k] = i;
                }
            }
        }
    }

    /* Check that a destination is found for each compmap entry. */
    for (int k = 0; k < maplen; k++)
        if (dest_ioproc[k] < 0 && compmap[k] > 0)
            return pio_err(ios, NULL, PIO_EINVAL, __FILE__, __LINE__);

    /* Completes the mapping for the box rearranger. */
    if ((ret = compute_counts(ios, iodesc, maplen, dest_ioproc, dest_ioindex,
                              ios->union_comm)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    /* Compute the max io buffer size needed for an iodesc. */
    if (ios->ioproc)
        if ((ret = compute_maxIObuffersize(ios->io_comm, iodesc)))
            return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    /* Using maxiobuflen compute the maximum number of vars of this type that the io
       task buffer can handle. */
    if ((ret = compute_maxaggregate_bytes(ios, iodesc)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

#ifdef DEBUG
    iodesc_dump(iodesc);
#endif
    return PIO_NOERR;
}

/**
 * Compare offsets is used by the sort in the subset rearrange. This
 * function is passed to qsort.
 *
 * @param a pointer to an offset.
 * @param b pointer to another offset.
 * @returns 0 if offsets are the same or either pointer is NULL.
 */
int compare_offsets(const void *a, const void *b)
{
    mapsort *x = (mapsort *)a;
    mapsort *y = (mapsort *)b;
    if (!x || !y)
        return 0;
    return (int)(x->iomap - y->iomap);
}

/**
 * Each region is a block of output which can be represented in a
 * single call to the underlying netcdf library.  This can be as small
 * as a single data point, but we hope we've aggragated better than
 * that.
 *
 * @param ndims the number of dimensions
 * @param gdimlen an array length ndims with the sizes of the global
 * dimensions.
 * @param maplen the length of the map
 * @param map may be NULL (when ???).
 * @param maxregions
 * @param firstregion pointer to the first region.
 * @returns 0 on success, error code otherwise.
 */
void get_start_and_count_regions(int ndims, const int *gdimlen, int maplen, const PIO_Offset *map,
                                 int *maxregions, io_region *firstregion)
{
    int nmaplen;
    int regionlen;
    io_region *region;

    /* Check inputs. */
    pioassert(ndims >= 0 && gdimlen && maplen >= 0 && maxregions && firstregion,
              "invalid input", __FILE__, __LINE__);

    nmaplen = 0;
    region = firstregion;
    if (map)
    {
        while (map[nmaplen++] <= 0)
            ;
        nmaplen--;
    }
    region->loffset = nmaplen;

    *maxregions = 1;

    while (nmaplen < maplen)
    {
        /* Here we find the largest region from the current offset
           into the iomap regionlen is the size of that region and we
           step to that point in the map array until we reach the
           end */
        for (int i = 0; i < ndims; i++)
            region->count[i] = 1;

        regionlen = find_region(ndims, gdimlen, maplen-nmaplen,
                                &map[nmaplen], region->start, region->count);

        pioassert(region->start[0] >= 0, "failed to find region", __FILE__, __LINE__);

        nmaplen = nmaplen + regionlen;

        if (region->next == NULL && nmaplen < maplen)
        {
            region->next = alloc_region(ndims);
            /* The offset into the local array buffer is the sum of
             * the sizes of all of the previous regions (loffset) */
            region = region->next;
            region->loffset = nmaplen;

            /* The calls to the io library are collective and so we
               must have the same number of regions on each io task
               maxregions will be the total number of regions on this
               task. */
            (*maxregions)++;
        }
    }
}

/**
 * The subset rearranger needs a mapping from compute tasks to IO
 * task, the only requirement is that each compute task map to one and
 * only one IO task.  This mapping groups by mpi task id others are
 * possible and may be better for certain decompositions
 *
 * @param ios pointer to the iosystem_desc_t struct
 * @param iodesc a pointer to the io_desc_t struct.
 * @returns 0 on success, error code otherwise.
 */
int default_subset_partition(iosystem_desc_t *ios, io_desc_t *iodesc)
{
    int taskratio = ios->num_comptasks / ios->num_iotasks;
    int color;
    int key;
    int mpierr; /* Return value from MPI functions. */

    pioassert(ios && iodesc, "invalid input", __FILE__, __LINE__);

    /* Create a new comm for each subset group with the io task in
       rank 0 and only 1 io task per group */
    if (ios->ioproc)
    {
        key = 0;
        color= ios->io_rank;
    }
    else
    {
        key = max(1, ios->comp_rank % taskratio + 1);
        color = min(ios->num_iotasks - 1, ios->comp_rank / taskratio);
    }

    if ((mpierr = MPI_Comm_split(ios->comp_comm, color, key, &iodesc->subset_comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    return PIO_NOERR;
}

/**
 * The subset rearranger computes a mapping between IO tasks and
 * compute tasks such that each compute task communicates with one and
 * only one IO task.
 *
 * @param ios pointer to the iosystem_desc_t struct.
 * @param maplen the length of the map.
 * @param compmap
 * @param gsize pointer to an array of sizes.
 * @param ndims the number of dimensions.
 * @param iodesc a pointer to the io_desc_t struct.
 * @returns 0 on success, error code otherwise.
 */
int subset_rearrange_create(iosystem_desc_t *ios, int maplen, PIO_Offset *compmap,
                            const int *gsize, int ndims, io_desc_t *iodesc)
{
    int i, j;
    PIO_Offset *iomap = NULL;
    int ierr = PIO_NOERR;
    mapsort *map = NULL;
    PIO_Offset totalgridsize;
    PIO_Offset *srcindex = NULL;
    PIO_Offset *myfillgrid = NULL;
    int maxregions;
    int rank, ntasks, rcnt;
    int mpierr; /* Return call from MPI function calls. */
    int ret;

    /* Check inputs. */
    pioassert(ios && compmap && gsize && iodesc, "invalid input",
              __FILE__, __LINE__);

    LOG((2, "subset_rearrange_create maplen = %d ndims = %d", maplen, ndims));

    /* subset partitions each have exactly 1 io task which is task 0
     * of that subset_comm */
    /* TODO: introduce a mechanism for users to define partitions */
    if ((ret = default_subset_partition(ios, iodesc)))
            return pio_err(ios, NULL, ret, __FILE__, __LINE__);
    iodesc->rearranger = PIO_REARR_SUBSET;

    /* Get size of this subset communicator, and rank in it. */
    if ((mpierr = MPI_Comm_rank(iodesc->subset_comm, &rank)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);
    if ((mpierr = MPI_Comm_size(iodesc->subset_comm, &ntasks)))
        return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);

    /* Check rank for correctness. */
    if (ios->ioproc)
        pioassert(rank == 0, "Bad io rank in subset create", __FILE__, __LINE__);
    else
        pioassert(rank > 0 && rank < ntasks, "Bad comp rank in subset create",
                  __FILE__, __LINE__);

    rcnt = 0;
    iodesc->ndof = maplen;
    if (ios->ioproc)
    {
        /* Allocate space to hold count of data to be received in pio_swapm(). */
        if (!(iodesc->rcount = malloc(ntasks * sizeof(int))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

        rcnt = 1;
    }

    /* Allocate space to hold count of data to be sent in pio_swapm(). */
    if (!(iodesc->scount = malloc(sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    iodesc->scount[0] = 0;
    totalgridsize = 1;
    for (i = 0; i < ndims; i++)
        totalgridsize *= gsize[i];

    for (i = 0; i < maplen; i++)
    {
        /*  turns out this can be allowed in some cases
            pioassert(compmap[i]>=0 && compmap[i]<=totalgridsize, "Compmap value out of bounds",
            __FILE__,__LINE__); */
        if (compmap[i] > 0)
            (iodesc->scount[0])++;
    }

    /* Allocate an array for indicies on the computation tasks (the
     * send side when writing). */
    if (iodesc->scount[0] > 0)
        if (!(iodesc->sindex = calloc(iodesc->scount[0], sizeof(PIO_Offset))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    j = 0;
    for (i = 0; i < maplen; i++)
        if (compmap[i] > 0)
            iodesc->sindex[j++] = i;

    /* Pass the reduced maplen (without holes) from each compute task to its associated IO task
       printf("%s %d %ld\n",__FILE__,__LINE__,iodesc->scount); */
    if ((mpierr = MPI_Gather(iodesc->scount, 1, MPI_INT, iodesc->rcount, rcnt, MPI_INT,
                             0, iodesc->subset_comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    iodesc->llen = 0;

    int rdispls[ntasks];
    int recvlths[ntasks];

    if (ios->ioproc)
    {
        for (i = 0;i < ntasks; i++)
        {
            iodesc->llen += iodesc->rcount[i];
            rdispls[i] = 0;
            recvlths[i] = iodesc->rcount[i];
            if (i > 0)
                rdispls[i] = rdispls[i - 1] + iodesc->rcount[i - 1];
        }

        if (iodesc->llen > 0)
        {
            if (!(srcindex = calloc(iodesc->llen, sizeof(PIO_Offset))))
                return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

            for (i = 0; i < iodesc->llen; i++)
                srcindex[i] = 0;
        }
    }
    else
    {
        for (i = 0; i < ntasks; i++)
        {
            recvlths[i] = 0;
            rdispls[i] = 0;
        }
    }
    if ((ret = determine_fill(ios, iodesc, gsize, compmap)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    /* Pass the sindex from each compute task to its associated IO task. */
    if ((mpierr = MPI_Gatherv(iodesc->sindex, iodesc->scount[0], PIO_OFFSET,
                              srcindex, recvlths, rdispls, PIO_OFFSET, 0,
                              iodesc->subset_comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    if (ios->ioproc && iodesc->llen>0)
    {
        if (!(map = calloc(iodesc->llen, sizeof(mapsort))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

        if (!(iomap = calloc(iodesc->llen, sizeof(PIO_Offset))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
    }

    /* Now pass the compmap, skipping the holes. */
    PIO_Offset *shrtmap;
    if (maplen>iodesc->scount[0] && iodesc->scount[0] > 0)
    {
        if (!(shrtmap = calloc(iodesc->scount[0], sizeof(PIO_Offset))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

        j = 0;
        for (i = 0; i < maplen; i++)
            if (compmap[i] > 0)
                shrtmap[j++] = compmap[i];
    }
    else
    {
        shrtmap = compmap;
    }

    if ((mpierr = MPI_Gatherv(shrtmap, iodesc->scount[0], PIO_OFFSET, iomap, recvlths, rdispls,
                              PIO_OFFSET, 0, iodesc->subset_comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    if (shrtmap != compmap)
        free(shrtmap);

    if (ios->ioproc && iodesc->llen > 0)
    {
        int pos = 0;
        int k = 0;
        mapsort *mptr;
        for (i = 0; i < ntasks; i++)
        {
            for (j = 0; j < iodesc->rcount[i]; j++)
            {
                mptr = &map[k];
                mptr->rfrom = i;
                mptr->soffset = srcindex[pos + j];
                mptr->iomap = iomap[pos + j];
                k++;
            }
            pos += iodesc->rcount[i];
        }
        /* sort the mapping, this will transpose the data into IO order */
        qsort(map, iodesc->llen, sizeof(mapsort), compare_offsets);

        if (!(iodesc->rindex = calloc(1, iodesc->llen * sizeof(PIO_Offset))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

        if (!(iodesc->rfrom = calloc(1, iodesc->llen * sizeof(int))))
            return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
    }

    int cnt[ntasks];
    for (i = 0; i < ntasks; i++)
    {
        cnt[i] = rdispls[i];

        /* offsets to swapm are in bytes */
        /*    rdispls[i]*=pio_offset_size; */
    }

    mapsort *mptr;
    for (i = 0; i < iodesc->llen; i++)
    {
        mptr = map+i;
        iodesc->rfrom[i] = mptr->rfrom;
        iodesc->rindex[i] = i;
        iomap[i] = mptr->iomap;
        srcindex[(cnt[iodesc->rfrom[i]])++] = mptr->soffset;
    }

    if (ios->ioproc && iodesc->needsfill)
    {
        /* we need the list of offsets which are not in the union of iomap */
        PIO_Offset thisgridsize[ios->num_iotasks];
        PIO_Offset thisgridmin[ios->num_iotasks], thisgridmax[ios->num_iotasks];
        int nio;
        PIO_Offset *myusegrid = NULL;
        int gcnt[ios->num_iotasks];
        int displs[ios->num_iotasks];

        thisgridmin[0] = 1;
        thisgridsize[0] =  totalgridsize / ios->num_iotasks;
        thisgridmax[0] = thisgridsize[0];
        int xtra = totalgridsize - thisgridsize[0] * ios->num_iotasks;

        for (nio = 0; nio < ios->num_iotasks; nio++)
        {
            int cnt = 0;
            int imin = 0;
            if (nio > 0)
            {
                thisgridsize[nio] =  totalgridsize / ios->num_iotasks;
                if (nio >= ios->num_iotasks - xtra)
                    thisgridsize[nio]++;
                thisgridmin[nio] = thisgridmax[nio - 1] + 1;
                thisgridmax[nio]= thisgridmin[nio] + thisgridsize[nio] - 1;
            }
            for (int i = 0; i < iodesc->llen; i++)
            {
                if (iomap[i] >= thisgridmin[nio] && iomap[i] <= thisgridmax[nio])
                {
                    cnt++;
                    if (cnt == 1)
                        imin = i;
                }
            }

            if ((mpierr = MPI_Gather(&cnt, 1, MPI_INT, gcnt, 1, MPI_INT, nio, ios->io_comm)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);

            if (nio == ios->io_rank)
            {
                displs[0] = 0;
                for (i = 1; i < ios->num_iotasks; i++)
                    displs[i] = displs[i - 1] + gcnt[i - 1];

                /* Allocate storage for the grid. */
                if (!(myusegrid = malloc(thisgridsize[nio] * sizeof(PIO_Offset))))
                    return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

                /* Initialize the grid to all -1. */
                for (i = 0; i < thisgridsize[nio]; i++)
                    myusegrid[i] = -1;
            }

            if ((mpierr = MPI_Gatherv(&iomap[imin], cnt, PIO_OFFSET, myusegrid, gcnt,
                                      displs, PIO_OFFSET, nio, ios->io_comm)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        }

        PIO_Offset grid[thisgridsize[ios->io_rank]];
        for (i = 0; i < thisgridsize[ios->io_rank]; i++)
            grid[i] = 0;

        int cnt = 0;
        for (i = 0; i < thisgridsize[ios->io_rank]; i++)
        {
            int j = myusegrid[i] - thisgridmin[ios->io_rank];
            pioassert(j < thisgridsize[ios->io_rank], "out of bounds array index", __FILE__, __LINE__);
            if (j >= 0)
            {
                grid[j] = 1;
                cnt++;
            }
        }
        if (myusegrid)
            free(myusegrid);

        iodesc->holegridsize=thisgridsize[ios->io_rank] - cnt;
        if (iodesc->holegridsize > 0)
        {
            /* Allocate space for the fillgrid. */
            if (!(myfillgrid = malloc(iodesc->holegridsize * sizeof(PIO_Offset))))
                return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
        }

        /* Initialize the fillgrid. */
        for (i = 0; i < iodesc->holegridsize; i++)
            myfillgrid[i] = -1;

        j = 0;
        for (i = 0; i < thisgridsize[ios->io_rank]; i++)
        {
            if (grid[i] == 0)
            {
                if (myfillgrid[j] == -1)
                    myfillgrid[j++]=thisgridmin[ios->io_rank] + i;
                else
                    return pio_err(ios, NULL, PIO_EINVAL, __FILE__, __LINE__);
            }
        }
        maxregions = 0;
        iodesc->maxfillregions = 0;
        if (myfillgrid)
        {
            iodesc->fillregion = alloc_region(iodesc->ndims);
            get_start_and_count_regions(iodesc->ndims, gsize, iodesc->holegridsize, myfillgrid,
                                        &iodesc->maxfillregions, iodesc->fillregion);
            free(myfillgrid);
            maxregions = iodesc->maxfillregions;
        }
        if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &maxregions, 1, MPI_INT, MPI_MAX, ios->io_comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);

        iodesc->maxfillregions = maxregions;

	iodesc->maxholegridsize = iodesc->holegridsize;
        if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &(iodesc->maxholegridsize), 1, MPI_INT, MPI_MAX, ios->io_comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    }

    if ((mpierr = MPI_Scatterv((void *)srcindex, recvlths, rdispls, PIO_OFFSET, (void *)iodesc->sindex,
                               iodesc->scount[0],  PIO_OFFSET, 0, iodesc->subset_comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    if (ios->ioproc)
    {
        iodesc->maxregions = 0;
        get_start_and_count_regions(iodesc->ndims,gsize,iodesc->llen, iomap,&(iodesc->maxregions),
                                    iodesc->firstregion);
        maxregions = iodesc->maxregions;
        if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &maxregions, 1, MPI_INT, MPI_MAX, ios->io_comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        iodesc->maxregions = maxregions;
        if (iomap)
            free(iomap);

        if (map)
            free(map);

        if (srcindex)
            free(srcindex);

        /* Compute the max io buffer size needed for an iodesc. */
        if ((ret = compute_maxIObuffersize(ios->io_comm, iodesc)))
            return pio_err(ios, NULL, ret, __FILE__, __LINE__);

        iodesc->nrecvs = ntasks;
#ifdef DEBUG
        iodesc_dump(iodesc);
#endif
    }

    /* Using maxiobuflen compute the maximum number of vars of this type that the io
       task buffer can handle. */
    if ((ret = compute_maxaggregate_bytes(ios, iodesc)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    return ierr;
}

/**
 * Performance tuning rearranger.
 *
 * @param ios pointer to the iosystem description struct.
 * @param iodesc pointer to the IO description struct.
 * @returns 0 on success, error code otherwise.
 */
void performance_tune_rearranger(iosystem_desc_t *ios, io_desc_t *iodesc)
{
#ifdef TIMING
#ifdef PERFTUNE
    double *wall, usr[2], sys[2];
    void *cbuf, *ibuf;
    int tsize;
    int myrank;
    int mpierr; /* Return code for MPI calls. */

    assert(iodesc);

    if ((mpierr = MPI_Type_size(iodesc->basetype, &tsize)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    cbuf = NULL;
    ibuf = NULL;
    if (iodesc->ndof > 0)
        if (!(cbuf = bget(iodesc->ndof * tsize)))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

    if (iodesc->llen > 0)
        if (!(ibuf = bget(iodesc->llen * tsize)))
            return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);

    if (iodesc->rearranger == PIO_REARR_BOX)
        mycomm = ios->union_comm;
    else
        mycomm = iodesc->subset_comm;

    if ((mpierr = MPI_Comm_size(mycomm, &nprocs)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    if ((mpierr = MPI_Comm_rank(mycomm, &myrank)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    int log2 = log(nprocs) / log(2) + 1;
    if (!(wall = bget(2 * 4 * log2 * sizeof(double))))
        return pio_err(ios, file, PIO_ENOMEM, __FILE__, __LINE__);
    double mintime;
    int k = 0;

    if ((mpierr = MPI_Barrier(mycomm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    GPTLstamp(&wall[0], &usr[0], &sys[0]);
    rearrange_comp2io(ios, iodesc, cbuf, ibuf, 1);
    rearrange_io2comp(ios, iodesc, ibuf, cbuf);
    GPTLstamp(&wall[1], &usr[1], &sys[1]);
    mintime = wall[1]-wall[0];
    if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, &mintime, 1, MPI_DOUBLE, MPI_MAX, mycomm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    handshake = iodesc->rearr_opts.comm_fc_opts_comp2io.enable_hs;
    isend = iodesc->isend;
    maxreqs = iodesc->max_requests;

    for (int i = 0; i < 2; i++)
    {
        if (i == 0)
            iodesc->rearr_opts.comm_fc_opts_comp2io.enable_hs = false;
        else
            iodesc->rearr_opts.comm_fc_opts_comp2io.enable_hs = true;

        for (int j = 0; j < 2; j++)
        {
            if (j == 0)
                iodesc->isend = false;
            else
                iodesc->isend = true;

            iodesc->max_requests = 0;

            for (nreqs = nprocs; nreqs >= 2; nreqs /= 2)
            {
                iodesc->max_requests = nreqs;
                if ((mpierr = MPI_Barrier(mycomm)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                GPTLstamp(wall, usr, sys);
                rearrange_comp2io(ios, iodesc, cbuf, ibuf, 1);
                rearrange_io2comp(ios, iodesc, ibuf, cbuf);
                GPTLstamp(wall+1, usr, sys);
                wall[1] -= wall[0];
                if ((mpierr = MPI_Allreduce(MPI_IN_PLACE, wall + 1, 1, MPI_DOUBLE, MPI_MAX,
                                            mycomm)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);

                if (wall[1] < mintime * 0.95)
                {
                    handshake = iodesc->rearr_opts.comm_fc_opts_comp2io.enable_hs;
                    isend = iodesc->isend;
                    maxreqs = nreqs;
                    mintime = wall[1];
                }
                else if (wall[1] > mintime * 1.05)
                {
                    exit;
                }
            }
        }
    }

    iodesc->rearr_opts.comm_fc_opts_comp2io.enable_hs = handshake;
    iodesc->isend = isend;
    iodesc->max_requests = maxreqs;

    LOG((1, "spmd optimization: maxreqs: %d handshake:%d isend:%d mintime=%f\n",
         maxreqs,handshake,isend,mintime));

    /* Free memory. */
    brel(wall);
    brel(cbuf);
    brel(ibuf);
#endif
#endif
}
