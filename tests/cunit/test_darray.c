/* Tests for darray functions.
 *
 * Ed Hartnett
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_darray"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

#define NDIM 1
#define DIM_LEN 4
#define VAR_NAME "foo"
#define DIM_NAME "dim"

/* Create the decomposition to divide the data between the 4 tasks. */
int create_decomposition(int ntasks, int my_rank, int iosysid, int *ioid)
{
    PIO_Offset elements_per_pe;     /* Array elements per processing unit. */
    PIO_Offset *compdof;  /* The decomposition mapping. */
    int dim_len[NDIM] = {DIM_LEN};
    int ret;

    /* How many data elements per task? */
    elements_per_pe = DIM_LEN / ntasks;

    /* Allocate space for the decomposition array. */
    if (!(compdof = malloc(elements_per_pe * sizeof(PIO_Offset))))
        return PIO_ENOMEM;

    /* Describe the decomposition. This is a 1-based array, so add 1! */
    for (int i = 0; i < elements_per_pe; i++)
        compdof[i] = my_rank * elements_per_pe + i + 1;

    /* Create the PIO decomposition for this test. */
    printf("%d Creating decomposition elements_per_pe = %d\n", my_rank, elements_per_pe);
    if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, NDIM, dim_len, (PIO_Offset)elements_per_pe,
                               compdof, ioid, NULL, NULL, NULL)))
        ERR(ret);

    printf("%d decomposition initialized.", my_rank);

    /* Free the mapping. */
    free(compdof);

    return 0;
}

/* Check the contents of the test file. */
int check_file(int iosysid, int ntasks, int my_rank, char *filename)
{
    int ncid;
    int ndims, nvars, ngatts, unlimdimid;
    char dim_name_in[NC_MAX_NAME + 1];
    PIO_Offset dim_len_in;
    PIO_Offset arraylen = 1;
    float data_in;
    int ioid;
    int ret;

    assert(filename);

    /* Open the file. */
    if ((ret = PIOc_open(iosysid, filename, NC_NOWRITE, &ncid)))
        return ret;

    /* Check metadata. */
    if ((ret = PIOc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid)))
        return ret;
    if (ndims != 1 || nvars != 1 || ngatts != 0 || unlimdimid != -1)
        return ERR_WRONG;
    if ((ret = PIOc_inq_dim(ncid, 0, dim_name_in, &dim_len_in)))
        return ret;
    if (strcmp(dim_name_in, DIM_NAME) || dim_len_in != DIM_LEN)
        return ERR_WRONG;

    /* Decompose the data over the tasks. */
    if ((ret = create_decomposition(ntasks, my_rank, iosysid, &ioid)))
        return ret;

    /* Read data. */
    if ((ret = PIOc_read_darray(ncid, 0, ioid, arraylen, &data_in)))
        return ret;

    /* Check data. */
    if (data_in != my_rank * 10)
        return ERR_WRONG;

    /* Close the file. */
    if ((ret = PIOc_closefile(ncid)))
        return ret;

    /* Free the PIO decomposition. */
    if ((ret = PIOc_freedecomp(iosysid, ioid)))
        ERR(ret);

    return PIO_NOERR;
}

/* Test the darray functionality. */
int test_darray(int iosysid, int ioid, int num_flavors, int *flavor, int my_rank)
{
    char filename[NC_MAX_NAME + 1]; /* Name for the output files. */
    int dim_len[NDIM] = {DIM_LEN}; /* Length of the dimensions in the sample data. */
    int dimids[NDIM];      /* The dimension IDs. */
    int ncid;      /* The ncid of the netCDF file. */
    int varid;     /* The ID of the netCDF varable. */
    int ret;       /* Return code. */
    
    /* Use PIO to create the example file in each of the four
     * available ways. */
    for (int fmt = 0; fmt < num_flavors; fmt++)
    {
        /* Create the filename. */
        sprintf(filename, "%s_%d.nc", TEST_NAME, flavor[fmt]);

        /* Create the netCDF output file. */
        printf("rank: %d Creating sample file %s with format %d...\n", my_rank, filename,
               flavor[fmt]);
        if ((ret = PIOc_createfile(iosysid, &ncid, &(flavor[fmt]), filename, PIO_CLOBBER)))
            ERR(ret);

        /* Define netCDF dimensions and variable. */
        printf("rank: %d Defining netCDF metadata...\n", my_rank);
        if ((ret = PIOc_def_dim(ncid, DIM_NAME, (PIO_Offset)dim_len[0], &dimids[0])))
            ERR(ret);

        /* Define a variable. */
        if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, &varid)))
            ERR(ret);

        /* End define mode. */
        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Write some data. */
        float fillvalue = 0.0;
        PIO_Offset arraylen = 1;
        float test_data[arraylen];
        for (int f = 0; f < arraylen; f++)
            test_data[f] = my_rank * 10 + f;
        if ((ret = PIOc_write_darray(ncid, varid, ioid, arraylen, test_data, &fillvalue)))
            ERR(ret);

        /* Close the netCDF file. */
        printf("rank: %d Closing the sample data file...\n", my_rank);
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

        /* Check the file contents. */
        if ((ret = check_file(iosysid, TARGET_NTASKS, my_rank, filename)))
            ERR(ret);
    }
    return PIO_NOERR;
}

/* Test without async.
 *
 * @param my_rank rank of the task.
 * @param num_flavors the number of PIO IO types that will be tested.
 * @param flavors array of the PIO IO types that will be tested.
 * @param test_comm communicator with all test tasks.
 * @returns 0 for success error code otherwise.
 */
