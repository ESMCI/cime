/*
 * This program tests darrays with async. This tests uses many types
 * of vars and iodesc's, all in the same file.
 *
 * Ed Hartnett, 5/10/17
 */
#include <pio.h>
#include <pio_tests.h>
#include <pio_internal.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 1

/* The name of this test. */
#define TEST_NAME "test_darray_async_many"

/* For 1-D use. */
#define NDIM1 1

/* For 2-D use. */
#define NDIM2 2

/* For 3-D use. */
#define NDIM3 3

/* For 4-D use. */
#define NDIM4 4

/* For maplens of 2. */
#define MAPLEN2 2

/* Lengths of non-unlimited dimensions. */
#define LAT_LEN 2
#define LON_LEN 3

/* Number of vars in test file. */
#ifdef _NETCDF4
#define NVAR 4
#else
#define NVAR 2
#endif /* _NETCDF4 */

/* Number of records written for record var. */
#define NREC 3

/* Names of the dimensions. */
char dim_name[NDIM4][PIO_MAX_NAME + 1] = {"time", "vert_level", "lat", "lon"};

/* Check the file that was created in this test. */
int check_darray_file(int iosysid, char *data_filename, int iotype, int my_rank)
{
    int ncid;
    int varid[NVAR] = {0, 1};
    void *data_in;
    void *data_in_norec;
    int ret;

    /* Reopen the file. */
    if ((ret = PIOc_openfile(iosysid, &ncid, &iotype, data_filename, NC_NOWRITE)))
        ERR(ret);

    /* Allocate memory to read data. */
    if (!(data_in = malloc(LAT_LEN * LON_LEN * sizeof(int) * NREC)))
        ERR(PIO_ENOMEM);
    if (!(data_in_norec = malloc(LAT_LEN * LON_LEN * sizeof(int))))
        ERR(PIO_ENOMEM);

    /* Read the record data. The values we expect are: 10, 11, 20, 21, 30,
     * 31, in each of two records. */
    if ((ret = PIOc_get_var(ncid, varid[0], data_in)))
        ERR(ret);

    /* Read the non-record data. The values we expect are: 10, 11, 20, 21, 30,
     * 31. */
    if ((ret = PIOc_get_var(ncid, varid[1], data_in_norec)))
        ERR(ret);

    /* Check the results. */
    for (int r = 0; r < LAT_LEN * LON_LEN * NREC; r++)
    {
        int tmp_r = r % (LAT_LEN * LON_LEN);
        if (((signed char *)data_in)[r] != (tmp_r/2 + 1) * 10.0 + tmp_r % 2)
            ERR(ret);
    }

    /* Check the results. */
    for (int r = 0; r < LAT_LEN * LON_LEN; r++)
        if (((signed char *)data_in_norec)[r] != (r/2 + 1) * 20.0 + r%2)
            ERR(ret);

    /* Free resources. */
    free(data_in);
    free(data_in_norec);

    /* Close the file. */
    if ((ret = PIOc_closefile(ncid)))
        ERR(ret);

    return 0;
}

/* Run a simple test using darrays with async. */
int run_darray_async_test(int iosysid, int my_rank, MPI_Comm test_comm,
                          int num_flavors, int *flavor)
{
    int ioid;
    int dim_len[NDIM4] = {NC_UNLIMITED, 2, 2, 3};
    int dimids_3d[NDIM3] = {0, 2, 3};
    int dimids_2d[NDIM2] = {2, 3};
    PIO_Offset elements_per_pe = LAT_LEN;
    PIO_Offset compdof[LAT_LEN] = {my_rank * 2 - 2, my_rank * 2 - 1};
    char decomp_filename[PIO_MAX_NAME + 1];
    int piotype = PIO_BYTE;
    int ret;

    sprintf(decomp_filename, "decomp_%s_rank_%d.nc", TEST_NAME, my_rank);

    /* Create the PIO decomposition for this test. */
    if ((ret = PIOc_init_decomp(iosysid, PIO_BYTE, NDIM2, &dim_len[2], elements_per_pe,
                                compdof, &ioid, PIO_REARR_BOX, NULL, NULL)))
        ERR(ret);

    /* Write the decomp file (on appropriate tasks). */
    if ((ret = PIOc_write_nc_decomp(iosysid, decomp_filename, 0, ioid, NULL, NULL, 0)))
        return ret;

    for (int fmt = 0; fmt < num_flavors; fmt++)
    {
        int ncid;
        int dimid[NDIM3];
        int varid[NVAR];
        char data_filename[PIO_MAX_NAME + 1];
        signed char my_data_byte[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1};
        char my_data_char[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1};
        /* short my_data_short[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
        /* int my_data_int[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
/*         float my_data_float[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
/*         double my_data_double[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
/* #ifdef _NETCDF4 */
/*         unsigned char my_data_ubyte[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
/*         unsigned short my_data_ushort[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
/*         unsigned int my_data_uint[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
/*         long long my_data_int64[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
/*         unsigned long long my_data_uint64[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1}; */
/* #endif /\* _NETCDF4 *\/ */
        signed char my_data_byte_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1};
        char my_data_char_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1};
