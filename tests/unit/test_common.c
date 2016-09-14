/**
 * @file Common test code for some PIO tests.
 *
 */
#include <pio.h>
#include <pio_tests.h>

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

/* Name of each flavor. */
char *
flavor_name(int flavor)
{
    char *ans = NULL;
    char flavor_name[NUM_FLAVORS][NC_MAX_NAME + 1] = {"pnetcdf", "classic",
						      "serial4", "parallel4"};

    if (flavor < NUM_FLAVORS)
	ans = flavor_name[flavor];

    return ans;
}

/* Initalize the test system. */
int
pio_test_init(int argc, char **argv, int *my_rank, int *ntasks,
	      int target_ntasks)
{
    int ret; /* Return value. */
    
#ifdef TIMING
    /* Initialize the GPTL timing library. */
    if ((ret = GPTLinitialize()))
	return ret;
#endif

    /* Initialize MPI. */
    if ((ret = MPI_Init(&argc, &argv)))
	MPIERR(ret);

    /* Learn my rank and the total number of processors. */
    if ((ret = MPI_Comm_rank(MPI_COMM_WORLD, my_rank)))
	MPIERR(ret);
    if ((ret = MPI_Comm_size(MPI_COMM_WORLD, ntasks)))
	MPIERR(ret);

    /* Check that a valid number of processors was specified. */
    if (*ntasks != target_ntasks)
    {
	fprintf(stderr, "ERROR: Number of processors must be exactly %d for this test!\n",
	    target_ntasks);
	ERR(ERR_AWFUL);
    }

    /* Turn on logging. */
    if ((ret = PIOc_set_log_level(3)))
	ERR(ret);
    
    return PIO_NOERR;
}

/* Finalize a test. */
int
pio_test_finalize()
{
    int ret; /* Return value. */
    
    /* Finalize MPI. */
    MPI_Finalize();

#ifdef TIMING
    /* Finalize the GPTL timing library. */
    if ((ret = GPTLfinalize()))
	return ret;
#endif

}    

/* Check the file for correctness. */
int
check_nc_sample_1(int iosysid, int format, char *filename, int my_rank)
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

/** This creates a netCDF file in the specified format, with some
 * sample values. */
int
create_nc_sample_1(int iosysid, int format, char *filename, int my_rank)
{
    /* The ncid of the netCDF file. */
    int ncid;

    /* The ID of the netCDF varable. */
    int varid;

    /* The ID of the netCDF dimension. */
    int dimid;

    /* Return code. */
    int ret;

    /* Start and count arrays for netCDF. */
    PIO_Offset start[NDIM], count[NDIM] = {0};

    /* The sample data. */
    int data[DIM_LEN];

    /* Create the file. */
    if ((ret = PIOc_createfile(iosysid, &ncid, &format, filename, NC_CLOBBER)))
	return ret;
    printf("%d file created ncid = %d\n", my_rank, ncid);

    /* /\* End define mode, then re-enter it. *\/ */
    if ((ret = PIOc_enddef(ncid)))
	return ret;
    printf("%d calling redef\n", my_rank);
    if ((ret = PIOc_redef(ncid)))
	return ret;

    /* Define a dimension. */
    char dimname2[NC_MAX_NAME + 1];
    printf("%d defining dimension %s\n", my_rank, DIM_NAME);
    if ((ret = PIOc_def_dim(ncid, DIM_NAME, DIM_LEN, &dimid)))
	return ret;

    /* Define a 1-D variable. */
    char varname2[NC_MAX_NAME + 1];
    printf("%d defining variable %s\n", my_rank, VAR_NAME);
    if ((ret = PIOc_def_var(ncid, VAR_NAME, NC_INT, NDIM, &dimid, &varid)))
	return ret;

    /* End define mode. */
    printf("%d ending define mode ncid = %d\n", my_rank, ncid);
    if ((ret = PIOc_enddef(ncid)))
	return ret;
    printf("%d define mode ended ncid = %d\n", my_rank, ncid);

    /* Write some data. For the PIOc_put/get functions, all data must
     * be on compmaster before the function is called. Only
     * compmaster's arguments are passed to the async msg handler. All
     * other computation tasks are ignored. */
    for (int i = 0; i < DIM_LEN; i++)
	data[i] = i;
    printf("%d writing data\n", my_rank);
    start[0] = 0;
    count[0] = DIM_LEN;
    if ((ret = PIOc_put_vars_tc(ncid, varid, start, count, NULL, NC_INT, data)))
	return ret;

    /* Close the file. */
    printf("%d closing file ncid = %d\n", my_rank, ncid);
    if ((ret = PIOc_closefile(ncid)))
	return ret;
    printf("%d closed file ncid = %d\n", my_rank, ncid);
    
    return PIO_NOERR;
}

