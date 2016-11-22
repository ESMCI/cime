/*
 * Tests for names of vars, atts, and dims. Also test the
 * PIOc_strerror() function.
 *
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_names"

#define NUM_NETCDF_FLAVORS 4
#define NDIM 3
#define X_DIM_LEN 400
#define Y_DIM_LEN 400
#define NUM_TIMESTEPS 6
#define VAR_NAME "foo"
#define ATT_NAME "bar"
#define START_DATA_VAL 42

/* The dimension names. */
char dim_name[NDIM][NC_MAX_NAME + 1] = {"timestep", "x", "y"};

/* Length of the dimensions in the sample data. */
int dim_len[NDIM] = {NC_UNLIMITED, X_DIM_LEN, Y_DIM_LEN};

/* Check the dimension names.
 *
 * @param my_rank rank of process
 * @param ncid ncid of open netCDF file
 * @returns 0 for success, error code otherwise. */
int
check_dim_names(int my_rank, int ncid)
{
    char dim_name[NC_MAX_NAME + 1];
    char zero_dim_name[NC_MAX_NAME + 1];
    int ret;

    for (int d = 0; d < NDIM; d++)
    {
        strcpy(dim_name, "11111111111111111111111111111111");
        if ((ret = PIOc_inq_dimname(ncid, d, dim_name)))
            return ret;
	printf("my_rank %d dim %d name %s\n", my_rank, d, dim_name);

        /* Did other ranks get the same name? */
        if (!my_rank)
            strcpy(zero_dim_name, dim_name);
        /*     printf("rank %d dim_name %s zero_dim_name %s\n", my_rank, dim_name, zero_dim_name); */
        if ((ret = MPI_Bcast(&zero_dim_name, strlen(dim_name) + 1, MPI_CHAR, 0,
                             MPI_COMM_WORLD)))
            MPIERR(ret);
        if (strcmp(dim_name, zero_dim_name))
            return ERR_AWFUL;
    }
    return 0;
}

/* Check the variable name.
 *
 * @param my_rank rank of process
 * @param ncid ncid of open netCDF file
 *
 * @returns 0 for success, error code otherwise. */
int
check_var_name(int my_rank, int ncid)
{
    char var_name[NC_MAX_NAME + 1];
    char zero_var_name[NC_MAX_NAME + 1];
    int ret;

    strcpy(var_name, "11111111111111111111111111111111");
    if ((ret = PIOc_inq_varname(ncid, 0, var_name)))
        return ret;
    printf("my_rank %d var name %s\n", my_rank, var_name);

    /* Did other ranks get the same name? */
    if (!my_rank)
        strcpy(zero_var_name, var_name);
    if ((ret = MPI_Bcast(&zero_var_name, strlen(var_name) + 1, MPI_CHAR, 0,
                         MPI_COMM_WORLD)))
        MPIERR(ret);
    if (strcmp(var_name, zero_var_name))
        return ERR_AWFUL;
    return 0;
}

/* Check the attribute name.
 *
 * @param my_rank rank of process
 * @param ncid ncid of open netCDF file
 *
 * @returns 0 for success, error code otherwise. */
int
check_att_name(int my_rank, int ncid)
{
    char att_name[NC_MAX_NAME + 1];
    char zero_att_name[NC_MAX_NAME + 1];
    int ret;

    strcpy(att_name, "11111111111111111111111111111111");
    if ((ret = PIOc_inq_attname(ncid, NC_GLOBAL, 0, att_name)))
        return ret;
    printf("my_rank %d att name %s\n", my_rank, att_name);

    /* Did everyone ranks get the same length name? */
/*    if (strlen(att_name) != strlen(ATT_NAME))
      return ERR_AWFUL;*/
    if (!my_rank)
        strcpy(zero_att_name, att_name);
    if ((ret = MPI_Bcast(&zero_att_name, strlen(att_name) + 1, MPI_CHAR, 0,
                         MPI_COMM_WORLD)))
        MPIERR(ret);
    if (strcmp(att_name, zero_att_name))
        return ERR_AWFUL;
    return 0;
}

/* Check the PIOc_strerror() function.
 *
 * @param my_rank the rank of this process.
 *
 * @return 0 for success, error code otherwise.
 */
int check_strerror(int my_rank)
{
#define NUM_TRIES 6
    char errstr[PIO_MAX_NAME + 1];
    int errcode[NUM_TRIES] = {PIO_EBADID,
                              NC_ENOTNC3, NC4_LAST_ERROR - 1, 0, 1,
                              PIO_EBADIOTYPE};
    const char *expected[NUM_TRIES] = {"NetCDF: Not a valid ID",
                                       "NetCDF: Attempting netcdf-3 operation on netcdf-4 file",
                                       "unknown PIO error", "No error",
                                       nc_strerror(1), "Bad IO type"};
    int ret = PIO_NOERR;

    for (int try = 0; try < NUM_TRIES; try++)
    {
        char result[PIO_MAX_NAME];

        /* Get the error string for this errcode. */
        PIOc_strerror(errcode[try], errstr);

        /* Check that it was as expected. */
        if (strcmp(errstr, expected[try]))
            ret = ERR_AWFUL;
    }

    return ret;
}

