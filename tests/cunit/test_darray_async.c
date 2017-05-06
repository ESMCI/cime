/*
 * This program tests darrays with async.
 *
 * Ed Hartnett, 5/4/17
 */
#include <pio.h>
#include <pio_tests.h>
#include <pio_internal.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 1

/* The name of this test. */
#define TEST_NAME "test_darray_async"

/* For 1-D use. */
#define NDIM1 1

/* For 2-D use. */
#define NDIM2 2

/* For 3-D use. */
#define NDIM3 3

/* For maplens of 2. */
#define MAPLEN2 2

/* Lengths of non-unlimited dimensions. */
#define LAT_LEN 2
#define LON_LEN 3

/* Name of test var. */
#define VAR_NAME "surface_temperature"

char dim_name[NDIM3][PIO_MAX_NAME + 1] = {"unlim", "lat", "lon"};

/* Length of the dimension. */
#define LEN3 3

/* Check the file that was created in this test. */
/* int check_darray_file(int iosysid, char *data_filename, int iotype, int my_rank) */
/* { */
/*     int ncid; */
/*     int dimid; */
/*     int varid; */
/*     float data_in[LEN3]; */
/*     int ret; */

/*     /\* Reopen the file. *\/ */
/*     if ((ret = PIOc_openfile(iosysid, &ncid, &iotype, data_filename, NC_NOWRITE))) */
/*         ERR(ret); */

/*     /\* Check the metadata. *\/ */
/*     if ((ret = PIOc_inq_varid(ncid, VAR_NAME, &varid))) */
/*         ERR(ret); */
/*     if ((ret = PIOc_inq_dimid(ncid, DIM_NAME, &dimid))) */
/*         ERR(ret); */

/*     /\* Check the data. *\/ */
/*     if ((ret = PIOc_get_var(ncid, varid, &data_in))) */
/*         ERR(ret); */
/*     for (int r = 1; r < TARGET_NTASKS; r++) */
/*         if (data_in[r - 1] != r * 10.0) */
/*             ERR(ret); */

/*     /\* Close the file. *\/ */
/*     if ((ret = PIOc_closefile(ncid))) */
/*         ERR(ret); */

/*     return 0; */
/* } */

/* Run a simple test using darrays with async. */
int run_darray_async_test(int iosysid, int my_rank, MPI_Comm test_comm,
                          int num_flavors, int *flavor)
{
    int ioid;
    int dim_len[NDIM3] = {NC_UNLIMITED, 2, 3};
    PIO_Offset elements_per_pe = LAT_LEN;
    PIO_Offset compdof[LAT_LEN] = {my_rank * 2 - 2, my_rank * 2 - 1};
    char decomp_filename[PIO_MAX_NAME + 1];
    int ret;

    sprintf(decomp_filename, "decomp_%s_rank_%d.nc", TEST_NAME, my_rank);

    /* Create the PIO decomposition for this test. */
    if ((ret = PIOc_init_decomp(iosysid, PIO_FLOAT, NDIM2, &dim_len[1], elements_per_pe,
                                compdof, &ioid, PIO_REARR_BOX, NULL, NULL)))
        ERR(ret);

    /* Write the decomp file (on appropriate tasks). */
    if ((ret = PIOc_write_nc_decomp(iosysid, decomp_filename, 0, ioid, NULL, NULL, 0)))
        return ret;

    for (int fmt = 0; fmt < num_flavors; fmt++)
    {
        int ncid;
        int dimid[NDIM3];
        int varid;
        char data_filename[PIO_MAX_NAME + 1];
        float my_data[LAT_LEN] = {my_rank * 10, my_rank * 10 + 1};

        /* For now, only serial iotypes work. Parallel coming soon! */
        if (flavor[fmt] == PIO_IOTYPE_PNETCDF || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
            continue;

        sprintf(data_filename, "data_%s_iotype_%d.nc", TEST_NAME, flavor[fmt]);

        /* Create sample output file. */
        if ((ret = PIOc_createfile(iosysid, &ncid, &flavor[fmt], data_filename,
                                   NC_CLOBBER)))
            ERR(ret);

        /* Define dimensions. */
        for (int d = 0; d < NDIM3; d++)
            if ((ret = PIOc_def_dim(ncid, dim_name[d], dim_len[d], &dimid[d])))
                ERR(ret);

        /* Define variable. */
        if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM3, dimid, &varid)))
            ERR(ret);

        /* End define mode. */
        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Set the record number. */
        if ((ret = PIOc_setframe(ncid, varid, 0)))
            ERR(ret);

        /* Write some data. */
        if ((ret = PIOc_write_darray(ncid, varid, ioid, elements_per_pe, my_data, NULL)))
            ERR(ret);

        /* Close the file. */
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

        /* Check the file for correctness. */
        /* if ((ret = check_darray_file(iosysid, data_filename, PIO_IOTYPE_NETCDF, my_rank))) */
        /*     ERR(ret); */

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
