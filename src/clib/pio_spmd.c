/** 
 * @file 
 * Algorithms modeled after spmd_utils in the Community
 * Atmosphere Model; C translation. This includes MPI_Gather,
 * MPI_Gatherv, and MPI_Alltoallw with flow control options.
 *
 * @author Jim Edwards
 * @date 2014
 */
#include <config.h>
#include <pio.h>
#include <pio_internal.h>

/**
 * Wrapper for MPI calls to print the Error string on error.
 *
 * @param ierr the error code to check.
 * @param file the code file where the error happened.
 * @param line the line of code (near) where the error happened.
 */
void CheckMPIReturn(const int ierr, const char *file, const int line)
{

    if (ierr != MPI_SUCCESS)
    {
        char errstring[MPI_MAX_ERROR_STRING];
        int errstrlen;
        int mpierr = MPI_Error_string(ierr, errstring, &errstrlen);

        fprintf(stderr, "MPI ERROR: %s in file %s at line %d\n", errstring, file,
                line);
    }
}


/**
 * Provides the functionality of MPI_Gather with flow control options.
 *
 * @param sendbuf starting address of send buffer.
 * @param sendcnt number of elements in send buffer.
 * @param sendtype data type of send buffer elements.
 * @param recvbuf address of receive buffer.
 * @param recvcnt number of elements for any single receive.
 * @param recvtype data type of recv buffer elements (significant only
 * at root).
 * @param root rank of receiving process.
 * @param comm communicator.
 * @param flow_cntl if non-zero, flow control will be used, and the
 * block size will be the min of flow_cntl and MAX_GATHER_BLOCK_SIZE.
 * @returns 0 for success, error code otherwise.
 */
int pio_fc_gather(void *sendbuf, const int sendcnt, const MPI_Datatype sendtype,
                  void *recvbuf, const int recvcnt, const MPI_Datatype recvtype,
                  const int root, const MPI_Comm comm, const int flow_cntl)
{
    int gather_block_size; /* Block size used for flow control. */
    int mytask, nprocs;    /* Task rank and number of tasks. */
    int mtag;
    MPI_Status status;
    int hs = 1;   /* Used for handshaking between root and other tasks. */
    int displs; /* Displacement within receive array. */
    int dsize; /* Size of the receive type. */
    int ierr; /* Return code. */

    LOG((2, "pio_fc_gather sendcnt = %d sendtype = %d recvcnt = %d recvtype = %d "
         "root = %d flow_cntl = %d", sendcnt, sendtype, recvcnt, recvtype, root, flow_cntl));

    /* If using flow control, determine the block size. */
    if (flow_cntl > 0)
    {
        /* Determine the block size. */
        gather_block_size = min(flow_cntl, MAX_GATHER_BLOCK_SIZE);
        
        /* Find rank and the number of tasks. */
        CheckMPIReturn(MPI_Comm_rank(comm, &mytask), __FILE__, __LINE__);
        CheckMPIReturn(MPI_Comm_size(comm, &nprocs), __FILE__, __LINE__);

        mtag = 2 * nprocs;

        if (mytask == root)
        {
            /* Only do this on the root task. */
            int preposts = min(nprocs - 1, gather_block_size);
            int head = 0;
            int count = 0;
            int tail = 0;
            MPI_Request rcvid[gather_block_size];

            /* Find the size of the receive type. */
            CheckMPIReturn(MPI_Type_size(recvtype, &dsize), __FILE__, __LINE__);

            /* Receive from all non-root tasks. */
            for (int p = 0; p < nprocs; p++)
                if (p != root)
                    if (recvcnt > 0)
                    {
                        count++;
                        if (count > preposts)
                        {
                            CheckMPIReturn(MPI_Wait(rcvid + tail, &status), __FILE__, __LINE__);
                            tail = (tail + 1) % preposts;
                        }

                        /* Determine the pointer to the correct part of the receive array. */
                        displs = p * recvcnt * dsize;
                        char *ptr = (char *)recvbuf + displs;

                        /* Receive */
                        CheckMPIReturn(MPI_Irecv(ptr, recvcnt, recvtype, p, mtag, comm, rcvid + head),
                                       __FILE__, __LINE__);

                        /* ??? */
                        head = (head + 1) % preposts;

                        /* Send handshaking. */
                        CheckMPIReturn(MPI_Send(&hs, 1, MPI_INT, p, mtag, comm), __FILE__, __LINE__);
                    }

            /* Get the size of the send type. */
            CheckMPIReturn(MPI_Type_size(sendtype, &dsize), __FILE__, __LINE__);

            /* Copy local data. (Seems like this disregards any
             * difference in send and receive types ???) */
            memcpy(recvbuf, sendbuf, sendcnt * dsize );

            count = min(count, preposts);

            if (count > 0)
                CheckMPIReturn(MPI_Waitall(count, rcvid, MPI_STATUSES_IGNORE), __FILE__, __LINE__);
        }
        else
        {
            /* Do this on all non-root tasks. */
            if (sendcnt > 0)
            {
                /* Receive handshaking. */
                CheckMPIReturn(MPI_Recv(&hs, 1, MPI_INT, root, mtag, comm, &status),
                               __FILE__, __LINE__);

                /* Perform blocking send to root with data. */
                CheckMPIReturn(MPI_Send(sendbuf, sendcnt, sendtype, root, mtag, comm),
                               __FILE__, __LINE__);
            }
        }
    }
    else
    {
        /* No flow control is required, so just call MPI_Gather. */
        CheckMPIReturn(MPI_Gather(sendbuf, sendcnt, sendtype, recvbuf, recvcnt, recvtype,
                                  root, comm), __FILE__, __LINE__);
    }

    return PIO_NOERR;
}

