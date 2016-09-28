/**
 * @file Tests for PIOc_Intercomm. This tests basic asynch I/O capability.
 * @author Ed Hartnett
 *
 * This very simple test runs on 32 ranks. Eight are used for IO, the
 * other 24 for computation. The netCDF sample files are created and
 * checked.
 *
 * To run with valgrind, use this command:
 * <pre>mpiexec -n 4 valgrind -v --leak-check=full --suppressions=../../../tests/unit/valsupp_test.supp
 * --error-exitcode=99 --track-origins=yes ./test_async_8io_24comp</pre>
 *
 */
#include <pio.h>
#include <pio_tests.h>

/* Number of different combonations of IO and computation processor
 * numbers we will try in this test. */
#define NUM_COMBOS 3

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_async_4proc"

/** Run async tests. */
int
main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid[COMPONENT_COUNT]; /* The ID for the parallel I/O system. */
    int flv; /* Index for loop of PIO netcdf flavors. */
    int ret; /* Return code. */

    int flavor[NUM_FLAVORS] = {PIO_IOTYPE_PNETCDF, PIO_IOTYPE_NETCDF,
			       PIO_IOTYPE_NETCDF4C, PIO_IOTYPE_NETCDF4P};

    /* Num procs for IO and computation. */
    int num_procs[NUM_COMBOS][COMPONENT_COUNT + 1] = {{3, 1}, {2, 2}, {1, 3}};

    /* Number of processors that will do IO. */
    int num_io_procs[NUM_COMBOS] = {3, 2, 1};

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS)))
	ERR(ERR_INIT);
    
    for (int combo = 0; combo < NUM_COMBOS; combo++)
    {
	/* Is the current process a computation task? */
	int comp_task = my_rank < num_io_procs[combo] ? 0 : 1;
	
	/* Initialize the IO system. */
	if ((ret = PIOc_Init_Async(MPI_COMM_WORLD, num_io_procs[combo], NULL, COMPONENT_COUNT,
				   num_procs[combo], NULL, iosysid)))
	    ERR(ERR_INIT);
	
	for (int c = 0; c < COMPONENT_COUNT; c++)
	    printf("%d iosysid[%d] = %d\n", my_rank, c, iosysid[c]);
	
	/* All the netCDF calls are only executed on the computation
	 * tasks. The IO tasks have not returned from PIOc_Init_Intercomm,
	 * and when the do, they should go straight to finalize. */
	if (comp_task)
	{
	    for (int flv = 0; flv < NUM_FLAVORS; flv++)
	    {
		char filename[NC_MAX_NAME + 1]; /* Test filename. */
		int my_comp_idx = 0; /* Index in iosysid array. */
		
		for (int sample = 0; sample < NUM_SAMPLES; sample++)
		{
		    /* Create a filename. */
		    sprintf(filename, "%s_%s_%d_%d.nc", TEST_NAME, flavor_name(flv), sample, my_comp_idx);
		    
		    /* Create sample file. */
		    printf("%d %s creating file %s\n", my_rank, TEST_NAME, filename);
		    if ((ret = create_nc_sample(sample, iosysid[my_comp_idx], flavor[flv], filename, my_rank, NULL)))
			ERR(ret);
		    
		    /* Check the file for correctness. */
		    if ((ret = check_nc_sample(sample, iosysid[my_comp_idx], flavor[flv], filename, my_rank, NULL)))
			ERR(ret);
		}
	    } /* next netcdf flavor */
	    
	    /* Finalize the IO system. Only call this from the computation tasks. */
	    printf("%d %s Freeing PIO resources\n", my_rank, TEST_NAME);
	    for (int c = 0; c < COMPONENT_COUNT; c++)
	    {
		if ((ret = PIOc_finalize(iosysid[c])))
		    ERR(ret);
		printf("%d %s PIOc_finalize completed for iosysid = %d\n", my_rank, TEST_NAME,
		       iosysid[c]);
	    }
	} /* endif comp_task */

	/* Wait for everyone to catch up. */
	printf("%d %s waiting for all processes!\n", my_rank, TEST_NAME);
	MPI_Barrier(MPI_COMM_WORLD);
    } /* next combo */

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
	ERR(ERR_AWFUL);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
