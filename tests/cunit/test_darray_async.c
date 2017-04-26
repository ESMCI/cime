/*
 * This program tests some internal functions in the library related
 * to the box and subset rearranger, and the transfer of data betweeen
 * IO and computation tasks.
 *
 * Ed Hartnett, 3/9/17
 */
#include <pio.h>
#include <pio_tests.h>
#include <pio_internal.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 1

/* The name of this test. */
#define TEST_NAME "test_darray_async"

/* For 1-D use. */
#define NDIM1 1

/* For maplens of 2. */
#define MAPLEN2 2

/* Name of test var. (Name of a Welsh town.)*/
#define VAR_NAME "Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch"

/* These tests are run with different rearrangers and numbers of IO
 * tasks. */
int run_darray_async_test(int numio, int iosysid, int my_rank, MPI_Comm test_comm,
                          int num_flavors, int *flavor)
{
    int ret;

    return 0;
}

/* Run Tests for pio_spmd.c functions. */
int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks;  /* Number of processors involved in current execution. */
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    MPI_Comm test_comm; /* A communicator for this test. */
    int ret;     /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS,
                              TARGET_NTASKS, 3, &test_comm)))
        ERR(ERR_INIT);
    if ((ret = PIOc_set_iosystem_error_handling(PIO_DEFAULT, PIO_RETURN_ERROR, NULL)))
        return ret;

    /* Figure out iotypes. */
    if ((ret = get_iotypes(&num_flavors, flavor)))
        ERR(ret);
    printf("Runnings tests for %d flavors\n", num_flavors);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
        int iosysid;
        int rearranger = ;
        
        if ((ret = PIOc_Init_Intracomm(test_comm, 1, 1, 0, PIO_REARR_BOX, &iosysid)))
            return ret;

        /* Run the simple darray async test. */
        if ((ret = run_darray_async_test(numio, iosysid, my_rank, test_comm,
                                         num_flavors, flavor)))
            return ret;

        /* Finalize PIO system. */
        if ((ret = PIOc_finalize(iosysid)))
            return ret;
    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
