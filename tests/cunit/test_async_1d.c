/*
 * Tests for PIOc_Intercomm. This tests basic asynch I/O capability.
 *
 * This very simple test runs on 4 ranks.
 *
 * @author Ed Hartnett
 */
#include <config.h>
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The number of IO tasks. */
#define NUM_IO_TASKS 1

/* The number of computational tasks. */
#define NUM_COMP_TASKS 3

/* The name of this test. */
#define TEST_NAME "test_async_1d"

/* Number of different combonations of IO and computation processor
 * numbers we will try in this test. */
#define NUM_COMBOS 3

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

/* Run async tests. */
int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid; /* The ID for the parallel I/O system. */
    int num_procs_per_comp[COMPONENT_COUNT] = {3};
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    int ret; /* Return code. */

    /* Initialize MPI. */
    if ((ret = MPI_Init(&argc, &argv)))
        MPIERR(ret);

    /* Learn my rank and the total number of processors. */
    if ((ret = MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)))
        MPIERR(ret);
    if ((ret = MPI_Comm_size(MPI_COMM_WORLD, &ntasks)))
        MPIERR(ret);

    /* Make sure we have 4 tasks. */
    if (ntasks != TARGET_NTASKS) ERR(ERR_WRONG);

    PIOc_set_log_level(4);

    /* Set up IO system. Task 0 will do IO, tasks 1-3 will be a single
     * computational unit. */
    if ((ret = PIOc_init_async(MPI_COMM_WORLD, NUM_IO_TASKS, NULL, COMPONENT_COUNT,
                               num_procs_per_comp, NULL, NULL, NULL,
                               PIO_REARR_BOX, &iosysid)))
        ERR(ret);

    /* Only computational processors run this code. */
    if (my_rank)
    {
        if ((ret = PIOc_finalize(iosysid)))
            ERR(ret);
    }

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
