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
#define TEST_NAME "test_iosystem3_simple"

/* Needed to init intracomm. */
#define STRIDE 1
#define BASE 0
#define REARRANGER 1

/* Used to devide up the tasks into MPI groups. */
#define OVERLAP_NUM_RANGES 2

/** Run test. */
int
main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid_world; /* The ID for the parallel I/O system. */
    int overlap_iosysid; /* The ID for iosystem of overlap_comm. */
    MPI_Group world_group; /* An MPI group of world. */
    MPI_Group overlap_group; /* An MPI group of 0, 1, and 3. */
    MPI_Comm overlap_comm = MPI_COMM_NULL; /* Communicator for tasks 0, 1, 2. */
    int overlap_rank = -1; /* Tasks rank in communicator. */
    int overlap_size = 0; /* Size of communicator. */
    int ret; /* Return code. */

#ifdef TIMING
    /* Initialize the GPTL timing library. */
    if ((ret = GPTLinitialize()))
	return ret;
#endif

    /* Initialize MPI. */
    if ((ret = MPI_Init(&argc, &argv)))
	MPIERR(ret);

    /* Learn my rank and the total number of processors. */
    if ((ret = MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)))
	MPIERR(ret);
    if ((ret = MPI_Comm_size(MPI_COMM_WORLD, &ntasks)))
	MPIERR(ret);

    /* Check that a valid number of processors was specified. */
    if (ntasks != TARGET_NTASKS)
    {
	fprintf(stderr, "ERROR: Number of processors must be exactly %d for this test!\n",
	    TARGET_NTASKS);
	return ERR_AWFUL;
    }

    /* Turn on logging. */
    if ((ret = PIOc_set_log_level(3)))
	return ret;
    
    /* Initialize PIO system on world. */
    if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, 4, 1, 0, 1, &iosysid_world)))
    	ERR(ret);

    /* Get MPI_Group of world comm. */
    if ((ret = MPI_Comm_group(MPI_COMM_WORLD, &world_group)))
	ERR(ret);

    /* Create a group with tasks 0, 1, 3. */
    int overlap_ranges[OVERLAP_NUM_RANGES][3] = {{0, 0, 1}, {1, 3, 2}};
    if ((ret = MPI_Group_range_incl(world_group, OVERLAP_NUM_RANGES,
				    overlap_ranges, &overlap_group)))
	ERR(ret);
    
    /* Create a communicator from the overlap_group. */
    if ((ret = MPI_Comm_create(MPI_COMM_WORLD, overlap_group, &overlap_comm)))
	ERR(ret);

    /* Learn my rank and the total number of processors in overlap
     * group. */
    if (overlap_comm != MPI_COMM_NULL)
    {
	if ((ret = MPI_Comm_rank(overlap_comm, &overlap_rank)))
	    MPIERR(ret);
	if ((ret = MPI_Comm_size(overlap_comm, &overlap_size)))
	    MPIERR(ret);
    }
    printf("%d overlap_comm = %d overlap_rank = %d overlap_size = %d\n", my_rank,
	   overlap_comm, overlap_rank, overlap_size);

    /* Initialize PIO system for overlap comm. */
    if (overlap_comm != MPI_COMM_NULL)
    {
	if ((ret = PIOc_Init_Intracomm(overlap_comm, 1, 1, 0, 1, &overlap_iosysid)))
	    ERR(ret);
    }

    printf("%d pio finalizing %d\n", my_rank, overlap_iosysid);
    /* Finalize PIO system. */
    if (overlap_comm != MPI_COMM_NULL)
    {
	printf("%d calling PIOc_finalize with iosysid = %d\n", my_rank, overlap_iosysid);
	if ((ret = PIOc_finalize(overlap_iosysid)))
	    ERR(ret);
    }
    if ((ret = PIOc_finalize(iosysid_world)))
    	ERR(ret);
    printf("%d pio finalized\n", my_rank);

    /* Free MPI resources used by test. */
    if ((ret = MPI_Group_free(&overlap_group)))
	ERR(ret);
    if ((ret = MPI_Group_free(&world_group)))
	ERR(ret);
    if (overlap_comm != MPI_COMM_NULL)
	if ((ret = MPI_Comm_free(&overlap_comm)))
	    ERR(ret);

    /* Finalize test. */
    printf("%d %s finalizing MPI...\n", my_rank, TEST_NAME);

    /* Finalize MPI. */
    MPI_Finalize();

#ifdef TIMING
    /* Finalize the GPTL timing library. */
    if ((ret = GPTLfinalize()))
	return ret;
#endif

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
