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
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_iosystem2_simple2"

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

    int ncid;
    int ncid2;
    for (int flv = 0; flv < NUM_FLAVORS; flv++)
    {
	char fn[NUM_FILES][NC_MAX_NAME + 1];
	char dimname[NC_MAX_NAME + 1];
	char filename[NUM_SAMPLES][NC_MAX_NAME + 1]; /* Test filename. */
	int sample_ncid[NUM_SAMPLES];

	for (int sample = 0; sample < NUM_SAMPLES; sample++)
	{
	    /* Create a filename. */
	    sprintf(filename[sample], "%s_%s_%d_%d.nc", TEST_NAME, flavor_name(flv), sample, 0);
		    
	    /* Create sample file. */
	    printf("%d %s creating file %s\n", my_rank, TEST_NAME, filename[sample]);
	    if ((ret = create_nc_sample(sample, iosysid_world, iotypes[flv], filename[sample], my_rank, NULL)))
		ERR(ret);
		    
	    /* Check the file for correctness. */
	    if ((ret = check_nc_sample(sample, iosysid_world, iotypes[flv], filename[sample], my_rank, &sample_ncid[sample])))
		ERR(ret);

	}

	/* Now check the files with the other iosysid. Even and odd
	 * processes will check different files. */
	int this_sample = even ? 0 : 1;
	char *file1 = filename[this_sample];
	int ncid2;
	if ((ret = check_nc_sample(this_sample, iosysid, iotypes[flv], file1, my_rank, &ncid2)))
	    ERR(ret);

	/* Now close the open files. */
	for (int sample = 0; sample < NUM_SAMPLES; sample++)
	    if ((ret = PIOc_closefile(sample_ncid[sample])))
		ERR(ret);

	if ((ret = PIOc_closefile(ncid2)))
	    ERR(ret);
	
    } /* next iotype */

    /* Finalize PIO odd/even intracomm. */
    if ((ret = PIOc_finalize(iosysid)))
	ERR(ret);

    /* Finalize PIO world intracomm. */
    if ((ret = PIOc_finalize(iosysid_world)))
	ERR(ret);

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
	ERR(ERR_AWFUL);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