/**
 * Provides the functionality of MPI_Gatherv with flow control options.
 *
 * @param sendbuf starting address of send buffer.
 * @param sendcnt number of elements in send buffer.
 * @param sendtype data type of send buffer elements.
 * @param recvbuf address of receive buffer.
 * @param recvcnts integer array (of length group size) containing the
 * number of elements that are received from each process (significant
 * only at root).
 * @param displs integer array (of length group size). Entry i
 * specifies the displacement relative to recvbuf at which to place
 * the incoming data from process i (significant only at root).
 * @param recvtype data type of recv buffer elements (significant only
 * at root).
 * @param root rank of receiving process.
 * @param comm communicator.
 * @param flow_cntl if non-zero, flow control will be used.
 * @returns 0 for success, error code otherwise.
 */
int pio_fc_gatherv(void *sendbuf, const int sendcnt, const MPI_Datatype sendtype,
                   void *recvbuf, const int *recvcnts, const int *displs,
                   const MPI_Datatype recvtype, const int root,
                   const MPI_Comm comm, const int flow_cntl)
{
    bool fc_gather;
    int gather_block_size;
    int mytask, nprocs;
    int mtag;
    MPI_Status status;
    int ierr;
    int hs;
    int dsize;

    if (flow_cntl > 0)
    {
        fc_gather = true;
        gather_block_size = min(flow_cntl, MAX_GATHER_BLOCK_SIZE);
    }
    else
    {
        fc_gather = false;
    }

    if (fc_gather)
    {
        CheckMPIReturn(MPI_Comm_rank(comm, &mytask), __FILE__, __LINE__);
        CheckMPIReturn(MPI_Comm_size(comm, &nprocs), __FILE__, __LINE__);

        mtag = 2 * nprocs;
        hs = 1;

        if (mytask == root)
        {
            int preposts = min(nprocs-1, gather_block_size);
            int head = 0;
            int count = 0;
            int tail = 0;
            MPI_Request rcvid[gather_block_size];

            CheckMPIReturn(MPI_Type_size(recvtype, &dsize), __FILE__, __LINE__);

            for (int p = 0; p < nprocs; p++)
            {
                if (p != root)
                {
                    if (recvcnts[p] > 0)
                    {
                        count++;
                        if (count > preposts)
                        {
                            CheckMPIReturn(MPI_Wait(rcvid+tail, &status), __FILE__, __LINE__);
                            tail = (tail + 1) % preposts;
                        }

                        void *ptr = (void *)((char *)recvbuf + dsize * displs[p]);

                        CheckMPIReturn(MPI_Irecv(ptr, recvcnts[p], recvtype, p, mtag, comm, rcvid + head),
                                       __FILE__,__LINE__);
                        head = (head + 1) % preposts;
                        CheckMPIReturn(MPI_Send(&hs, 1, MPI_INT, p, mtag, comm), __FILE__, __LINE__);
                    }
                }
            }

            /* copy local data */
            CheckMPIReturn(MPI_Type_size(sendtype, &dsize), __FILE__, __LINE__);
            CheckMPIReturn(MPI_Sendrecv(sendbuf, sendcnt, sendtype,
                                        mytask, 102, recvbuf, recvcnts[mytask], recvtype,
                                        mytask, 102, comm, &status), __FILE__, __LINE__);

            count = min(count, preposts);
            if (count > 0)
                CheckMPIReturn(MPI_Waitall(count, rcvid, MPI_STATUSES_IGNORE), __FILE__, __LINE__);
        }
        else
        {
            if (sendcnt > 0)
            {
                CheckMPIReturn(MPI_Recv(&hs, 1, MPI_INT, root, mtag, comm, &status), __FILE__, __LINE__);
                CheckMPIReturn(MPI_Send(sendbuf, sendcnt, sendtype, root, mtag, comm), __FILE__, __LINE__);
            }
        }
    }
    else
    {
        CheckMPIReturn(MPI_Gatherv(sendbuf, sendcnt, sendtype, recvbuf, recvcnts,
                                   displs, recvtype, root, comm), __FILE__, __LINE__);
    }

    return PIO_NOERR;
}