/* Run Tests for NetCDF-4 Functions.
 *
 * @param argc argument count
 * @param argv array of arguments
 */
int
main(int argc, char **argv)
{
    /* Zero-based rank of processor. */
    int my_rank;

    /* Number of processors involved in current execution. */
    int ntasks;

    /* Specifies the flavor of netCDF output format. */
    int iotype;

    /* Number of processors that will do IO. In this test we
     * will do IO from all processors. */
    int niotasks;

    /* Stride in the mpi rank between io tasks. Always 1 in this
     * test. */
    int ioproc_stride = 1;

    /* Number of the aggregator? Always 0 in this test. */
    int numAggregator = 0;

    /* Zero based rank of first processor to be used for I/O. */
    int ioproc_start = 0;

    /* The dimension IDs. */
    int dimids[NDIM];

    /* Array index per processing unit. */
    PIO_Offset elements_per_pe;

    /* The ID for the parallel I/O system. */
    int iosysid;

    /* The ncid of the netCDF file. */
    int ncid = 0;

    /* The ID of the netCDF varable. */
    int varid;

    /* The I/O description ID. */
    int ioid;

    /* A buffer for sample data. */
    float *buffer;

    /* A buffer for reading data back from the file. */
    int *read_buffer;

    /* The decomposition mapping. */
    PIO_Offset *compdof;

    /* Return code. */
    int ret;

    /* Index for loops. */
    int fmt, d, d1, i;
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    MPI_Comm test_comm; /* A communicator for this test. */

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS,
			     &test_comm)))
        ERR(ERR_INIT);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
	printf("%d running test code\n", my_rank);
	
        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);

	/* Check the error string function. */
	if ((ret = check_strerror(my_rank)))
	    ERR(ret);

	/* keep things simple - 1 iotask per MPI process */
	niotasks = TARGET_NTASKS;

	/* Initialize the PIO IO system. This specifies how
	 * many and which processors are involved in I/O. */
	if ((ret = PIOc_Init_Intracomm(test_comm, niotasks, ioproc_stride,
				       ioproc_start, PIO_REARR_SUBSET, &iosysid)))
	    ERR(ret);
	printf("%d inited intracomm\n", my_rank);	

	/* Describe the decomposition. This is a 1-based array, so add 1! */
	elements_per_pe = X_DIM_LEN * Y_DIM_LEN / ntasks;
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
	printf("%d inited decomp\n", my_rank);		

	/* Use PIO to create the example file in each of the four
	 * available ways. */
	for (fmt = 0; fmt < num_flavors; fmt++)
	{
	    char filename[NC_MAX_NAME + 1]; /* Test filename. */
	    char iotype_name[NC_MAX_NAME + 1];

	    /* Create a filename. */
	    if ((ret = get_iotype_name(flavor[fmt], iotype_name)))
		return ret;
	    sprintf(filename, "%s_%s.nc", TEST_NAME, iotype_name);

	    /* Create the netCDF output file. */
	    printf("rank: %d Creating sample file %s with format %d...\n",
		   my_rank, filename, flavor[fmt]);
	    if ((ret = PIOc_createfile(iosysid, &ncid, &(flavor[fmt]), filename, PIO_CLOBBER)))
		ERR(ret);

	    /* Define netCDF dimensions and variable. */
	    printf("rank: %d Defining netCDF metadata...\n", my_rank);
	    for (d = 0; d < NDIM; d++)
	    {
		printf("rank: %d Defining netCDF dimension %s, length %d\n", my_rank,
		       dim_name[d], dim_len[d]);
		if ((ret = PIOc_def_dim(ncid, dim_name[d], (PIO_Offset)dim_len[d], &dimids[d])))
		    ERR(ret);
	    }

	    /* Check the dimension names. */
	    if ((ret = check_dim_names(my_rank, ncid)))
		ERR(ret);

	    /* Define a global attribute. */
	    int att_val = 42;
	    if ((ret = PIOc_put_att_int(ncid, NC_GLOBAL, ATT_NAME, NC_INT, 1, &att_val)))
		ERR(ret);

	    /* Check the attribute name. */
	    if ((ret = check_att_name(my_rank, ncid)))
		ERR(ret);

	    /* Define a variable. */
	    if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, &varid)))
		ERR(ret);

	    /* Check the variable name. */
	    if ((ret = check_var_name(my_rank, ncid)))
		ERR(ret);

	    if ((ret = PIOc_enddef(ncid)))
		ERR(ret);

	    /* Close the netCDF file. */
	    printf("rank: %d Closing the sample data file...\n", my_rank);
	    if ((ret = PIOc_closefile(ncid)))
		ERR(ret);

	    /* Put a barrier here to make output look better. */
	    if ((ret = MPI_Barrier(test_comm)))
		MPIERR(ret);
	}

	/* Free the PIO decomposition. */
	printf("rank: %d Freeing PIO decomposition...\n", my_rank);
	if ((ret = PIOc_freedecomp(iosysid, ioid)))
	    ERR(ret);

    } /* endif my_rank < TARGET_NTASKS */

    /* Wait for everyone to catch up. */
    printf("%d %s waiting for all processes!\n", my_rank, TEST_NAME);
    MPI_Barrier(test_comm);

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
