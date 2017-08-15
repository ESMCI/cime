/*
 * This program tests darrays with async and non-async. 
 *
 * @author Ed Hartnett
 * @date 7/8/17
 */
#include <config.h>
#include <pio.h>
#include <pio_tests.h>
#include <pio_internal.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 1

/* The name of this test. */
#define TEST_NAME "test_darray_2sync"

#define NUM_IO_PROCS 1
#define NUM_COMPUTATION_PROCS 3
#define COMPONENT_COUNT 1

#define DIM_NAME "simple_dim"
#define DIM_LEN 6
#define VAR_NAME "simple_var"
#define NDIM1 1

/* Tests for darray that can run on both async and non-async
 * iosysids. This is a deliberately simple test, to make debugging
 * easier. */
int darray_simple_test(int iosysid, int my_rank, int num_iotypes, int *iotype,
                       int async)
{
    /* For each of the available IOtypes... */
    for (int iot = 0; iot < num_iotypes; iot++)
    {
        int ncid;
        int dimid;
        int varid;
        int ioid;
        char filename[PIO_MAX_NAME + 1];
        int ret;

        /* Create test filename. */
        sprintf(filename, "%s_simple_async_%d_iotype_%d.nc", TEST_NAME, async, iotype[iot]);

        /* Create the test file. */
        if ((ret = PIOc_createfile(iosysid, &ncid, &iotype[iot], filename, PIO_CLOBBER)))
            ERR(ret);

        /* Define a dimension. */
        if ((ret = PIOc_def_dim(ncid, DIM_NAME, DIM_LEN, &dimid)))
            ERR(ret);

        /* Define a 1D var. */
        if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_INT, NDIM1, &dimid, &varid)))
            ERR(ret);

        /* End define mode. */
        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Create the PIO decomposition for this test. */
        int elements_per_pe = 2;
        PIO_Offset compdof[elements_per_pe];
        int gdimlen = DIM_LEN;
        if (my_rank == 0)
        {
            /* Only non-async code will reach here, for async, task 0
             * does not run this function. */
            compdof[0] = -1;
            compdof[1] = -1;
        }
        else
        {
            compdof[0] = (my_rank - 1) * elements_per_pe;
            compdof[1] = compdof[0] + 1;
        }

        /* Initialize the decomposition. */
        if ((ret = PIOc_init_decomp(iosysid, PIO_INT, NDIM1, &gdimlen, elements_per_pe,
                                    compdof, &ioid, PIO_REARR_BOX, NULL, NULL)))
            ERR(ret);

        /* Set the record number for the unlimited dimension. */
        if ((ret = PIOc_setframe(ncid, varid, 0)))
            ERR(ret);

        /* Write the data. There are 3 procs with data, each writes 2
         * values. */
        int arraylen = 2;
        int test_data[2] = {my_rank, -my_rank};
        if ((ret = PIOc_write_darray(ncid, varid, ioid, arraylen, test_data, NULL)))
            ERR(ret);

        /* Free decomposition. */
        if ((ret = PIOc_freedecomp(iosysid, ioid)))
            ERR(ret);

        /* Close the test file. */
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

        /* /\* Check the file. *\/ */
        /* { */
        /*     int ncid2; */
        /*     int data_in[elements_per_pe * NUM_COMPUTATION_PROCS]; */

        /*     /\* Reopen the file. *\/ */
        /*     if ((ret = PIOc_openfile2(iosysid, &ncid2, &iotype[iot], filename, PIO_NOWRITE))) */
        /*         ERR(ret); */

        /*     /\* Read the data. *\/ */
        /*     if ((ret = PIOc_get_var_int(ncid2, 0, data_in))) */
        /*         ERR(ret); */
        /*     if (my_rank && data_in[0] != 1 && data_in[1] != -1 && data_in[2] != 2 && */
        /*         data_in[3] != -2 && data_in[4] != 3 && data_in[5] != -3) */
        /*         ERR(ret); */

        /*     /\* Close the test file. *\/ */
        /*     if ((ret = PIOc_closefile(ncid2))) */
        /*         ERR(ret); */
        /* } */
    }
    
    return PIO_NOERR;
}

/* This function can be run for both async and non async. It runs all
 * the test functions. */
int run_darray_tests(int iosysid, int my_rank, int num_iotypes, int *iotype, int async)
{
    int ret;
    
    /* Run the simple darray test. */
    if ((ret = darray_simple_test(iosysid, my_rank, num_iotypes, iotype, async)))
        ERR(ret);
        
    return PIO_NOERR;
}

/* Initialize with task 0 as IO task, tasks 1-3 as a
 * computation component. */
int run_async_tests(MPI_Comm test_comm, int my_rank, int num_iotypes, int *iotype)
{
    int iosysid;
    int num_computation_procs = NUM_COMPUTATION_PROCS;
    MPI_Comm io_comm;              /* Will get a duplicate of IO communicator. */
    MPI_Comm comp_comm[COMPONENT_COUNT]; /* Will get duplicates of computation communicators. */
    int mpierr;
    int ret;

    if ((ret = PIOc_init_async(test_comm, NUM_IO_PROCS, NULL, COMPONENT_COUNT,
                               &num_computation_procs, NULL, &io_comm, comp_comm,
                               PIO_REARR_BOX, &iosysid)))
        ERR(ERR_INIT);
        
    /* This code runs only on computation components. */
    if (my_rank)
    {
        /* Run the tests. */
        if ((ret = run_darray_tests(iosysid, my_rank, num_iotypes, iotype, 1)))
            ERR(ret);

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

    return PIO_NOERR;
}    

/* Initialize with task 0 as IO task, tasks 1-3 as a
 * computation component. */
int run_noasync_tests(MPI_Comm test_comm, int my_rank, int num_iotypes, int *iotype)
{
    int iosysid;
    int stride = 1;
    int base = 1;
    int ret;

    /* Initialize PIO system. */
    if ((ret = PIOc_Init_Intracomm(test_comm, NUM_IO_PROCS, stride, base, PIO_REARR_BOX,
                                   &iosysid)))
        ERR(ret);

    /* Run the tests. */
    if ((ret = run_darray_tests(iosysid, my_rank, num_iotypes, iotype, 1)))
        ERR(ret);
    
    /* Finalize PIO system. */
    if ((ret = PIOc_finalize(iosysid)))
        return ret;
            
    return PIO_NOERR;
}    

/* Run Tests for darray functions. */
int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks;  /* Number of processors involved in current execution. */
    int num_iotypes; /* Number of PIO netCDF iotypes in this build. */
    int iotype[NUM_IOTYPES]; /* iotypes for the supported netCDF IO iotypes. */
    MPI_Comm test_comm; /* A communicator for this test. */
    int ret;     /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS,
                              TARGET_NTASKS, -1, &test_comm)))
        ERR(ERR_INIT);
    if ((ret = PIOc_set_iosystem_error_handling(PIO_DEFAULT, PIO_RETURN_ERROR, NULL)))
        return ret;

    /* Figure out iotypes. */
    if ((ret = get_iotypes(&num_iotypes, iotype)))
        ERR(ret);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
        if ((ret = run_async_tests(test_comm, my_rank, num_iotypes, iotype)))
            ERR(ret);
        
        if ((ret = run_noasync_tests(test_comm, my_rank, num_iotypes, iotype)))
            ERR(ret);
        
    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
