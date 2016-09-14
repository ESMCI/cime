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
#include <unistd.h>
#ifdef TIMING
#include <gptl.h>
#endif

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

/** The number of possible output netCDF output flavors available to
 * the ParallelIO library. */
#define NUM_NETCDF_FLAVORS 4

/** The number of dimensions in the test data. */
#define NDIM 1

/** The length of our test data. */
#define DIM_LEN 4

/** The name of the dimension in the netCDF output file. */
#define FIRST_DIM_NAME "jojo"
#define DIM_NAME "dim_test_intercomm3"

/** The name of the variable in the netCDF output file. */
#define FIRST_VAR_NAME "bill"
#define VAR_NAME "var_test_intercomm3"

/** Error code for when things go wrong. */
#define ERR_AWFUL 1111
#define ERR_WRONG 2222

/** Handle MPI errors. This should only be used with MPI library
 * function calls. */
#define MPIERR(e) do {                                                  \
	MPI_Error_string(e, err_buffer, &resultlen);			\
	fprintf(stderr, "MPI error, line %d, file %s: %s\n", __LINE__, __FILE__, err_buffer); \
	MPI_Finalize();							\
	return ERR_AWFUL;							\
    } while (0)

/** Handle non-MPI errors by finalizing the MPI library and exiting
 * with an exit code. */
#define ERR(e) do {				\
        fprintf(stderr, "Error %d in %s, line %d\n", e, __FILE__, __LINE__); \
	MPI_Finalize();				\
	return e;				\
    } while (0)

/** Global err buffer for MPI. When there is an MPI error, this buffer
 * is used to store the error message that is associated with the MPI
 * error. */
char err_buffer[MPI_MAX_ERROR_STRING];

/** This is the length of the most recent MPI error message, stored
 * int the global error string. */
int resultlen;

/* Check the file for correctness. */
int
check_file(int iosysid, int format, char *filename, int my_rank)
{
    int ncid;
    int ret;
    int ndims, nvars, ngatts, unlimdimid;
    int ndims2, nvars2, ngatts2, unlimdimid2;
    int dimid2;
    char dimname[NC_MAX_NAME + 1];
    PIO_Offset dimlen;
    char dimname2[NC_MAX_NAME + 1];
    PIO_Offset dimlen2;
    char varname[NC_MAX_NAME + 1];
    nc_type vartype;
    int varndims, vardimids, varnatts;
    char varname2[NC_MAX_NAME + 1];
    nc_type vartype2;
    int varndims2, vardimids2, varnatts2;
    int varid2;
    int att_data;
    short short_att_data;
    float float_att_data;
    double double_att_data;

    /* Re-open the file to check it. */
    printf("%d test_intercomm3 opening file %s format %d\n", my_rank, filename, format);
    if ((ret = PIOc_openfile(iosysid, &ncid, &format, filename,
    			     NC_NOWRITE)))
    	ERR(ret);

    /* Try to read the data. */
    PIO_Offset start[NDIM] = {0}, count[NDIM] = {DIM_LEN};
    int data_in[DIM_LEN];
    if ((ret = PIOc_get_vars_tc(ncid, 0, start, count, NULL, NC_INT, data_in)))
    	ERR(ret);
    for (int i = 0; i < DIM_LEN; i++)
    {
    	printf("%d test_intercomm3 read data_in[%d] = %d\n", my_rank, i, data_in[i]);
    	if (data_in[i] != i)
    	    ERR(ERR_AWFUL);
    }

    /* Find the number of dimensions, variables, and global attributes.*/
    if ((ret = PIOc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid)))
    	ERR(ret);
    if (ndims != 1 || nvars != 1 || ngatts != 0 || unlimdimid != -1)
    	ERR(ERR_WRONG);

    /* This should return PIO_NOERR. */
    if ((ret = PIOc_inq(ncid, NULL, NULL, NULL, NULL)))
    	ERR(ret);

    /* Check the other functions that get these values. */
    if ((ret = PIOc_inq_ndims(ncid, &ndims2)))
    	ERR(ret);
    if (ndims2 != 1)
    	ERR(ERR_WRONG);
    if ((ret = PIOc_inq_nvars(ncid, &nvars2)))
    	ERR(ret);
    if (nvars2 != 1)
    	ERR(ERR_WRONG);
    if ((ret = PIOc_inq_natts(ncid, &ngatts2)))
    	ERR(ret);
    if (ngatts2 != 0)
    	ERR(ERR_WRONG);
    if ((ret = PIOc_inq_unlimdim(ncid, &unlimdimid2)))
    	ERR(ret);
    if (unlimdimid != -1)
    	ERR(ERR_WRONG);

    /* Check out the dimension. */
    if ((ret = PIOc_inq_dim(ncid, 0, dimname, &dimlen)))
    	ERR(ret);
    if (strcmp(dimname, DIM_NAME) || dimlen != DIM_LEN)
    	ERR(ERR_WRONG);

    /* Check out the variable. */
    if ((ret = PIOc_inq_var(ncid, 0, varname, &vartype, &varndims, &vardimids, &varnatts)))
    	ERR(ret);
    if (strcmp(varname, VAR_NAME) || vartype != NC_INT || varndims != NDIM ||
    	vardimids != 0 || varnatts != 0)
    	ERR(ERR_WRONG);

    /* Close the file. */
    printf("%d test_intercomm3 closing file (again) ncid = %d\n", my_rank, ncid);
    if ((ret = PIOc_closefile(ncid)))
    	ERR(ret);

    return 0;
}

