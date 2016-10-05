/**
 * @file Tests the PIO library with multiple iosysids in use at the
 * same time.
 *
 * This is a simplified, C version of the fortran pio_iosystem_tests2.F90.
 *
 * @author Ed Hartnett
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 2

/* The name of this test. */
#define TEST_NAME "test_iosystem3_simple"

/* Number of test files generated. */
#define NUM_FILES 3

/* Used to define netcdf test file. */
#define PIO_TF_MAX_STR_LEN 100
#define ATTNAME "filename"
#define DIMNAME "filename_dim"

/* Needed to init intracomm. */
#define STRIDE 1
#define BASE 0
#define REARRANGER 1

/** Run test. */
int
main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid; /* The ID for the parallel I/O system. */
    int iosysid_world; /* The ID for the parallel I/O system. */
    int iotypes[NUM_FLAVORS] = {PIO_IOTYPE_PNETCDF, PIO_IOTYPE_NETCDF,
			       PIO_IOTYPE_NETCDF4C, PIO_IOTYPE_NETCDF4P};
    int ret; /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS)))
	ERR(ERR_INIT);

    /* Split world into odd and even. */
    MPI_Comm newcomm;
    int even = my_rank % 2 ? 0 : 1;
    if ((ret = MPI_Comm_split(MPI_COMM_WORLD, even, 0, &newcomm)))
	MPIERR(ret);
    printf("%d newcomm = %d even = %d\n", my_rank, newcomm, even);

    /* Get size of new communicator. */
    int new_size;
    if ((ret = MPI_Comm_size(newcomm, &new_size)))
	MPIERR(ret);

    /* Initialize an intracomm for evens/odds. */
    if ((ret = PIOc_Init_Intracomm(newcomm, new_size, STRIDE, BASE, REARRANGER, &iosysid)))
	ERR(ret);

    /* Initialize an intracomm for all processes. */
    if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, ntasks, STRIDE, BASE, REARRANGER,
				   &iosysid_world)))
	ERR(ret);

    /* Finalize PIO world intracomm. */
    if ((ret = PIOc_finalize(iosysid_world)))
	ERR(ret);

    /* Finalize PIO odd/even intracomm. */
    if ((ret = PIOc_finalize(iosysid)))
	ERR(ret);

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
	ERR(ERR_AWFUL);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