/**
 * Returns the smallest power of 2 greater than i.
 *
 * @param i input number
 * @returns the smallest power of 2 greater than i.
 */
int ceil2(const int i)
{
    int p = 1;
    while (p < i)
        p *= 2;

    return(p);
}

/**
 * Given integers p and k between 0 and np-1,
 * if (p+1)^k <= np-1 then return (p+1)^k else -1.
 *
 * @param np
 * @param p integer between 0 and np - 1.
 * @param k integer between 0 and np - 1.
 * @returns (p + 1) ^ k else -1.
 */
int pair(const int np, const int p, const int k)
{
    int q = (p + 1) ^ k ;
    int pair = (q > np - 1) ? -1 : q;
    return pair;
}

/**
 * Provides the functionality of MPI_Alltoallw with flow control
 * options. Generalized all-to-all communication allowing different
 * datatypes, counts, and dis‐ placements for each partner
 *
 * @param sndbuf starting address of send buffer
 * @param sndlths integer array equal to the group size specifying the
 * number of elements to send to each processor
 * @param sdispls integer array (of length group size). Entry j
 * specifies the displacement in bytes (relative to sendbuf) from
 * which to take the outgoing data destined for process j
 * @param stypes array of datatypes (of length group size). Entry j
 * specifies the type of data to send to process j
 * @param rcvbuf address of receive buffer
 * @param rcvlths integer array equal to the group size specifying the
 * number of elements that can be received from each processor
 * @param rdispls integer array (of length group size). Entry i
 * specifies the displacement in bytes (relative to recvbuf) at which
 * to place the incoming data from process i
 * @param rtypes array of datatypes (of length group size). Entry i
 * specifies the type of data received from process i
 * @param comm MPI communicator for the MPI_Alltoallw call.
 * @param handshake
 * @param isend
 * @param max_requests
 * @returns 0 for success, error code otherwise.
 */
