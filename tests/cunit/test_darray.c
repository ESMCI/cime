/*
 * Tests for PIO distributed arrays.
 *
 * Ed Hartnett, 2/16/17
 */
#include <pio.h>
#include <pio_internal.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_darray"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

/* The number of dimensions in the example data. In this test, we
 * are using three-dimensional data. */
#define NDIM 3

/* But sometimes we need arrays of the non-record dimensions. */
#define NDIM2 2

/* The length of our sample data along each dimension. */
#define X_DIM_LEN 4
#define Y_DIM_LEN 4

/* The number of timesteps of data to write. */
#define NUM_TIMESTEPS 2

/* The name of the variable in the netCDF output files. */
#define VAR_NAME "foo"

/* The dimension names. */
char dim_name[NDIM][PIO_MAX_NAME + 1] = {"timestep", "x", "y"};

/* Length of the dimensions in the sample data. */
int dim_len[NDIM] = {NC_UNLIMITED, X_DIM_LEN, Y_DIM_LEN};

/** 
 * Test the darray functionality. Create a netCDF file with 3
 * dimensions and 1 PIO_INT variable, and use darray to write some
 * data.
 *
 * @param iosysid the IO system ID.
 * @param ioid the ID of the decomposition.
 * @param num_flavors the number of IOTYPES available in this build.
 * @param flavor array of available iotypes.
 * @param my_rank rank of this task.
 * @returns 0 for success, error code otherwise.
*/
int test_darray(int iosysid, int ioid, int num_flavors, int *flavor, int my_rank)
{
    char filename[PIO_MAX_NAME + 1]; /* Name for the output files. */
    int dimids[NDIM];      /* The dimension IDs. */
    int ncid;      /* The ncid of the netCDF file. */
    int ncid2;     /* The ncid of the re-opened netCDF file. */
    int varid;     /* The ID of the netCDF varable. */
    int ret;       /* Return code. */
    PIO_Offset arraylen = 4;
    int fillvalue = NC_FILL_INT;
    int test_data[arraylen];
    int test_data_in[arraylen];

    /* Initialize some data. */
    for (int f = 0; f < arraylen; f++)
        test_data[f] = my_rank * 10 + f;

    /* Use PIO to create the example file in each of the four
     * available ways. */
    for (int fmt = 0; fmt < num_flavors; fmt++) 
    {
        /* Create the filename. */
        sprintf(filename, "data_%s_iotype_%d.nc", TEST_NAME, flavor[fmt]);

        /* Create the netCDF output file. */
        printf("rank: %d Creating sample file %s with format %d...\n", my_rank, filename,
               flavor[fmt]);
        if ((ret = PIOc_createfile(iosysid, &ncid, &flavor[fmt], filename, PIO_CLOBBER)))
            ERR(ret);

        /* Define netCDF dimensions and variable. */
        printf("%d Defining netCDF metadata...\n", my_rank);
        for (int d = 0; d < NDIM; d++)
            if ((ret = PIOc_def_dim(ncid, dim_name[d], (PIO_Offset)dim_len[d], &dimids[d])))
                ERR(ret);

        /* Define a variable. */
        if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_INT, NDIM, dimids, &varid)))
            ERR(ret);

        /* End define mode. */
        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Set the value of the record dimension. */
        if ((ret = PIOc_setframe(ncid, varid, 0)))
            ERR(ret);

        /* These should not work. */
        if (PIOc_write_darray(ncid + TEST_VAL_42, varid, ioid, arraylen, test_data, &fillvalue) != PIO_EBADID)
            ERR(ERR_WRONG);
        if (PIOc_write_darray(ncid, varid, ioid + TEST_VAL_42, arraylen, test_data, &fillvalue) != PIO_EBADID)
            ERR(ERR_WRONG);
        if (PIOc_write_darray(ncid, varid, ioid, arraylen + TEST_VAL_42, test_data, &fillvalue) != PIO_EINVAL)
            ERR(ERR_WRONG);

        /* Write the data. */
        if ((ret = PIOc_write_darray(ncid, varid, ioid, arraylen, test_data, &fillvalue)))
            ERR(ret);

        /* Close the netCDF file. */
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

        /* Reopen the file. */
        if ((ret = PIOc_openfile(iosysid, &ncid2, &flavor[fmt], filename, PIO_NOWRITE)))
            ERR(ret);

        /* These should not work. */
        if (PIOc_read_darray(ncid2 + TEST_VAL_42, varid, ioid, arraylen,
                             test_data_in) != PIO_EBADID)
            ERR(ERR_WRONG);
        if (PIOc_read_darray(ncid2, varid, ioid + TEST_VAL_42, arraylen,
                             test_data_in) != PIO_EBADID)
            ERR(ERR_WRONG);
        
        /* Read the data. */
        if ((ret = PIOc_read_darray(ncid2, varid, ioid, arraylen, test_data_in)))
            ERR(ret);

        /* Check the results. */
        for (int f = 0; f < arraylen; f++)
            if (test_data_in[f] != test_data[f])
                return ERR_WRONG;

        /* Try to write, but it won't work, because we opened file read-only. */
        if (PIOc_write_darray(ncid2, varid, ioid, arraylen, test_data, &fillvalue) != PIO_EPERM)
            ERR(ERR_WRONG);
        
        /* Close the netCDF file. */
        printf("%d Closing the sample data file...\n", my_rank);
        if ((ret = PIOc_closefile(ncid2)))
            ERR(ret);
    }
    return PIO_NOERR;
}

