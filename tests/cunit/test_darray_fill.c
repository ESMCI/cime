/*
 * Tests for PIO distributed arrays.
 *
 * @author Ed Hartnett
 * @date 4/21/18
 */
#include <config.h>
#include <pio.h>
#include <pio_internal.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_darray_fill"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 4

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

#define VAR_NAME "PIO_TF_test_var"
#define DIM_NAME "PIO_TF_test_dim"
#define FILL_VALUE_NAME "_FillValue"

/* Test with and without specifying a fill value to
 * PIOc_write_darray(). */
#define NUM_TEST_CASES_FILLVALUE 2

#define NDIM1 1
#define MAPLEN 7

/* Length of the dimensions in the sample data. */
int dim_len[NDIM1] = {28};

/* Run test for each of the rearrangers. */
#define NUM_REARRANGERS_TO_TEST 1

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
                              MIN_NTASKS, 4, &test_comm)))
        ERR(ERR_INIT);

    if ((ret = PIOc_set_iosystem_error_handling(PIO_DEFAULT, PIO_RETURN_ERROR, NULL)))
        return ret;

    /* Only do something on max_ntasks tasks. */
    if (my_rank < TARGET_NTASKS)
    {
        /* int rearranger[NUM_REARRANGERS_TO_TEST] = {PIO_REARR_BOX, PIO_REARR_SUBSET}; */
        int rearranger[NUM_REARRANGERS_TO_TEST] = {PIO_REARR_SUBSET};
        int iosysid;  /* The ID for the parallel I/O system. */
        int ioproc_stride = 1;    /* Stride in the mpi rank between io tasks. */
        int ioproc_start = 0;     /* Zero based rank of first processor to be used for I/O. */
        int wioid, rioid;
        int maplen = MAPLEN;
        MPI_Offset wcompmap[MAPLEN];
        MPI_Offset rcompmap[MAPLEN];
        int data[MAPLEN];
        int data_in[MAPLEN];
        int expected[MAPLEN];
        int fill_value_int = -2;
        int ret;      /* Return code. */

        /* Set up the compmaps. Don't forget these are 1-based
         * numbers, like in Fortran! */
        for (int i = 0; i < MAPLEN; i++)
        {
            wcompmap[i] = i % 2 ? my_rank * MAPLEN + i + 1 : 0; /* Even values missing. */
            rcompmap[i] = my_rank * MAPLEN + i + 1;
            data[i] = wcompmap[i];
            expected[i] = i % 2 ? my_rank * MAPLEN + i + 1 : fill_value_int; 
        }

        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);

        for (int r = 0; r < NUM_REARRANGERS_TO_TEST; r++)
        {
            /* Initialize the PIO IO system. This specifies how
             * many and which processors are involved in I/O. */
            if ((ret = PIOc_Init_Intracomm(test_comm, NUM_IO_PROCS, ioproc_stride, ioproc_start,
                                           rearranger[r], &iosysid)))
                return ret;

            /* /\* Initialize decompositions. *\/ */
            if ((ret = PIOc_InitDecomp(iosysid, PIO_INT, NDIM1, dim_len, maplen, wcompmap,
                                       &wioid, &rearranger[r], NULL, NULL)))
               return ret;
            if ((ret = PIOc_InitDecomp(iosysid, PIO_INT, NDIM1, dim_len, maplen, rcompmap,
                                       &rioid, &rearranger[r], NULL, NULL)))
               return ret;

            int ncid, dimid, varid;
            int iotype = PIO_IOTYPE_NETCDF4C;
            char filename[NC_MAX_NAME + 1];

            /* Put together filename. */
            sprintf(filename, "%s_%d.nc", TEST_NAME, iotype);
            
            /* Create file. */
            if ((ret = PIOc_createfile(iosysid, &ncid, &iotype, filename, NC_CLOBBER)))
                return ret;

            /* Define metadata. */
            if ((ret = PIOc_def_dim(ncid, DIM_NAME, dim_len[0], &dimid)))
                return ret;
            if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_INT, NDIM1, &dimid, &varid)))
                return ret;
            if ((ret = PIOc_put_att_int(ncid, varid, FILL_VALUE_NAME, PIO_INT, 1, &fill_value_int)))
                return ret;
            if ((ret = PIOc_enddef(ncid)))
                return ret;

            /* Write some data. */
            if ((ret = PIOc_write_darray(ncid, varid, wioid, MAPLEN, data, &fill_value_int)))
                return ret;
            if ((ret = PIOc_sync(ncid)))
                return ret;

            /* Read the data. */
            if ((ret = PIOc_read_darray(ncid, varid, rioid, MAPLEN, data_in)))
                return ret;

            /* Check results. */
            for (int j = 0; j < MAPLEN; j++)
            {
                if (data_in[j] != expected[j])
                    return ERR_AWFUL;
                printf("data_in[%d] = %d\n", j, data_in[j]);
            }
            
            /* Close file. */
            if ((ret = PIOc_closefile(ncid)))
                return ret;
            
            /* Free decompositions. */
            if ((ret = PIOc_freedecomp(iosysid, wioid)))
               return ret;
            if ((ret = PIOc_freedecomp(iosysid, rioid)))
               return ret;

            /* Finalize PIO system. */
            if ((ret = PIOc_finalize(iosysid)))
                return ret;

        } /* next rearranger */
    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);
    return 0;
}
