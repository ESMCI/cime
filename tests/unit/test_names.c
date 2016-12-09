/*
 * Tests for names of vars, atts, and dims. Also test the
 * PIOc_strerror() function.
 *
 * Ed Hartnett
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 1

/* The name of this test. */
#define TEST_NAME "test_names"

/* The number of dimensions in the test data. */
#define NDIM 3


#define X_DIM_LEN 400
#define Y_DIM_LEN 400
#define NUM_TIMESTEPS 6
#define VAR_NAME "foo"
#define ATT_NAME "bar"

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
check_dim_names(int my_rank, int ncid, MPI_Comm test_comm)
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
                             test_comm)))
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
check_var_name(int my_rank, int ncid, MPI_Comm test_comm)
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
                         test_comm)))
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
check_att_name(int my_rank, int ncid, MPI_Comm test_comm)
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
                         test_comm)))
        MPIERR(ret);
    if (strcmp(att_name, zero_att_name))
        return ERR_AWFUL;
    return 0;
}

/* 
 * Check error strings. 
 *
 * @param my_rank rank of this task.
 * @param num_tries number of errcodes to try.
 * @param errcode pointer to array of error codes, of length num_tries.
 * @param expected pointer to an array of strings, with the expected
 * error messages for each error code.
 * @returns 0 for success, error code otherwise.
 */
int check_error_strings(int my_rank, int num_tries, int *errcode,
                        const char **expected)
{
    int ret;
    
    /* Try each test code. */
    for (int try = 0; try < num_tries; try++)
    {
        char errstr[PIO_MAX_NAME + 1];
        
        /* Get the error string for this errcode. */
        if ((ret = PIOc_strerror(errcode[try], errstr)))
            return ret;

        if (!my_rank)
            printf("%d for errcode = %d message = %s\n", my_rank, errcode[try], errstr);

        /* Check that it was as expected. */
        if (strncmp(errstr, expected[try], strlen(expected[try])))
        {
            if (!my_rank)
                printf("expected %s got %s\n", expected[try], errstr);
            return ERR_AWFUL;
        }
        if (!my_rank)
            printf("%d errcode = %d passed\n", my_rank, errcode[try]);
    }

    return PIO_NOERR;
}    

/* Check the PIOc_strerror() function for classic netCDF.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror_netcdf(int my_rank)
{
#ifdef _NETCDF
    #define NUM_NETCDF_TRIES 4
    int errcode[NUM_NETCDF_TRIES] = {PIO_EBADID, NC4_LAST_ERROR - 1, 0, 1};
    const char *expected[NUM_NETCDF_TRIES] = {"NetCDF: Not a valid ID",
                                       "Unknown Error: Unrecognized error code", "No error",
                                       nc_strerror(1)};
    int ret;

    if ((ret = check_error_strings(my_rank, NUM_NETCDF_TRIES, errcode, expected)))
        return ret;

    if (!my_rank)
        printf("check_strerror_netcdf SUCCEEDED!\n");
#endif /* (_NETCDF) */

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function for netCDF-4.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror_netcdf4(int my_rank)
{
#ifdef _NETCDF4
#define NUM_NETCDF4_TRIES 2
    int errcode[NUM_NETCDF4_TRIES] = {NC_ENOTNC3, NC_ENOPAR};
    const char *expected[NUM_NETCDF4_TRIES] =
        {"NetCDF: Attempting netcdf-3 operation on netcdf-4 file",
         "NetCDF: Parallel operation on file opened for non-parallel access"};
    int ret;

    if ((ret = check_error_strings(my_rank, NUM_NETCDF4_TRIES, errcode, expected)))
        return ret;

    if (!my_rank)
        printf("check_strerror_netcdf4 SUCCEEDED!\n");
#endif /* _NETCDF4 */

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function for parallel-netCDF.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror_pnetcdf(int my_rank)
{
#ifdef _PNETCDF
#define NUM_PNETCDF_TRIES 2
    int errcode[NUM_PNETCDF_TRIES] = {NC_EMULTIDEFINE_VAR_NUM, NC_EMULTIDEFINE_ATTR_VAL};
    const char *expected[NUM_PNETCDF_TRIES] =
        {"Number of variables is",
         "Attribute value is inconsistent among processes."};
    int ret;

    if ((ret = check_error_strings(my_rank, NUM_PNETCDF_TRIES, errcode, expected)))
        return ret;

    if (!my_rank)
        printf("check_strerror_pnetcdf SUCCEEDED!\n");
#endif /* _PNETCDF */

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function for PIO.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror_pio(int my_rank)
{
#define NUM_PIO_TRIES 6
    int errcode[NUM_PIO_TRIES] = {PIO_EBADID,
                              NC_ENOTNC3, NC4_LAST_ERROR - 1, 0, 1,
                              PIO_EBADIOTYPE};
    const char *expected[NUM_PIO_TRIES] = {"NetCDF: Not a valid ID",
                                       "NetCDF: Attempting netcdf-3 operation on netcdf-4 file",
                                       "Unknown Error: Unrecognized error code", "No error",
                                       nc_strerror(1), "Bad IO type"};
    int ret;

    if ((ret = check_error_strings(my_rank, NUM_PIO_TRIES, errcode, expected)))
        return ret;

    if (!my_rank)
        printf("check_strerror_pio SUCCEEDED!\n");

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror(int my_rank)
{
    int ret;
    if ((ret = check_strerror_netcdf(my_rank)))
        return ret;
    if ((ret = check_strerror_netcdf4(my_rank)))
        return ret;
    if ((ret = check_strerror_pnetcdf(my_rank)))
        return ret;
    if ((ret = check_strerror_pio(my_rank)))
        return ret;
    
}

/* Run Tests for NetCDF-4 Functions. */
int main(int argc, char **argv)
{
    int my_rank;    /* Zero-based rank of processor. */
    int ntasks;     /* Number of processors involved in current execution. */
    int iotype;     /* Specifies the flavor of netCDF output format. */
    int niotasks;   /* Number of processors that will do IO. */
    int ioproc_stride = 1;   /* Stride in the mpi rank between io tasks. */
    int ioproc_start = 0;    /* Zero based rank of first processor to be used for I/O. */
    int dimids[NDIM];        /* The dimension IDs. */
    PIO_Offset elements_per_pe;  /* Array index per processing unit. */
    int iosysid;    /* The ID for the parallel I/O system. */
    int ncid;       /* The ncid of the netCDF file. */
    int varid;      /* The ID of the netCDF varable. */
    int ioid;       /* The I/O description ID. */
    PIO_Offset *compdof;     /* The decomposition mapping. */
    int fmt, d, d1, i;       /* Index for loops. */
    int num_flavors;         /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    MPI_Comm test_comm;      /* A communicator for this test. */
    int ret;                 /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS, TARGET_NTASKS,
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
	    if ((ret = check_dim_names(my_rank, ncid, test_comm)))
		ERR(ret);

	    /* Define a global attribute. */
	    int att_val = 42;
	    if ((ret = PIOc_put_att_int(ncid, NC_GLOBAL, ATT_NAME, NC_INT, 1, &att_val)))
		ERR(ret);

	    /* Check the attribute name. */
	    if ((ret = check_att_name(my_rank, ncid, test_comm)))
		ERR(ret);

	    /* Define a variable. */
	    if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, &varid)))
		ERR(ret);

	    /* Check the variable name. */
	    if ((ret = check_var_name(my_rank, ncid, test_comm)))
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
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
