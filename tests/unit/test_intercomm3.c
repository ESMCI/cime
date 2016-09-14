/**
 * @file Tests for PIOc_Intercomm. This tests basic asynch I/O capability.
 * @author Ed Hartnett
 *
 * To run with valgrind, use this command:
 * <pre>mpiexec -n 4 valgrind -v --leak-check=full --suppressions=../../../tests/unit/valsupp_test.supp
 * --error-exitcode=99 --track-origins=yes ./test_intercomm3</pre>
 *
 */
#include <pio.h>
#include <pio_tests.h>

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 2

/* Number of computational components to create. */
#define COMPONENT_COUNT 2

/** The number of possible output netCDF output flavors available to
 * the ParallelIO library. */
#define NUM_NETCDF_FLAVORS 4

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_intercomm3"

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

/** The name of the global attribute in the netCDF output file. */
#define FIRST_ATT_NAME "willy_gatt_test_intercomm3"
#define ATT_NAME "gatt_test_intercomm3"
#define SHORT_ATT_NAME "short_gatt_test_intercomm3"
#define FLOAT_ATT_NAME "float_gatt_test_intercomm3"
#define DOUBLE_ATT_NAME "double_gatt_test_intercomm3"

/** The value of the global attribute in the netCDF output file. */
#define ATT_VALUE 42

/** Run Tests for Init_Intercomm
 *
 * @param argc argument count
 * @param argv array of arguments
 */
