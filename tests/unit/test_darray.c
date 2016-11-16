/*
 * Tests for darray functions.
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_darray"

#define NDIM 1
#define DIM_LEN 4
#define VAR_NAME "foo"
#define DIM_NAME "dim"

/* Create the decomposition to divide the data between the 4 tasks. */
int create_decomposition(int ntasks, int my_rank, int iosysid, int *ioid)
{
    PIO_Offset elements_per_pe;     /* Array elements per processing unit. */
    PIO_Offset *compdof;  /* The decomposition mapping. */
    int dim_len[NDIM] = {DIM_LEN};
    int ret;

    /* How many data elements per task? */
    elements_per_pe = DIM_LEN / ntasks;

    /* Allocate space for the decomposition array. */
    if (!(compdof = malloc(elements_per_pe * sizeof(PIO_Offset))))
	return PIO_ENOMEM;

    /* Describe the decomposition. This is a 1-based array, so add 1! */
    for (int i = 0; i < elements_per_pe; i++)
	compdof[i] = my_rank * elements_per_pe + i + 1;

    /* Create the PIO decomposition for this test. */
    printf("%d Creating decomposition elements_per_pe = %d\n", my_rank, elements_per_pe);
    if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, NDIM, dim_len, (PIO_Offset)elements_per_pe,
			       compdof, ioid, NULL, NULL, NULL)))
	ERR(ret);

    printf("%d decomposition initialized.", my_rank);

    /* Free the mapping. */
    free(compdof);

    return 0;
}

/* Check the contents of the test file. */
int check_file(int iosysid, int ntasks, int my_rank, char *filename)
{
    int ncid;
    int ndims, nvars, ngatts, unlimdimid;
    char dim_name_in[NC_MAX_NAME + 1];
    PIO_Offset dim_len_in;
    PIO_Offset arraylen = 1;
    float data_in;
    int ioid;
    int ret;

    assert(filename);

    /* Open the file. */
    if ((ret = PIOc_open(iosysid, filename, NC_NOWRITE, &ncid)))
	return ret;

    /* Check metadata. */
    if ((ret = PIOc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid)))
	return ret;
    if (ndims != 1 || nvars != 1 || ngatts != 0 || unlimdimid != -1)
	return ERR_WRONG;
    if ((ret = PIOc_inq_dim(ncid, 0, dim_name_in, &dim_len_in)))
	return ret;
    if (strcmp(dim_name_in, DIM_NAME) || dim_len_in != DIM_LEN)
	return ERR_WRONG;

    /* Decompose the data over the tasks. */
    if ((ret = create_decomposition(ntasks, my_rank, iosysid, &ioid)))
    	return ret;

    /* Read data. */
    if ((ret = PIOc_read_darray(ncid, 0, ioid, arraylen, &data_in)))
    	return ret;

    /* Check data. */
    if (data_in != my_rank * 10)
	return ERR_WRONG;

    /* Close the file. */
    if ((ret = PIOc_closefile(ncid)))
	return ret;

    return PIO_NOERR;
}

/* Run Tests for darray Functions. */
int main(int argc, char **argv)
{
    int my_rank;     /* Zero-based rank of processor. */
    int ntasks;      /* Number of processors involved in current execution. */
    int iotype;      /* Specifies the flavor of netCDF output format. */
    char filename[NC_MAX_NAME + 1]; /* Name for the output files. */
    int niotasks;    /* Number of processors that will do IO. */
    int ioproc_stride = 1; /* Stride in the mpi rank between io tasks. */
    int numAggregator = 0; /* Number of the aggregator? */
    int ioproc_start = 0;  /* Zero based rank of first I/O processor. */
    int dimids[NDIM];      /* The dimension IDs. */
    PIO_Offset elements_per_pe;     /* Array index per processing unit. */
    int iosysid;   /* The ID for the parallel I/O system. */
    int ncid;      /* The ncid of the netCDF file. */
    int varid;     /* The ID of the netCDF varable. */
    int ioid;      /* The I/O description ID. */
    float *buffer; /* A buffer for sample data. */
    int *read_buffer;     /* A buffer for reading data back from the file. */
    PIO_Offset *compdof;  /* The decomposition mapping. */
    int fmt, d, d1;    /* Index for loops. */
    MPI_Comm test_comm;   /* Contains all tasks running test. */
    int num_flavors;      /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    int ret;              /* Return code. */

    /* Length of the dimensions in the sample data. */
    int dim_len[NDIM] = {DIM_LEN};

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS, &test_comm)))
        ERR(ERR_INIT);
    if (my_rank < TARGET_NTASKS)
    {
        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);

	/* keep things simple - 1 iotask per MPI process */
	niotasks = ntasks;

	/* Initialize the PIO IO system. This specifies how
	 * many and which processors are involved in I/O. */
	if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, niotasks, ioproc_stride,
				       ioproc_start, PIO_REARR_SUBSET, &iosysid)))
	    ERR(ret);

	/* Describe the decomposition. This is a 1-based array, so add 1! */
	elements_per_pe = DIM_LEN / ntasks;
	if (!(compdof = malloc(elements_per_pe * sizeof(PIO_Offset))))
	    return PIO_ENOMEM;
	for (int i = 0; i < elements_per_pe; i++)
	    compdof[i] = my_rank * elements_per_pe + i + 1;

	/* Create the PIO decomposition for this test. */
	printf("rank: %d Creating decomposition...\n", my_rank);
	if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, NDIM, dim_len, (PIO_Offset)elements_per_pe,
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
	    printf("rank: %d Creating sample file %s with format %d...\n", my_rank, filename,
		   flavor[fmt]);
	    if ((ret = PIOc_createfile(iosysid, &ncid, &(flavor[fmt]), filename, PIO_CLOBBER)))
		ERR(ret);

	    /* Define netCDF dimensions and variable. */
	    printf("rank: %d Defining netCDF metadata...\n", my_rank);
	    if ((ret = PIOc_def_dim(ncid, DIM_NAME, (PIO_Offset)dim_len[0], &dimids[0])))
		ERR(ret);

	    /* Define a variable. */
	    if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, &varid)))
		ERR(ret);

	    /* End define mode. */
	    if ((ret = PIOc_enddef(ncid)))
		ERR(ret);

	    /* Write some data. */
	    float fillvalue = 0.0;
	    PIO_Offset arraylen = 1;
	    float test_data[arraylen];
	    for (int f = 0; f < arraylen; f++)
		test_data[f] = my_rank * 10 + f;
	    if ((ret = PIOc_write_darray(ncid, varid, ioid, arraylen, test_data, &fillvalue)))
	    	ERR(ret);

	    /* Close the netCDF file. */
	    printf("rank: %d Closing the sample data file...\n", my_rank);
	    if ((ret = PIOc_closefile(ncid)))
		ERR(ret);

	    /* Put a barrier here to make output look better. */
	    if ((ret = MPI_Barrier(MPI_COMM_WORLD)))
		MPIERR(ret);

	    /* Check the file contents. */
	    if ((ret = check_file(iosysid, ntasks, my_rank, filename)))
		ERR(ret);
	}

	/* Free the PIO decomposition. */
	printf("rank: %d Freeing PIO decomposition...\n", my_rank);
	if ((ret = PIOc_freedecomp(iosysid, ioid)))
	    ERR(ret);

    } /* my_rank < TARGET_NTASKS */

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
        return ERR_AWFUL;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
