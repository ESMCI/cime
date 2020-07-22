/*
 * This very simple test for PIO runs on 4 ranks.
 *
 * @author Ed Hartnett
 */
#include <config.h>
#include <pio.h>
#include <pio_tests.h>

/* The name of this test. */
#define TEST_NAME "test_simple"

int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int num_iotasks = 1;
    int iosysid; /* The ID for the parallel I/O system. */
    /* int num_flavors; /\* Number of PIO netCDF flavors in this build. *\/ */
    /* int flavor[NUM_FLAVORS]; /\* iotypes for the supported netCDF IO flavors. *\/ */
    int ret; /* Return code. */

    /* Initialize MPI. */
    if ((ret = MPI_Init(&argc, &argv)))
        MPIERR(ret);

    /* Learn my rank and the total number of processors. */
    if ((ret = MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)))
        MPIERR(ret);
    if ((ret = MPI_Comm_size(MPI_COMM_WORLD, &ntasks)))
        MPIERR(ret);

    /* PIOc_set_log_level(4); */

    /* Change error handling so we can test inval parameters. */
    if ((ret = PIOc_set_iosystem_error_handling(PIO_DEFAULT, PIO_RETURN_ERROR, NULL)))
        ERR(ret);

    /* Initialize the IOsystem. */
    if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, num_iotasks, 1, 0, PIO_REARR_BOX,
				   &iosysid)))
	ERR(ret);

    /* Finalize the IOsystem. */
    if ((ret = PIOc_finalize(iosysid)))
	ERR(ret);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
