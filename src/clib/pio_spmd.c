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
 * datatypes, counts, and displacements for each partner
 *
 * @param sendbuf starting address of send buffer
 * @param sendcounts integer array equal to the number of tasks in
 * communicator comm (ntasks). It specifies the number of elements to
 * send to each processor
 * @param sdispls integer array (of length ntasks). Entry j
 * specifies the displacement in bytes (relative to sendbuf) from
 * which to take the outgoing data destined for process j.
 * @param sendtypes array of datatypes (of length ntasks). Entry j
 * specifies the type of data to send to process j.
 * @param recvbuf address of receive buffer.
 * @param recvcounts integer array (of length ntasks) specifying the
 * number of elements that can be received from each processor.
 * @param rdispls integer array (of length ntasks). Entry i
 * specifies the displacement in bytes (relative to recvbuf) at which
 * to place the incoming data from process i.
 * @param recvtypes array of datatypes (of length ntasks). Entry i
 * specifies the type of data received from process i.
 * @param comm MPI communicator for the MPI_Alltoallw call.
 * @param handshake if true, use handshaking.
 * @param isend the isend bool indicates whether sends should be
 * posted using mpi_irsend which can be faster than blocking
 * sends. When flow control is used max_requests > 0 and the number of
 * irecvs posted from a given task will not exceed this value. On some
 * networks too many outstanding irecvs will cause a communications
 * bottleneck.
 * @param max_requests If 0, no flow control is used.
 * @returns 0 for success, error code otherwise.
 */