int pio_swapm(void *sndbuf, int *sndlths, int *sdispls, MPI_Datatype *stypes,
              void *rcvbuf, int *rcvlths, int *rdispls, MPI_Datatype *rtypes,
              MPI_Comm comm, const bool handshake, bool isend, const int max_requests)
{
    int nprocs;
    int mytask;
    int maxsend = 0;
    int maxrecv = 0;

    CheckMPIReturn(MPI_Comm_size(comm, &nprocs),__FILE__, __LINE__);
    CheckMPIReturn(MPI_Comm_rank(comm, &mytask),__FILE__, __LINE__);

    /* If max_requests == 0 no throttling is requested and the default
     * mpi_alltoallw function is used. */
    if (max_requests == 0)
    {
#ifdef DEBUG
        int totalrecv = 0;
        int totalsend = 0;
        for (int i = 0; i < nprocs; i++)
        {
            totalsend += sndlths[i];
            totalrecv += rcvlths[i];
        }
        printf("%s %d totalsend %d totalrecv %d \n", __FILE__, __LINE__, totalsend,
               totalrecv);
#endif
#ifdef OPEN_MPI
        for (int i = 0; i < nprocs; i++)
        {
            if (stypes[i] == MPI_DATATYPE_NULL)
                stypes[i] = MPI_CHAR;
            if (rtypes[i] == MPI_DATATYPE_NULL)
                rtypes[i] = MPI_CHAR;
        }
#endif
        CheckMPIReturn(MPI_Alltoallw(sndbuf, sndlths, sdispls, stypes, rcvbuf,
                                     rcvlths, rdispls, rtypes, comm), __FILE__, __LINE__);

#ifdef OPEN_MPI
        for (int i = 0; i < nprocs; i++)
        {
            if (stypes[i] == MPI_CHAR)
                stypes[i] = MPI_DATATYPE_NULL;
            if (rtypes[i] == MPI_CHAR)
                rtypes[i] = MPI_DATATYPE_NULL;
        }
#endif
        return PIO_NOERR;
    }

    int tag;
    int offset_t;
    int ierr;
    MPI_Status status;
    int steps;
    int istep;
    int rstep;
    int p;
    int maxreq;
    int maxreqh;
    int hs;
    int cnt;
    void *ptr;
    MPI_Request rcvids[nprocs];

    offset_t = nprocs;
    /* send to self */
    if (sndlths[mytask] > 0)
    {
        void *sptr, *rptr;
        int extent, lb;
        tag = mytask + offset_t;
        sptr = (void *)((char *) sndbuf + sdispls[mytask]);
        rptr = (void *)((char *) rcvbuf + rdispls[mytask]);

        /*
          MPI_Type_get_extent(stypes[mytask], &lb, &extent);
          printf("%s %d %d %d\n",__FILE__,__LINE__,extent, lb);
          MPI_Type_get_extent(rtypes[mytask], &lb, &extent);
          printf("%s %d %d %d\n",__FILE__,__LINE__,extent, lb);
        */
#ifdef ONEWAY
        CheckMPIReturn(MPI_Sendrecv(sptr, sndlths[mytask],stypes[mytask],
                                    mytask, tag, rptr, rcvlths[mytask], rtypes[mytask],
                                    mytask, tag, comm, &status), __FILE__, __LINE__);
#else
        CheckMPIReturn(MPI_Irecv(rptr, rcvlths[mytask], rtypes[mytask],
                                 mytask, tag, comm, rcvids), __FILE__, __LINE__);
        CheckMPIReturn(MPI_Send(sptr, sndlths[mytask], stypes[mytask],
                                mytask, tag, comm), __FILE__, __LINE__);

        CheckMPIReturn(MPI_Wait(rcvids, &status), __FILE__, __LINE__);
#endif
    }

    if (nprocs == 1)
        return PIO_NOERR;

    int swapids[nprocs];
    MPI_Request sndids[nprocs];
    MPI_Request hs_rcvids[nprocs];

    for (int i = 0; i < nprocs; i++)
    {
        rcvids[i] = MPI_REQUEST_NULL;
        swapids[i] = 0;
    }

    if (isend)
        for (int i = 0; i < nprocs; i++)
            sndids[i] = MPI_REQUEST_NULL;

    if (handshake)
        for (int i = 0; i < nprocs; i++)
            hs_rcvids[i] = MPI_REQUEST_NULL;

    steps = 0;
    for (istep = 0; istep < ceil2(nprocs) - 1; istep++)
    {
        p = pair(nprocs, istep, mytask);
        if (p >= 0 && (sndlths[p] > 0 || rcvlths[p] > 0))
            swapids[steps++] = p;
    }

    if (steps == 1)
    {
        maxreq = 1;
        maxreqh = 1;
    }
    else
    {
        if (max_requests > 1 && max_requests < steps)
        {
            maxreq = max_requests;
            maxreqh = maxreq / 2;
        }
        else if (max_requests >= steps)
        {
            maxreq = steps;
            maxreqh = steps;
        }
        else
        {
            maxreq = 2;
            maxreqh = 1;
        }
    }

    /* If handshaking is in use, do a nonblocking recieve to listen
     * for it. */
    if (handshake)
    {
        hs = 1;
        for (istep = 0; istep < maxreq; istep++)
        {
            p = swapids[istep];
            if (sndlths[p] > 0)
            {
                tag = mytask + offset_t;
                CheckMPIReturn(MPI_Irecv(&hs, 1, MPI_INT, p, tag, comm, hs_rcvids + istep),
                               __FILE__, __LINE__);
            }
        }
    }

    for (istep = 0; istep < maxreq; istep++)
    {
        p = swapids[istep];
        if (rcvlths[p] > 0)
        {
            tag = p + offset_t;
            ptr = (void *)((char *)rcvbuf + rdispls[p]);

            CheckMPIReturn(MPI_Irecv(ptr, rcvlths[p], rtypes[p], p, tag, comm, rcvids + istep),
                           __FILE__, __LINE__);

            if (handshake)
                CheckMPIReturn(MPI_Send(&hs, 1, MPI_INT, p, tag, comm), __FILE__, __LINE__);
        }
    }

    /* ??? */
    rstep = maxreq;
    for (istep = 0; istep < steps; istep++)
    {
        p = swapids[istep];
        if (sndlths[p] > 0)
        {
            tag = mytask + offset_t;
            if (handshake)
            {
                CheckMPIReturn(MPI_Wait(hs_rcvids + istep, &status), __FILE__, __LINE__);
                hs_rcvids[istep] = MPI_REQUEST_NULL;
            }
            ptr = (void *)((char *)sndbuf + sdispls[p]);

            if (isend)
                CheckMPIReturn(MPI_Irsend(ptr, sndlths[p], stypes[p], p, tag, comm, sndids + istep),
                               __FILE__, __LINE__);
            else
                CheckMPIReturn(MPI_Send(ptr, sndlths[p], stypes[p], p, tag, comm), __FILE__, __LINE__);
        }

        /* We did comms in sets of size max_reqs, if istep > maxreqh
         * then there is a remainder that must be handled. */
        if (istep > maxreqh)
        {
            p = istep - maxreqh;
            if (rcvids[p] != MPI_REQUEST_NULL)
            {
                CheckMPIReturn(MPI_Wait(rcvids+p, &status), __FILE__, __LINE__);
                rcvids[p] = MPI_REQUEST_NULL;
            }
            if (rstep < steps)
            {
                p = swapids[rstep];
                if (handshake && sndlths[p] > 0)
                {
                    tag = mytask + offset_t;
                    CheckMPIReturn(MPI_Irecv( &hs, 1, MPI_INT, p, tag, comm, hs_rcvids+rstep), __FILE__, __LINE__);
                }
                if (rcvlths[p] > 0)
                {
                    tag = p + offset_t;

                    ptr = (void *)((char *) rcvbuf + rdispls[p]);
                    CheckMPIReturn(MPI_Irecv( ptr, rcvlths[p], rtypes[p], p, tag, comm, rcvids+rstep),
                                   __FILE__, __LINE__);
                    if (handshake)
                        CheckMPIReturn(MPI_Send( &hs, 1, MPI_INT, p, tag, comm), __FILE__, __LINE__);
                }
                rstep++;
            }
        }
    }

    /* ??? */
    if (steps > 0)
    {
        CheckMPIReturn(MPI_Waitall(steps, rcvids, MPI_STATUSES_IGNORE), __FILE__, __LINE__);
        if (isend)
            CheckMPIReturn(MPI_Waitall(steps, sndids, MPI_STATUSES_IGNORE), __FILE__, __LINE__);
    }

    return PIO_NOERR;
}