int test_no_async(int my_rank, int ntasks, int num_flavors, int *flavor,
                  MPI_Comm test_comm)
{
    int niotasks;    /* Number of processors that will do IO. */
    int ioproc_stride = 1;    /* Stride in the mpi rank between io tasks. */
    int numAggregator = 0;    /* Number of the aggregator? Always 0 in this test. */
    int ioproc_start = 0;    /* Zero based rank of first processor to be used for I/O. */
    PIO_Offset elements_per_pe;    /* Array index per processing unit. */
    int iosysid;    /* The ID for the parallel I/O system. */
    int ioid; /* The I/O description ID. */
    PIO_Offset *compdof; /* The decomposition mapping. */
    int dim_len[NDIM] = {DIM_LEN}; /* Length of the dimensions in the sample data. */
    int ret; /* Return code. */

    /* keep things simple - 1 iotask per MPI process */
    niotasks = TARGET_NTASKS;

    /* Initialize the PIO IO system. This specifies how
     * many and which processors are involved in I/O. */
    if ((ret = PIOc_Init_Intracomm(test_comm, niotasks, ioproc_stride,
                                   ioproc_start, PIO_REARR_SUBSET, &iosysid)))
        ERR(ret);

    /* Describe the decomposition. This is a 1-based array, so add 1! */
    elements_per_pe = DIM_LEN / TARGET_NTASKS;
    if (!(compdof = malloc(elements_per_pe * sizeof(PIO_Offset))))
        return PIO_ENOMEM;
    for (int i = 0; i < elements_per_pe; i++)
        compdof[i] = my_rank * elements_per_pe + i + 1;

    /* Create the PIO decomposition for this test. */
    printf("rank: %d Creating decomposition...\n", my_rank);
    if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, NDIM, dim_len, (PIO_Offset)elements_per_pe,
                               compdof, &ioid, NULL, NULL, NULL)))
        ERR(ret);
    free(compdof);

    if ((ret = test_darray(iosysid, ioid, num_flavors, flavor, my_rank)))
        return ret;

    /* Free the PIO decomposition. */
    printf("rank: %d Freeing PIO decomposition...\n", my_rank);
    if ((ret = PIOc_freedecomp(iosysid, ioid)))
        ERR(ret);
    return PIO_NOERR;
}

/* Test with async.
 *
 * @param my_rank rank of the task.
 * @param nprocs the size of the communicator.
 * @param num_flavors the number of PIO IO types that will be tested.
 * @param flavors array of the PIO IO types that will be tested.
 * @param test_comm communicator with all test tasks.
 * @returns 0 for success error code otherwise.
 */
int test_async(int my_rank, int nprocs, int num_flavors, int *flavor,
               MPI_Comm test_comm)
{
    int niotasks;            /* Number of processors that will do IO. */
    int ioproc_stride = 1;   /* Stride in the mpi rank between io tasks. */
    int ioproc_start = 0;    /* 0 based rank of first task to be used for I/O. */
    PIO_Offset elements_per_pe;    /* Array index per processing unit. */
    int iosysid[COMPONENT_COUNT];  /* The ID for the parallel I/O system. */
    int ioid;                      /* The I/O description ID. */
    PIO_Offset *compdof;           /* The decomposition mapping. */
    int num_procs[COMPONENT_COUNT + 1] = {1, TARGET_NTASKS - 1}; /* Num procs in each component. */
    int mpierr;  /* Return code from MPI functions. */
    int ret;     /* Return code. */

    /* Is the current process a computation task? */
    int comp_task = my_rank < NUM_IO_PROCS ? 0 : 1;
    printf("%d comp_task = %d\n", my_rank, comp_task);

    /* Initialize the IO system. */
    if ((ret = PIOc_Init_Async(test_comm, NUM_IO_PROCS, NULL, COMPONENT_COUNT,
                               num_procs, NULL, iosysid)))
        ERR(ERR_INIT);
    for (int c = 0; c < COMPONENT_COUNT; c++)
        printf("%d iosysid[%d] = %d\n", my_rank, c, iosysid[c]);

    /* All the netCDF calls are only executed on the computation
     * tasks. The IO tasks have not returned from PIOc_Init_Intercomm,
     * and when the do, they should go straight to finalize. */
    if (comp_task)
    {
        /* Test the netCDF-4 functions. */
        /* if ((ret = test_darray(iosysid[0], ioid, num_flavors, flavor, my_rank))) */
        /*     return ret; */

        /* Finalize the IO system. Only call this from the computation tasks. */
        printf("%d %s Freeing PIO resources\n", my_rank, TEST_NAME);
        for (int c = 0; c < COMPONENT_COUNT; c++)
        {
            if ((ret = PIOc_finalize(iosysid[c])))
                ERR(ret);
            printf("%d %s PIOc_finalize completed for iosysid = %d\n", my_rank, TEST_NAME,
                   iosysid[c]);
        }
    } /* endif comp_task */

    return PIO_NOERR;
}

/* Run Tests for darray Functions. */
int main(int argc, char **argv)
{
    int my_rank;     /* Zero-based rank of processor. */
    int ntasks;      /* Number of processors involved in current execution. */
    MPI_Comm test_comm;   /* Contains all tasks running test. */
    int num_flavors;      /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    int ret;              /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS,
                             &test_comm)))
        ERR(ERR_INIT);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);

        /* Run tests without async feature. */
        if ((ret = test_no_async(my_rank, ntasks, num_flavors, flavor, test_comm)))
            return ret;

        /* Run tests with async. */
        if ((ret = test_async(my_rank, ntasks, num_flavors, flavor, test_comm)))
            return ret;

    } /* my_rank < TARGET_NTASKS */

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ERR_AWFUL;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