/**
 * Run all the tests. 
 *
 * @param iosysid the IO system ID.
 * @param num_flavors number of available iotypes in the build.
 * @param flavor pointer to array of the available iotypes.
 * @param my_rank rank of this task.
 * @param test_comm the communicator the test is running on.
 * @returns 0 for success, error code otherwise. 
 */
int test_all_darray(int iosysid, int num_flavors, int *flavor, int my_rank, MPI_Comm test_comm)
{
    int ioid;
    int my_test_size;
    char filename[NC_MAX_NAME + 1];
    int dim_len_2d[NDIM2] = {X_DIM_LEN, Y_DIM_LEN};
    int ret; /* Return code. */

    if ((ret = MPI_Comm_size(test_comm, &my_test_size)))
        MPIERR(ret);

    /* This will be our file name for writing out decompositions. */
    sprintf(filename, "%s_decomp_rank_%d_flavor_%d_.nc", TEST_NAME, my_rank, *flavor);

    printf("%d Testing darray.\n", my_rank);
        
    /* Decompose the data over the tasks. */
    if ((ret = create_decomposition_2d(TARGET_NTASKS, my_rank, iosysid, dim_len_2d, &ioid)))
        return ret;

    /* Run a simple darray test. */
    if ((ret = test_darray(iosysid, ioid, num_flavors, flavor, my_rank)))
        return ret;
    
    /* Free the PIO decomposition. */
    if ((ret = PIOc_freedecomp(iosysid, ioid)))
        ERR(ret);

    return PIO_NOERR;
}

/* Run tests for darray functions. */
int main(int argc, char **argv)
{
    int my_rank;
    int ntasks;
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    MPI_Comm test_comm; /* A communicator for this test. */
    int ret;         /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS,
                              MIN_NTASKS, 3, &test_comm)))
        ERR(ERR_INIT);

    if ((ret = PIOc_set_iosystem_error_handling(PIO_DEFAULT, PIO_RETURN_ERROR, NULL)))
        return ret;

    /* Only do something on max_ntasks tasks. */
    if (my_rank < TARGET_NTASKS)
    {
        int iosysid;  /* The ID for the parallel I/O system. */
        int ioproc_stride = 1;    /* Stride in the mpi rank between io tasks. */
        int ioproc_start = 0;     /* Zero based rank of first processor to be used for I/O. */
        int ret;      /* Return code. */
        
        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);
        printf("Runnings tests for %d flavors\n", num_flavors);

        /* Initialize the PIO IO system. This specifies how
         * many and which processors are involved in I/O. */
        if ((ret = PIOc_Init_Intracomm(test_comm, TARGET_NTASKS, ioproc_stride,
                                       ioproc_start, PIO_REARR_SUBSET, &iosysid)))
            return ret;

        /* Run tests. */
        printf("%d Running tests...\n", my_rank);
        if ((ret = test_all_darray(iosysid, num_flavors, flavor, my_rank, test_comm)))
            return ret;

        /* Finalize PIO system. */
        if ((ret = PIOc_finalize(iosysid)))
            return ret;

    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);
    return 0;
}