/*         short my_data_short_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
        /* int my_data_int_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
/*         float my_data_float_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
/*         double my_data_double_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
/* #ifdef _NETCDF4 */
/*         unsigned char my_data_ubyte_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
/*         unsigned short my_data_ushort_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
/*         unsigned int my_data_uint_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
/*         long long my_data_int64_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
/*         unsigned long long my_data_uint64_norec[LAT_LEN] = {my_rank * 20, my_rank * 20 + 1}; */
/* #endif /\* _NETCDF4 *\/ */

        /* For now, only serial iotypes work. Parallel coming soon! */
        if (flavor[fmt] == PIO_IOTYPE_PNETCDF || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
            continue;

        /* Create sample output file. */
        sprintf(data_filename, "data_%s_iotype_%d_piotype_%d.nc", TEST_NAME, flavor[fmt],
                piotype);
        if ((ret = PIOc_createfile(iosysid, &ncid, &flavor[fmt], data_filename,
                                   NC_CLOBBER)))
            ERR(ret);

        /* Define dimensions. */
        for (int d = 0; d < NDIM4; d++)
            if ((ret = PIOc_def_dim(ncid, dim_name[d], dim_len[d], &dimid[d])))
                ERR(ret);

        /* Define variables. */
        char var_name[PIO_MAX_NAME + 1];
        char var_norec_name[PIO_MAX_NAME + 1];
        int var_type[NVAR] = {PIO_BYTE, PIO_BYTE, PIO_CHAR, PIO_CHAR};
        for (int v = 0; v < NVAR; v += 2)
        {
            sprintf(var_name, "var_%d", v);
            sprintf(var_norec_name, "var_norec_%d", v);
            if ((ret = PIOc_def_var(ncid, var_name, var_type[v], NDIM3, dimids_3d, &varid[v])))
                ERR(ret);
            if ((ret = PIOc_def_var(ncid, var_norec_name, var_type[v + 1], NDIM2, dimids_2d,
                                    &varid[v + 1])))
            ERR(ret);
        }

        /* End define mode. */
        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Set the record number for the record var. */
        if ((ret = PIOc_setframe(ncid, varid[0], 0)))
            ERR(ret);

        /* Write some data to the record vars. */
        if ((ret = PIOc_write_darray(ncid, varid[0], ioid, elements_per_pe, my_data_byte, NULL)))
            ERR(ret);

        /* if ((ret = PIOc_write_darray(ncid, varid[2], ioid, elements_per_pe, my_data_char, NULL))) */
        /*     ERR(ret); */
        
        /* Write some data to the non-record vars. */
        if ((ret = PIOc_write_darray(ncid, varid[1], ioid, elements_per_pe, my_data_byte_norec, NULL)))
            ERR(ret);

        if ((ret = PIOc_write_darray(ncid, varid[3], ioid, elements_per_pe, my_data_char_norec, NULL)))
            ERR(ret);

        /* Sync the file. */
        if ((ret = PIOc_sync(ncid)))
            ERR(ret);

        /* Increment the record number for the record var. */
        if ((ret = PIOc_advanceframe(ncid, varid[0])))
            ERR(ret);

        /* Write another record. */
        if ((ret = PIOc_write_darray(ncid, varid[0], ioid, elements_per_pe, my_data_byte, NULL)))
            ERR(ret);

        /* Sync the file. */
        if ((ret = PIOc_sync(ncid)))
            ERR(ret);

        /* Increment the record number for the record var. */
        if ((ret = PIOc_advanceframe(ncid, varid[0])))
            ERR(ret);

        /* Write a third record. */
        if ((ret = PIOc_write_darray(ncid, varid[0], ioid, elements_per_pe, my_data_byte, NULL)))
            ERR(ret);

        /* Close the file. */
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

        /* Check the file for correctness. */
        if ((ret = check_darray_file(iosysid, data_filename, PIO_IOTYPE_NETCDF, my_rank)))
            ERR(ret);

    } /* next iotype */

    /* Free the decomposition. */
    if ((ret = PIOc_freedecomp(iosysid, ioid)))
        ERR(ret);

    return 0;
}

/* Run Tests for pio_spmd.c functions. */
int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks;  /* Number of processors involved in current execution. */
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    MPI_Comm test_comm; /* A communicator for this test. */
    int ret;     /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS,
                              TARGET_NTASKS, 3, &test_comm)))
        ERR(ERR_INIT);
    if ((ret = PIOc_set_iosystem_error_handling(PIO_DEFAULT, PIO_RETURN_ERROR, NULL)))
        return ret;

    /* Figure out iotypes. */
    if ((ret = get_iotypes(&num_flavors, flavor)))
        ERR(ret);
    printf("Runnings tests for %d flavors\n", num_flavors);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
        int iosysid;

        /* Initialize with task 0 as IO task, tasks 1-3 as a
         * computation component. */
#define NUM_IO_PROCS 1
#define NUM_COMPUTATION_PROCS 3
#define COMPONENT_COUNT 1
        int num_computation_procs = NUM_COMPUTATION_PROCS;
        MPI_Comm io_comm;              /* Will get a duplicate of IO communicator. */
        MPI_Comm comp_comm[COMPONENT_COUNT]; /* Will get duplicates of computation communicators. */
        int mpierr;

        if ((ret = PIOc_init_async(test_comm, NUM_IO_PROCS, NULL, COMPONENT_COUNT,
                                   &num_computation_procs, NULL, &io_comm, comp_comm,
                                   PIO_REARR_BOX, &iosysid)))
            ERR(ERR_INIT);
        
        /* This code runs only on computation components. */
        if (my_rank)
        {
            /* Run the simple darray async test. */
            if ((ret = run_darray_async_test(iosysid, my_rank, test_comm, num_flavors, flavor)))
                return ret;
            
            /* Finalize PIO system. */
            if ((ret = PIOc_finalize(iosysid)))
                return ret;
            
            /* Free the computation conomponent communicator. */
            if ((mpierr = MPI_Comm_free(comp_comm)))
                MPIERR(mpierr);
        }
        else
        {
            /* Free the IO communicator. */
            if ((mpierr = MPI_Comm_free(&io_comm)))
                MPIERR(mpierr);
        }
    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