int
main(int argc, char **argv)
{
    int verbose = 1;

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
    char base_filename[NUM_NETCDF_FLAVORS][NC_MAX_NAME + 1] = {"test_intercomm3_pnetcdf",
							       "test_intercomm3_classic",
							       "test_intercomm3_serial4",
							       "test_intercomm3_parallel4"};

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

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS)))
	ERR(ERR_INIT);

    /* How many processors will be used for our IO and 2 computation components. */
    int num_procs[COMPONENT_COUNT + 1] = {2, 1, 1};

    /* Is the current process a computation task? */
    int comp_task = my_rank < 2 ? 0 : 1;

    /* Index of computation task in iosysid array. Varies by rank and
     * does not apply to IO component processes. */
    int my_comp_idx = comp_task ? my_rank - 2 : -1;

    /* Initialize the IO system. */
    if ((ret = PIOc_Init_Async(MPI_COMM_WORLD, NUM_IO_PROCS, NULL, COMPONENT_COUNT,
			       num_procs, NULL, iosysid)))
	ERR(ERR_AWFUL);

    /* All the netCDF calls are only executed on the computation
     * tasks. The IO tasks have not returned from PIOc_Init_Intercomm,
     * and when the do, they should go straight to finalize. */
    if (comp_task)
    {
    	for (int fmt = 1; fmt < NUM_NETCDF_FLAVORS - 2; fmt++)
    	{
    	    int ncid, varid, dimid;
    	    PIO_Offset start[NDIM], count[NDIM] = {0};
    	    int data[DIM_LEN];
	    char filename[NC_MAX_NAME + 1];

	    /* Create a filename for this computation component. */
	    sprintf(filename, "%s_%d.nc", base_filename[fmt], my_comp_idx);

    	    /* Create a netCDF file with one dimension and one variable. */
    	    if (verbose)
    	    	printf("%d test_intercomm3 creating file %s\n", my_rank, filename);
    	    if ((ret = PIOc_createfile(iosysid[my_comp_idx], &ncid, &format[fmt], filename,
    	    			       NC_CLOBBER)))
    	    	ERR(ret);
    	    if (verbose)
    	    	printf("%d test_intercomm3 file created ncid = %d\n", my_rank, ncid);

    	    /* /\* End define mode, then re-enter it. *\/ */
    	    if ((ret = PIOc_enddef(ncid)))
    	    	ERR(ret);
    	    if (verbose)
    	    	printf("%d test_intercomm3 calling redef\n", my_rank);
    	    if ((ret = PIOc_redef(ncid)))
    	    	ERR(ret);

    	    /* Test the inq_format function. */
    	    int myformat;
    	    if ((ret = PIOc_inq_format(ncid, &myformat)))
    	    	ERR(ret);
    	    if ((format[fmt] == PIO_IOTYPE_PNETCDF || format[fmt] == PIO_IOTYPE_NETCDF) &&
    	    	myformat != 1)
    	    	ERR(ERR_AWFUL);
    	    else if ((format[fmt] == PIO_IOTYPE_NETCDF4C || format[fmt] == PIO_IOTYPE_NETCDF4P) &&
    	    	     myformat != 3)
    	    	ERR(ERR_AWFUL);

    	    /* Test the inq_type function for atomic types. */
    	    char type_name[NC_MAX_NAME + 1];
    	    PIO_Offset type_size;
    	    #define NUM_TYPES 11
    	    nc_type xtype[NUM_TYPES] = {NC_CHAR, NC_BYTE, NC_SHORT, NC_INT, NC_FLOAT, NC_DOUBLE,
    	    				NC_UBYTE, NC_USHORT, NC_UINT, NC_INT64, NC_UINT64};
    	    int type_len[NUM_TYPES] = {1, 1, 2, 4, 4, 8, 1, 2, 4, 8, 8};
    	    int max_type = format[fmt] == PIO_IOTYPE_NETCDF ? NC_DOUBLE : NC_UINT64;
    	    for (int i = 0; i < max_type; i++)
    	    {
    	    	if ((ret = PIOc_inq_type(ncid, xtype[i], type_name, &type_size)))
    	    	    ERR(ret);
    	    	if (type_size != type_len[i])
    	    	    ERR(ERR_AWFUL);
    	    }

    	    /* Define a dimension. */
    	    char dimname2[NC_MAX_NAME + 1];
    	    if (verbose)
    	    	printf("%d test_intercomm3 defining dimension %s\n", my_rank, DIM_NAME);
    	    if ((ret = PIOc_def_dim(ncid, FIRST_DIM_NAME, DIM_LEN, &dimid)))
    	    	ERR(ret);
    	    if ((ret = PIOc_inq_dimname(ncid, 0, dimname2)))
    	    	ERR(ret);
    	    if (strcmp(dimname2, FIRST_DIM_NAME))
    	    	ERR(ERR_WRONG);
    	    if ((ret = PIOc_rename_dim(ncid, 0, DIM_NAME)))
    	    	ERR(ret);

    	    /* Define a 1-D variable. */
    	    char varname2[NC_MAX_NAME + 1];
    	    if (verbose)
    	    	printf("%d test_intercomm3 defining variable %s\n", my_rank, VAR_NAME);
    	    if ((ret = PIOc_def_var(ncid, FIRST_VAR_NAME, NC_INT, NDIM, &dimid, &varid)))
    	    	ERR(ret);
    	    if ((ret = PIOc_inq_varname(ncid, 0, varname2)))
    	    	ERR(ret);
    	    if (strcmp(varname2, FIRST_VAR_NAME))
    	    	ERR(ERR_WRONG);
    	    if ((ret = PIOc_rename_var(ncid, 0, VAR_NAME)))
    	    	ERR(ret);

    	    /* char *buf111 = malloc(19999); */

    	    /* /\* Add a global attribute. *\/ */
    	    /* if (verbose) */
    	    /* 	printf("%d test_intercomm3 writing attributes %s\n", my_rank, ATT_NAME); */
    	    /* int att_data = ATT_VALUE; */
    	    /* short short_att_data = ATT_VALUE; */
    	    /* float float_att_data = ATT_VALUE; */
    	    /* double double_att_data = ATT_VALUE; */
    	    /* char attname2[NC_MAX_NAME + 1]; */
    	    /* /\* Write an att and rename it. *\/ */
    	    /* if ((ret = PIOc_put_att_int(ncid, NC_GLOBAL, FIRST_ATT_NAME, NC_INT, 1, &att_data))) */
    	    /* 	ERR(ret); */
    	    /* if ((ret = PIOc_inq_attname(ncid, NC_GLOBAL, 0, attname2))) */
    	    /* 	ERR(ret); */
    	    /* if (strcmp(attname2, FIRST_ATT_NAME)) */
    	    /* 	ERR(ERR_WRONG); */
    	    /* if ((ret = PIOc_rename_att(ncid, NC_GLOBAL, FIRST_ATT_NAME, ATT_NAME))) */
    	    /* 	ERR(ret); */

    	    /* /\* Write an att and delete it. *\/ */
    	    /* nc_type myatttype; */
    	    /* if ((ret = PIOc_put_att_int(ncid, NC_GLOBAL, FIRST_ATT_NAME, NC_INT, 1, &att_data))) */
    	    /* 	ERR(ret); */
    	    /* if ((ret = PIOc_del_att(ncid, NC_GLOBAL, FIRST_ATT_NAME))) */
    	    /* 	ERR(ret); */
    	    /* /\* if ((ret = PIOc_inq_att(ncid, NC_GLOBAL, FIRST_ATT_NAME, NULL, NULL)) != PIO_ENOTATT) *\/ */
    	    /* /\* { *\/ */
    	    /* /\* 	printf("ret = %d\n", ret); *\/ */
    	    /* /\* 	ERR(ERR_AWFUL); *\/ */
    	    /* /\* } *\/ */

    	    /* /\* Write some atts of different types. *\/ */
    	    /* if ((ret = PIOc_put_att_short(ncid, NC_GLOBAL, SHORT_ATT_NAME, NC_SHORT, 1, &short_att_data))) */
    	    /* 	ERR(ret); */
    	    /* if ((ret = PIOc_put_att_float(ncid, NC_GLOBAL, FLOAT_ATT_NAME, NC_FLOAT, 1, &float_att_data))) */
    	    /* 	ERR(ret); */
    	    /* if ((ret = PIOc_put_att_double(ncid, NC_GLOBAL, DOUBLE_ATT_NAME, NC_DOUBLE, 1, &double_att_data))) */
    	    /* 	ERR(ret); */

    	    /* End define mode. */
    	    if (verbose)
    	    	printf("%d test_intercomm3 ending define mode ncid = %d\n", my_rank, ncid);
    	    if ((ret = PIOc_enddef(ncid)))
    	    	ERR(ret);
	    printf("%d test_intercomm3 define mode ended ncid = %d\n", my_rank, ncid);
	    
    	    /* /\* Write some data. For the PIOc_put/get functions, all */
    	    /*  * data must be on compmaster before the function is */
    	    /*  * called. Only compmaster's arguments are passed to the */
    	    /*  * async msg handler. All other computation tasks are */
    	    /*  * ignored. *\/ */
    	    /* for (int i = 0; i < DIM_LEN; i++) */
    	    /* 	data[i] = i; */
    	    /* if (verbose) */
    	    /* 	printf("%d test_intercomm3 writing data\n", my_rank); */
    	    /* if (verbose) */
    	    /* 	printf("%d test_intercomm3 writing data\n", my_rank); */
    	    /* start[0] = 0; */
    	    /* count[0] = DIM_LEN; */
    	    /* if ((ret = PIOc_put_vars_tc(ncid, varid, start, count, NULL, NC_INT, data))) */
    	    /* 	ERR(ret); */

    	    /* Close the file. */
    	    if (verbose)
    	    	printf("%d test_intercomm3 closing file ncid = %d\n", my_rank, ncid);
    	    if ((ret = PIOc_closefile(ncid)))
    	    	ERR(ret);
	    printf("%d test_intercomm3 closed file ncid = %d\n", my_rank, ncid);	    

    	    /* /\* /\\* Check the file for correctness. *\\/ *\/ */
    	    /* /\* if ((ret = check_file(iosysid, format[fmt], filename[fmt], my_rank, verbose))) *\/ */
    	    /* /\* 	ERR(ret); *\/ */

    	    /* /\* Now delete the file. *\/ */
    	    /* /\* if ((ret = PIOc_deletefile(iosysid, filename[fmt]))) *\/ */
    	    /* /\* 	ERR(ret); *\/ */
    	    /* /\* if ((ret = PIOc_openfile(iosysid, &ncid, &format[fmt], filename[fmt], *\/ */
    	    /* /\* 			     NC_NOWRITE)) != PIO_ENFILE) *\/ */
    	    /* /\* 	ERR(ERR_AWFUL); *\/ */

    	} /* next netcdf format flavor */

	/* If I don't sleep here for a second, there are problems. */
	sleep(2);

	/* Finalize the IO system. Only call this from the computation tasks. */
	if (verbose)
	    printf("%d test_intercomm3 Freeing PIO resources\n", my_rank);
	for (int c = 0; c < COMPONENT_COUNT; c++)
	{
	    if ((ret = PIOc_finalize(iosysid[c])))
		ERR(ret);
	    printf("%d test_intercomm3 PIOc_finalize completed for iosysid = %d\n", my_rank, iosysid[c]);
	}
    } /* endif comp_task */

    /* Wait for everyone to catch up. */
    printf("%d %s waiting for all processes!\n", my_rank, TEST_NAME);
    MPI_Barrier(MPI_COMM_WORLD);

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
	ERR(ERR_AWFUL);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
