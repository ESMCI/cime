/**
 * @file Tests the PIO library with multiple iosysids in use at the
 * same time.
 *
 * This is a simplified, C version of the fortran
 * pio_iosystem_tests3.F90.
 *
 * @author Ed Hartnett
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_iosystem3"

/* Used when initializing PIO. */
#define STRIDE1 1
#define BASE0 0
#define NUM_IO4 4
#define REARRANGER 1

/** Run async tests. */
int
main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid_world; /* The ID for the parallel I/O system. */
    char fname0[NC_MAX_NAME + 1];
    int ncid;
    int ret; /* Return code. */

    int iotypes[NUM_FLAVORS] = {PIO_IOTYPE_PNETCDF, PIO_IOTYPE_NETCDF,
				PIO_IOTYPE_NETCDF4C, PIO_IOTYPE_NETCDF4P};

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS)))
	ERR(ERR_INIT);

    /* Initialize PIO system on world. */
    if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, NUM_IO4, STRIDE1, BASE0, REARRANGER, &iosysid_world)))
    	ERR(ret);

    for (int i = 0; i < NUM_FLAVORS; i++)
    {
	/* Create the file. */
	sprintf(fname0, "test_iosystem3_simple2_%d.nc", i);
	if ((ret = PIOc_createfile(iosysid_world, &ncid, &iotypes[i], fname0, NC_CLOBBER)))
	    return ret;

	/* End define mode. */
	if ((ret = PIOc_enddef(ncid)))
	    return ret;
	
	/* Close the file. */
	if ((ret = PIOc_closefile(ncid)))
	    return ret;
    
    	/* Now check the first file from WORLD communicator. */
	int mode = PIO_WRITE;

	/* Open the file. Note that we never close it, which is bad,
	 * but should not cause a failure. */
	if ((ret = PIOc_openfile(iosysid_world, &ncid, &iotypes[i], fname0, mode)))
	    return ret;

	/* Check the file. */
	int ndims;
	if ((ret = PIOc_inq(ncid, &ndims, NULL, NULL, NULL)))
	    return ret;
    } /* next iotype */

    /* Finalize PIO systems. */
    printf("%d pio finalizing\n", my_rank);
    if ((ret = PIOc_finalize(iosysid_world)))
    	ERR(ret);

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
	ERR(ERR_AWFUL);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