/** Run Tests for Init_Intercomm
 *
 * @param argc argument count
 * @param argv array of arguments
 */
int
main(int argc, char **argv)
{
    /** Zero-based rank of processor. */
    int my_rank;

    /** Number of processors involved in current execution. */
    int ntasks;

    /** Different output flavors. */
    int format[NUM_NETCDF_FLAVORS] = {PIO_IOTYPE_PNETCDF,
				      PIO_IOTYPE_NETCDF,
				      PIO_IOTYPE_NETCDF4C,
				      PIO_IOTYPE_NETCDF4P};

    /** Names for the output files. */
    char base_filename[NUM_NETCDF_FLAVORS][NC_MAX_NAME + 1] = {"test_intercomm4_pnetcdf",
							       "test_intercomm4_classic",
							       "test_intercomm4_serial4",
							       "test_intercomm4_parallel4"};

    /** The ID for the parallel I/O system. */
    int iosysid[COMPONENT_COUNT];

    /** The ncid of the netCDF file. */
    int ncid;

    /** The ID of the netCDF varable. */
    int varid;

    /** Return code. */
    int ret;

    /** Index for loops. */
    int fmt, d, d1, i;

#ifdef TIMING
    /* Initialize the GPTL timing library. */
    if ((ret = GPTLinitialize ()))
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
    if (ntasks != 2)
    {
	fprintf(stderr, "test_intercomm4 Number of processors must be exactly 2!\n");
	ERR(ERR_AWFUL);
    }
    printf("%d: test_intercomm4 ParallelIO Library test_intercomm4 running on %d processors.\n",
	   my_rank, ntasks);

    /* Turn on logging. */
    if ((ret = PIOc_set_log_level(3)))
	ERR(ret);

    /* How many processors will be used for our IO and computation
     * component. */
    int num_procs[COMPONENT_COUNT + 1] = {1, 1};

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
    	    int ncid, varid, dimid;
    	    PIO_Offset start[NDIM], count[NDIM] = {0};
    	    int data[DIM_LEN];
	    char filename[NC_MAX_NAME + 1];

	    /* Create a filename for this computation component. */
	    sprintf(filename, "%s_%d.nc", base_filename[fmt], my_comp_idx);

    	    /* Create a netCDF file with one dimension and one variable. */
	    printf("%d test_intercomm4 creating file %s\n", my_rank, filename);
    	    if ((ret = PIOc_createfile(iosysid[my_comp_idx], &ncid, &format[fmt], filename,
    	    			       NC_CLOBBER)))
    	    	ERR(ret);
	    printf("%d test_intercomm4 file created ncid = %d\n", my_rank, ncid);

    	    /* /\* End define mode, then re-enter it. *\/ */
    	    if ((ret = PIOc_enddef(ncid)))
    	    	ERR(ret);
	    printf("%d test_intercomm4 calling redef\n", my_rank);
    	    if ((ret = PIOc_redef(ncid)))
    	    	ERR(ret);

    	    /* Define a dimension. */
    	    char dimname2[NC_MAX_NAME + 1];
	    printf("%d test_intercomm4 defining dimension %s\n", my_rank, DIM_NAME);
    	    if ((ret = PIOc_def_dim(ncid, DIM_NAME, DIM_LEN, &dimid)))
    	    	ERR(ret);

    	    /* Define a 1-D variable. */
    	    char varname2[NC_MAX_NAME + 1];
	    printf("%d test_intercomm4 defining variable %s\n", my_rank, VAR_NAME);
    	    if ((ret = PIOc_def_var(ncid, VAR_NAME, NC_INT, NDIM, &dimid, &varid)))
    	    	ERR(ret);

    	    /* char *buf111 = malloc(19999); */

    	    /* End define mode. */
	    printf("%d test_intercomm4 ending define mode ncid = %d\n", my_rank, ncid);
    	    if ((ret = PIOc_enddef(ncid)))
    	    	ERR(ret);
	    printf("%d test_intercomm4 define mode ended ncid = %d\n", my_rank, ncid);

    	    /* Write some data. For the PIOc_put/get functions, all
    	     * data must be on compmaster before the function is
    	     * called. Only compmaster's arguments are passed to the
    	     * async msg handler. All other computation tasks are
    	     * ignored. */
    	    for (int i = 0; i < DIM_LEN; i++)
    	    	data[i] = i;
	    printf("%d test_intercomm4 writing data\n", my_rank);
    	    start[0] = 0;
    	    count[0] = DIM_LEN;
    	    if ((ret = PIOc_put_vars_tc(ncid, varid, start, count, NULL, NC_INT, data)))
    	    	ERR(ret);

    	    /* Close the file. */
	    printf("%d test_intercomm4 closing file ncid = %d\n", my_rank, ncid);
    	    if ((ret = PIOc_closefile(ncid)))
    	    	ERR(ret);
	    printf("%d test_intercomm4 closed file ncid = %d\n", my_rank, ncid);

    	    /* Check the file for correctness. */
    	    if ((ret = check_file(iosysid[my_comp_idx], format[fmt], filename, my_rank)))
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
