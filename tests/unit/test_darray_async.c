/*
 * Tests for darray functions.
 * @author Ed Hartnett
 *
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_darray_async"

#define NDIM 3
#define X_DIM_LEN 400
#define Y_DIM_LEN 400
#define VAR_NAME "foo"

/* The dimension names. */
char dim_name[NDIM][NC_MAX_NAME + 1] = {"timestep", "x", "y"};

/* Length of the dimensions in the sample data. */
int dim_len[NDIM] = {NC_UNLIMITED, X_DIM_LEN, Y_DIM_LEN};

/* Run Tests for darray Functions. */
int main(int argc, char **argv)
{
    int my_rank;  /* Zero-based rank of processor. */
    int ntasks;   /* Number of processors involved in current execution. */    
    int iotype;   /* Specifies the flavor of netCDF output format. */
    char filename[NC_MAX_NAME + 1]; /* Name for output file. */
    int niotasks;    /* Number of processors that will do IO. */
    int ioproc_stride = 1; /* Stride in the mpi rank between io tasks. */
    int numAggregator = 0; /* Number of the aggregator? */
    int ioproc_start = 0;  /* Zero based rank of first processor to be used for I/O. */
    int dimids[NDIM];      /* The dimension IDs. */
    PIO_Offset elements_per_pe;  /* Array index per processing unit. */    
    int iosysid; /* The ID for the parallel I/O system. */
    int ncid;    /* The ncid of the netCDF file. */
    int varid;   /* The ncid of the netCDF file. */
    int ioid;    /* The I/O description ID. */
    float *buffer;     /* A buffer for sample data. */
    int *read_buffer;  /* A buffer for reading data back from the file. */
    PIO_Offset *compdof;  /* The decomposition mapping. */
    MPI_Comm test_comm;   /* Contains all tasks running test. */
    int num_flavors;      /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    int fmt, d, d1, i;    /* Index for loops. */
    int ret;     /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS,
			     &test_comm)))
        ERR(ERR_INIT);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);

	/* keep things simple - 1 iotask per MPI process */
	niotasks = TARGET_NTASKS;

	/* Initialize the PIO IO system. This specifies how
	 * many and which processors are involved in I/O. */
	if ((ret = PIOc_Init_Intracomm(test_comm, niotasks, ioproc_stride,
				       ioproc_start, PIO_REARR_SUBSET, &iosysid)))
	    ERR(ret);

	/* Describe the decomposition. This is a 1-based array, so add 1! */
	elements_per_pe = X_DIM_LEN * Y_DIM_LEN / TARGET_NTASKS;
	if (!(compdof = malloc(elements_per_pe * sizeof(PIO_Offset))))
	    return PIO_ENOMEM;
	for (i = 0; i < elements_per_pe; i++) {
	    compdof[i] = my_rank * elements_per_pe + i + 1;
	}

	/* Create the PIO decomposition for this test. */
	printf("rank: %d Creating decomposition...\n", my_rank);
	if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, 2, &dim_len[1], (PIO_Offset)elements_per_pe,
				   compdof, &ioid, NULL, NULL, NULL)))
	    ERR(ret);
	free(compdof);

	/* Use PIO to create the example file in each of the four
	 * available ways. */
	for (fmt = 0; fmt < num_flavors; fmt++)
	{
	    /* Create the filename. */
	    sprintf(filename, "%s_%d.nc", TEST_NAME, flavor[fmt]);
	
	    /* Create the netCDF output file. */
	    printf("rank: %d Creating sample file %s with format %d...\n",
		   my_rank, filename, flavor[fmt]);
	    if ((ret = PIOc_createfile(iosysid, &ncid, &(flavor[fmt]), filename,
				       PIO_CLOBBER)))
		ERR(ret);

	    /* Define netCDF dimensions and variable. */
	    printf("rank: %d Defining netCDF metadata...\n", my_rank);
	    for (d = 0; d < NDIM; d++) {
		printf("rank: %d Defining netCDF dimension %s, length %d\n", my_rank,
		       dim_name[d], dim_len[d]);
		if ((ret = PIOc_def_dim(ncid, dim_name[d], (PIO_Offset)dim_len[d], &dimids[d])))
		    ERR(ret);
	    }

	    /* Define a variable. */
	    if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, &varid)))
		ERR(ret);

	    if ((ret = PIOc_enddef(ncid)))
		ERR(ret);

	    /* Close the netCDF file. */
	    printf("rank: %d Closing the sample data file...\n", my_rank);
	    if ((ret = PIOc_closefile(ncid)))
		ERR(ret);

	    /* Put a barrier here to make verbose output look better. */
	    if ((ret = MPI_Barrier(test_comm)))
		MPIERR(ret);
	}

	/* Free the PIO decomposition. */
	printf("rank: %d Freeing PIO decomposition...\n", my_rank);
	if ((ret = PIOc_freedecomp(iosysid, ioid)))
	    ERR(ret);
    } /* my_rank < TARGET_NTASKS */

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ERR_AWFUL;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
