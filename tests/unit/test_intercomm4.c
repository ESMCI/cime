/**
 * @file Tests for PIOc_Intercomm. This tests the Init_Intercomm()
 * function, and basic asynch I/O capability.
 *
 * To run with valgrind, use this command:
 * <pre>mpiexec -n 4 valgrind -v --leak-check=full --suppressions=../../../tests/unit/valsupp_test.supp
 * --error-exitcode=99 --track-origins=yes ./test_intercomm3</pre>
 *
 */
#include <pio.h>
#include <pio_tests.h>

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 2

/** The number of possible output netCDF output flavors available to
 * the ParallelIO library. */
#define NUM_NETCDF_FLAVORS 4

/** Run Tests for Init_Intercomm
 */
int
main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid[COMPONENT_COUNT]; /* The ID for the parallel I/O system. */
    int fmt; /* Index for loop of PIO netcdf formats. */
    int ret; /* Return code. */
    int format[NUM_NETCDF_FLAVORS] = {PIO_IOTYPE_PNETCDF,  /* Output flavors. */
				      PIO_IOTYPE_NETCDF,
				      PIO_IOTYPE_NETCDF4C,
				      PIO_IOTYPE_NETCDF4P};
    char base_filename[NUM_NETCDF_FLAVORS][NC_MAX_NAME + 1] = {"test_intercomm4_pnetcdf",
							       "test_intercomm4_classic",
							       "test_intercomm4_serial4",
							       "test_intercomm4_parallel4"};
    int num_procs[COMPONENT_COUNT + 1] = {1, 1}; /* Num procs for IO and computation. */


    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS)))
	ERR(ERR_AWFUL);
    
    /* Is the current process a computation task? */
    int comp_task = my_rank < 1 ? 0 : 1;

    /* Index of computation task in iosysid array. Varies by rank and
     * does not apply to IO component processes. */
    int my_comp_idx = comp_task ? my_rank - 1 : -1;

    /* Initialize the IO system. */
    if ((ret = PIOc_Init_Async(MPI_COMM_WORLD, NUM_IO_PROCS, NULL, COMPONENT_COUNT,
			       num_procs, NULL, iosysid)))
	ERR(ERR_AWFUL);

    /* All the netCDF calls are only executed on the computation
     * tasks. The IO tasks have not returned from PIOc_Init_Intercomm,
     * and when the do, they should go straight to finalize. */
    if (comp_task)
    {
    	for (int fmt = 0; fmt < NUM_NETCDF_FLAVORS; fmt++)
    	{
	    char filename[NC_MAX_NAME + 1];

	    /* Create a filename for this computation component. */
	    sprintf(filename, "%s_%d.nc", base_filename[fmt], my_comp_idx);

    	    /* Create a netCDF file with one dimension and one variable. */
	    printf("%d test_intercomm4 creating file %s\n", my_rank, filename);

	    /* Create the sample file. */
	    if ((ret = create_nc_sample_1(iosysid[my_comp_idx], format[fmt], filename, my_rank)))
		ERR(ret);

    	    /* Check the file for correctness. */
    	    if ((ret = check_nc_sample_1(iosysid[my_comp_idx], format[fmt], filename, my_rank)))
    	    	ERR(ret);

    	} /* next netcdf format flavor */

	/* Finalize the IO system. Only call this from the computation tasks. */
	printf("%d test_intercomm4 Freeing PIO resources\n", my_rank);
	for (int c = 0; c < COMPONENT_COUNT; c++)
	{
	    if ((ret = PIOc_finalize(iosysid[c])))
		ERR(ret);
	    printf("%d test_intercomm4 PIOc_finalize completed for iosysid = %d\n", my_rank, iosysid[c]);
	}
    } /* endif comp_task */

    printf("%d test_intercomm4 Freeing local MPI resources...\n", my_rank);

    /* Wait for everyone to catch up. */
    printf("%d test_intercomm4 waiting for other processes!\n", my_rank);
    MPI_Barrier(MPI_COMM_WORLD);
    printf("%d test_intercomm4 done waiting for other processes!\n", my_rank);

    /* Finalize the MPI library. */
    printf("finalizing MPI");
    MPI_Finalize();
    printf("finalized MPI");

#ifdef TIMING
    /* Finalize the GPTL timing library. */
    if ((ret = GPTLfinalize()))
	return ret;
#endif

    printf("%d test_intercomm4 SUCCESS!!\n", my_rank);

    return 0;
}