int pio_swapm(void *sendbuf, int *sendcounts, int *sdispls, MPI_Datatype *sendtypes,
              void *recvbuf, int *recvcounts, int *rdispls, MPI_Datatype *recvtypes,
              MPI_Comm comm, const bool handshake, bool isend, const int max_requests)
{
    int ntasks;  /* Number of tasks in communicator comm. */
    int my_rank; /* Rank of this task in comm. */
    int maxsend = 0;
    int maxrecv = 0;
    int tag;
    int offset_t;
    int steps;
    int istep;
    int rstep;
    int p;
    int maxreq;
    int maxreqh;
    int hs = 1; /* Used for handshaking. */
    int cnt;
    void *ptr;
    MPI_Status status; /* Not actually used - replace with MPI_STATUSES_IGNORE. */
    int mpierr;  /* Return code from MPI functions. */
    int ierr;    /* Return value. */

    LOG((2, "pio_swapm handshake = %d isend = %d max_requests = %d", handshake,
         isend, max_requests));

    /* Get my rank and size of communicator. */
    if ((mpierr = MPI_Comm_size(comm, &ntasks)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    if ((mpierr = MPI_Comm_rank(comm, &my_rank)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    LOG((2, "ntasks = %d my_rank = %d", ntasks, my_rank));

    /* Now we know the size of these arrays. */
    int swapids[ntasks];
    MPI_Request rcvids[ntasks];
    MPI_Request sndids[ntasks];
    MPI_Request hs_rcvids[ntasks];

    /* Print some debugging info, if logging is enabled. */
#if PIO_ENABLE_LOGGING
    {
        for (int p = 0; p < ntasks; p++)
            LOG((3, "sendcounts[%d] = %d", p, sendcounts[p]));
        for (int p = 0; p < ntasks; p++)
            LOG((3, "sdispls[%d] = %d", p, sdispls[p]));
        for (int p = 0; p < ntasks; p++)
            LOG((3, "sendtypes[%d] = %d", p, sendtypes[p]));
        for (int p = 0; p < ntasks; p++)
            LOG((3, "recvcounts[%d] = %d", p, recvcounts[p]));
        for (int p = 0; p < ntasks; p++)
            LOG((3, "rdispls[%d] = %d", p, rdispls[p]));
        for (int p = 0; p < ntasks; p++)
            LOG((3, "recvtypes[%d] = %d", p, recvtypes[p]));
    }
#endif /* PIO_ENABLE_LOGGING */

    /* If max_requests == 0 no throttling is requested and the default
     * mpi_alltoallw function is used. */
    if (max_requests == 0)
    {
#ifdef OPEN_MPI
        /* OPEN_MPI developers determined that MPI_DATATYPE_NULL was
           not a valid argument to MPI_Alltoallw according to the
           standard. The standard is a little vague on this issue and
           other mpi vendors disagree. In my opinion it just makes
           sense that if an argument expects an mpi datatype then
           MPI_DATATYPE_NULL should be valid. For each task it's
           possible that either sendlength or receive length is 0 it
           is in this case that the datatype null makes sense. */
        for (int i = 0; i < ntasks; i++)
        {
            if (sendtypes[i] == MPI_DATATYPE_NULL)
                sendtypes[i] = MPI_CHAR;
            if (recvtypes[i] == MPI_DATATYPE_NULL)
                recvtypes[i] = MPI_CHAR;
        }
#endif

        /* Call the MPI alltoall without flow control. */
        LOG((3, "Calling MPI_Alltoallw without flow control."));
        if ((mpierr = MPI_Alltoallw(sendbuf, sendcounts, sdispls, sendtypes, recvbuf,
                                    recvcounts, rdispls, recvtypes, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);

#ifdef OPEN_MPI
        /* OPEN_MPI has problems with MPI_DATATYPE_NULL. */
        for (int i = 0; i < ntasks; i++)
        {
            if (sendtypes[i] == MPI_CHAR)
                sendtypes[i] = MPI_DATATYPE_NULL;
            if (recvtypes[i] == MPI_CHAR)
                recvtypes[i] = MPI_DATATYPE_NULL;
        }
#endif
        return PIO_NOERR;
    }

    /* an index for communications tags */
    offset_t = ntasks;

    /* Send to self. */
    if (sendcounts[my_rank] > 0)
    {
        void *sptr, *rptr;
        int extent, lb;
        tag = my_rank + offset_t;
        sptr = (char *)sendbuf + sdispls[my_rank];
        rptr = (char *)recvbuf + rdispls[my_rank];

        /*
          MPI_Type_get_extent(sendtypes[my_rank], &lb, &extent);
          printf("%s %d %d %d\n",__FILE__,__LINE__,extent, lb);
          MPI_Type_get_extent(recvtypes[my_rank], &lb, &extent);
          printf("%s %d %d %d\n",__FILE__,__LINE__,extent, lb);
        */

#ifdef ONEWAY
        /* If ONEWAY is true we will post mpi_sendrecv comms instead
         * of irecv/send. */
        if ((mpierr = MPI_Sendrecv(sptr, sendcounts[my_rank],sendtypes[my_rank],
                                   my_rank, tag, rptr, recvcounts[my_rank], recvtypes[my_rank],
                                   my_rank, tag, comm, &status)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
#else
        if ((mpierr = MPI_Irecv(rptr, recvcounts[my_rank], recvtypes[my_rank],
                                my_rank, tag, comm, rcvids)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        if ((mpierr = MPI_Send(sptr, sendcounts[my_rank], sendtypes[my_rank],
                               my_rank, tag, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);

        if ((mpierr = MPI_Wait(rcvids, &status)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
#endif
    }

    /* When send to self is complete there is nothing left to do if
     * ntasks==1. */
    if (ntasks == 1)
        return PIO_NOERR;

    for (int i = 0; i < ntasks; i++)
    {
        rcvids[i] = MPI_REQUEST_NULL;
        swapids[i] = 0;
    }

    if (isend)
        for (int i = 0; i < ntasks; i++)
            sndids[i] = MPI_REQUEST_NULL;

    if (handshake)
        for (int i = 0; i < ntasks; i++)
            hs_rcvids[i] = MPI_REQUEST_NULL;

    steps = 0;
    for (istep = 0; istep < ceil2(ntasks) - 1; istep++)
    {
        p = pair(ntasks, istep, my_rank);
        if (p >= 0 && (sendcounts[p] > 0 || recvcounts[p] > 0))
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
        for (istep = 0; istep < maxreq; istep++)
        {
            p = swapids[istep];
            if (sendcounts[p] > 0)
            {
                tag = my_rank + offset_t;
                if ((mpierr = MPI_Irecv(&hs, 1, MPI_INT, p, tag, comm, hs_rcvids + istep)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            }
        }
    }

    /* Post up to maxreq irecv's. */
    for (istep = 0; istep < maxreq; istep++)
    {
        p = swapids[istep];
        if (recvcounts[p] > 0)
        {
            tag = p + offset_t;
            ptr = (char *)recvbuf + rdispls[p];

            if ((mpierr = MPI_Irecv(ptr, recvcounts[p], recvtypes[p], p, tag, comm,
                                    rcvids + istep)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);

            if (handshake)
                if ((mpierr = MPI_Send(&hs, 1, MPI_INT, p, tag, comm)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        }
    }

    /* Tell the paired task that this tasks' has posted it's irecvs'. */
    rstep = maxreq;
    for (istep = 0; istep < steps; istep++)
    {
        p = swapids[istep];
        if (sendcounts[p] > 0)
        {
            tag = my_rank + offset_t;
            /* If handshake is enabled don't post sends until the
             * receiving task has posted recvs. */
            if (handshake)
            {
                if ((mpierr = MPI_Wait(hs_rcvids + istep, &status)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                hs_rcvids[istep] = MPI_REQUEST_NULL;
            }
            ptr = (char *)sendbuf + sdispls[p];

            if (isend)
                if ((mpierr = MPI_Irsend(ptr, sendcounts[p], sendtypes[p], p, tag, comm,
                                         sndids + istep)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            else
                if ((mpierr = MPI_Send(ptr, sendcounts[p], sendtypes[p], p, tag, comm)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        }

        /* We did comms in sets of size max_reqs, if istep > maxreqh
         * then there is a remainder that must be handled. */
        if (istep > maxreqh)
        {
            p = istep - maxreqh;
            if (rcvids[p] != MPI_REQUEST_NULL)
            {
                if ((mpierr = MPI_Wait(rcvids + p, &status)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                rcvids[p] = MPI_REQUEST_NULL;
            }
            if (rstep < steps)
            {
                p = swapids[rstep];
                if (handshake && sendcounts[p] > 0)
                {
                    tag = my_rank + offset_t;
                    if ((mpierr = MPI_Irecv(&hs, 1, MPI_INT, p, tag, comm, hs_rcvids+rstep)))
                        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                }
                if (recvcounts[p] > 0)
                {
                    tag = p + offset_t;

                    ptr = (char *)recvbuf + rdispls[p];
                    if ((mpierr = MPI_Irecv(ptr, recvcounts[p], recvtypes[p], p, tag, comm, rcvids + rstep)))
                        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                    if (handshake)
                        if ((mpierr = MPI_Send(&hs, 1, MPI_INT, p, tag, comm)))
                            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                }
                rstep++;
            }
        }
    }

    /* If steps > 0 there are still outstanding messages, wait for
     * them here. */
    if (steps > 0)
    {
        if ((mpierr = MPI_Waitall(steps, rcvids, MPI_STATUSES_IGNORE)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        if (isend)
            if ((mpierr = MPI_Waitall(steps, sndids, MPI_STATUSES_IGNORE)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    }

    return PIO_NOERR;
}
