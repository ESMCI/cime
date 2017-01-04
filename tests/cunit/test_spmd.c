/*
 * This program tests MPI_Alltoallw by having processor i send different
 * amounts of data to each processor.
 * The first test sends i items to processor i from all processors.
 *
 * Jim Edwards
 * Ed Hartnett, 11/23/16
 */
#include <pio.h>
#include <pio_tests.h>
#include <pio_internal.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 1

/* The name of this test. */
#define TEST_NAME "test_spmd"

/* Number of test cases in inner loop of test. */
#define NUM_TEST_CASES 5

#define TEST_MAX_GATHER_BLOCK_SIZE 32

/* The actual tests are here. */
int run_spmd_tests(MPI_Comm test_comm)
{
    int my_rank;  /* 0-based rank in test_comm. */
    int ntasks;   /* Number of tasks in test_comm. */
    int num_elem; /* Number of elements in buffers. */
    int type_size; /* Size in bytes of an element. */
    int mpierr;   /* Return value from MPI calls. */
    int ret;      /* Return value. */

    /* Learn rank and size. */
    if ((mpierr = MPI_Comm_size(test_comm, &ntasks)))
        MPIERR(mpierr);
    if ((mpierr = MPI_Comm_rank(test_comm, &my_rank)))
        MPIERR(mpierr);

    /* Determine size of buffers. */
    num_elem = ntasks;

    int sbuf[ntasks];    /* The send buffer. */
    int rbuf[ntasks];    /* The receive buffer. */
    int sendcounts[ntasks]; /* Number of elements of data being sent from each task. */
    int recvcounts[ntasks]; /* Number of elements of data being sent from each task. */
    int sdispls[ntasks]; /* Displacements for sending data. */
    int rdispls[ntasks]; /* Displacements for receiving data. */
    MPI_Datatype sendtypes[ntasks]; /* MPI types of data being sent. */
    MPI_Datatype recvtypes[ntasks]; /* MPI types of data being received. */

    /* Load up the send buffer. */
    for (int i = 0; i < num_elem; i++)
        sbuf[i] = my_rank;

    /* Load up the receive buffer to make debugging easier. */
    for (int i = 0; i < num_elem; i++)
        rbuf[i] = -999;

    /* Get the size of the int type for MPI. (Should always be 4.) */
    if ((mpierr = MPI_Type_size(MPI_INT, &type_size)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    assert(type_size == sizeof(int));

    /* Initialize the arrays. */
    for (int i = 0; i < ntasks; i++)
    {
        sendcounts[i] = 1;
        sdispls[i] = 0;
        sendtypes[i] = MPI_INT;
        recvcounts[i] = 1;
        rdispls[i] = i * type_size;
        recvtypes[i] = MPI_INT;
    }

    /* Perform tests for different values of msg_cnt. (BTW it hangs
     * with msg_cnt = 1!). */
    for (int msg_cnt = 0; msg_cnt < TARGET_NTASKS; msg_cnt = msg_cnt ? msg_cnt * 2 : 4)
    {
        if (!my_rank)
            printf("message count %d\n",msg_cnt);

        for (int itest = 0; itest < NUM_TEST_CASES; itest++)
        {
            bool hs = false;
            bool isend = false;

            /* Wait for all tasks. */
            MPI_Barrier(test_comm);

            /* Print results. */
            if (!my_rank)
                for (int e = 0; e < num_elem; e++)
                    printf("sbuf[%d] = %d\n", e, sbuf[e]);

            /* Set the parameters different for each test case. */
            if (itest == 1)
            {
                hs = true;
                isend = true;
            }
            else if (itest == 2)
            {
                hs = false;
                isend = true;
            }
            else if (itest == 3)
            {
                hs = false;
                isend = false;
            }
            else if (itest == 4)
            {
                hs = true;
                isend = false;
            }

            /* Run the swapm function. */
            if ((ret = pio_swapm(sbuf, sendcounts, sdispls, sendtypes, rbuf, recvcounts,
                                 rdispls, recvtypes, test_comm, hs, isend, msg_cnt)))
                return ret;

            /* Print results. */
            /* MPI_Barrier(test_comm); */
            /* for (int e = 0; e < num_elem; e++) */
            /*     printf("%d sbuf[%d] = %d\n", my_rank, e, sbuf[e]); */
            /* MPI_Barrier(test_comm); */
            /* for (int e = 0; e < num_elem; e++) */
            /*     printf("%d rbuf[%d] = %d\n", my_rank, e, rbuf[e]); */

            /* Check that rbuf has 0, 1, ..., ntasks-1. */
            for (int e = 0; e < num_elem; e++)
                if (((int *)rbuf)[e] != e)
                    return ERR_WRONG;
        }
    }

    return 0;
}

int test_CalcStartandCount()
{
    int ndims = 2;
    int gdims[2] = {31, 777602};
    int num_io_procs = 24;
    bool converged = false;
    PIO_Offset start[ndims], kount[ndims];
    int iorank, numaiotasks = 0;
    long int tpsize = 0;
    long int psize;
    long int pgdims = 1;
    int scnt;

    for (int i = 0; i < ndims; i++)
        pgdims *= gdims[i];

    while (!converged)
    {
        for (iorank = 0; iorank < num_io_procs; iorank++)
        {
            numaiotasks = CalcStartandCount(PIO_DOUBLE, ndims, gdims, num_io_procs, iorank, start, kount);
            if (iorank < numaiotasks)
                printf("iorank %d start %ld %ld count %ld %ld\n", iorank, start[0], start[1], kount[0], kount[1]);

            if (numaiotasks < 0)
                return numaiotasks;

            psize = 1;
            scnt = 0;
            for (int i = 0; i < ndims; i++)
            {
                psize *= kount[i];
                scnt += kount[i];
            }
            tpsize += psize;
        }

        if (tpsize == pgdims)
            converged = true;
        else
        {
            printf("Failed to converge %ld %ld %d\n", tpsize, pgdims, num_io_procs);
            tpsize = 0;
            num_io_procs--;
        }
    }

    return 0;
}

/* Run Tests for pio_spmd.c functions. */
int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks;  /* Number of processors involved in current execution. */
    int ret;     /* Return code. */
    MPI_Comm test_comm; /* A communicator for this test. */

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS,
                              TARGET_NTASKS, 3, &test_comm)))
        ERR(ERR_INIT);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
        printf("%d running spmd test code\n", my_rank);
        if ((ret = run_spmd_tests(test_comm)))
            return ret;

        printf("%d running CalcStartandCount test code\n", my_rank);
        if ((ret = test_CalcStartandCount()))
            return ret;

    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
