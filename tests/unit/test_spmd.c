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
#include <sys/time.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 2

/* The name of this test. */
#define TEST_NAME "test_spmd"

#define TEST_MAX_GATHER_BLOCK_SIZE 32

/* The actual tests are here. */
int run_spmd_tests(MPI_Comm test_comm)
{
    int my_rank;  /* 0-based rank in test_comm. */
    int ntasks;   /* Number of tasks in test_comm. */
    int num_elem; /* Number of elements in buffers. */
    int type_size; /* Size in bytes of an element. */
    struct timeval t1, t2; /* For timing. */
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

    //    for (int msg_cnt=4; msg_cnt<size; msg_cnt*=2){
    //   if (rank==0) printf("message count %d\n",msg_cnt);
    int msg_cnt = 0;
    for (int itest = 0; itest < 1; itest++)
    {
        bool hs = false;
        bool isend = false;

        /* Wait for all tasks. */
        MPI_Barrier(test_comm);

        if (!my_rank)
        {
            printf("Start itest %d\n", itest);
            gettimeofday(&t1, NULL);
        }

        /* Print results. */
        if (!my_rank)
        {
            for (int e = 0; e < num_elem; e++)
                printf("sbuf[%d] = %d\n", e, sbuf[e]);
        }

        if (itest == 0)
            ret = pio_swapm(sbuf, sendcounts, sdispls, sendtypes, rbuf, recvcounts,
                            rdispls, recvtypes, test_comm, hs, isend, 0);
        /* else if (itest == 1) */
        /* { */
        /*     hs = true; */
        /*     isend = true; */
        /*     ret = pio_swapm(ntasks, my_rank, sbuf,  sendcounts, sdispls, sendtypes, */
        /*                     rbuf,  recvcounts, rdispls, recvtypes, test_comm, hs, isend, msg_cnt); */
        /* } */
        /* else if (itest == 2) */
        /* { */
        /*     hs = false; */
        /*     isend = true; */
        /*     ret = pio_swapm(ntasks, my_rank, sbuf, sendcounts, sdispls, sendtypes, */
        /*                     rbuf, recvcounts, rdispls, recvtypes, test_comm, hs, isend, msg_cnt); */

        /* } */
        /* else if (itest == 3) */
        /* { */
        /*     hs = false; */
        /*     isend = false; */
        /*     ret = pio_swapm(ntasks, my_rank, sbuf, sendcounts, sdispls, sendtypes, */
        /*                     rbuf, recvcounts, rdispls, recvtypes, test_comm, hs, isend, msg_cnt); */

        /* } */
        /* else if (itest == 4) */
        /* { */
        /*     hs = true; */
        /*     isend = false; */
        /*     ret = pio_swapm(ntasks, my_rank, sbuf,  sendcounts, sdispls, sendtypes, */
        /*                     rbuf,  recvcounts, rdispls, recvtypes, test_comm, hs, isend, msg_cnt); */

        /* } */

        if (!my_rank)
        {
            gettimeofday(&t2, NULL);
            printf("itest = %d Time in microseconds: %ld microseconds\n", itest,
                   ((t2.tv_sec - t1.tv_sec) * 1000000L + t2.tv_usec) - t1.tv_usec);
        }

        /* Print results. */
        MPI_Barrier(test_comm);
        for (int e = 0; e < num_elem; e++)
            printf("%d sbuf[%d] = %d\n", my_rank, e, sbuf[e]);
        MPI_Barrier(test_comm);
        for (int e = 0; e < num_elem; e++)
            printf("%d rbuf[%d] = %d\n", my_rank, e, rbuf[e]);
    }

    /* Test pio_fc_gather. In fact it does not work for msg_cnt > 0. */
    /* for (int msg_cnt = 0; msg_cnt <= TEST_MAX_GATHER_BLOCK_SIZE; */
    /*      msg_cnt = msg_cnt ? msg_cnt * 2 : 1) */
    /* int msg_cnt = 0; */
    /* { */
    /*     /\* Load up the buffers *\/ */
    /*     for (int i = 0; i < num_elem; i++) */
    /*     { */
    /*         sbuf[i] = i + 100 * my_rank; */
    /*         rbuf[i] = -i; */
    /*     } */

    /*     printf("%d Testing pio_fc_gather with msg_cnt = %d\n", my_rank, msg_cnt); */

    /*     /\* Start timeer. *\/ */
    /*     if (!my_rank) */
    /*         gettimeofday(&t1, NULL); */

    /*     /\* Run the gather function. *\/ */
    /*     /\* if ((ret = pio_fc_gather(sbuf, ntasks, MPI_INT, rbuf, ntasks, MPI_INT, 0, test_comm, *\/ */
    /*     /\*                          msg_cnt))) *\/ */
    /*     /\*     return ret; *\/ */

    /*     /\* Only check results on task 0. *\/ */
    /*     if (!my_rank) */
    /*     { */
    /*         /\* Stop timer. *\/ */
    /*         gettimeofday(&t2, NULL); */
    /*         printf("Time in microseconds: %ld microseconds\n", */
    /*                ((t2.tv_sec - t1.tv_sec) * 1000000L + t2.tv_usec) - t1.tv_usec); */

    /*         /\* Check results. *\/ */
    /*         for (int j = 0; j < ntasks; j++) */
    /*             for (int i = 0; i < ntasks; i++) */
    /*                 if (rbuf[i + j * ntasks] != i + 100 * j) */
    /*                     printf("got %d expected %d\n", rbuf[i + j * ntasks], i + 100 * j); */
    /*     } */


    /*     /\* Wait for all test tasks. *\/ */
    /*     MPI_Barrier(test_comm); */
    /* } */

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
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS,
                             &test_comm)))
        ERR(ERR_INIT);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
        printf("%d running test code\n", my_rank);
        if ((ret = run_spmd_tests(test_comm)))
            return ret;

    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
