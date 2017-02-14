/*
 * Tests for PIO Functions. In this test we use a simple 2D variable,
 * with an unlimited dimension. The data will have two timesteps, and
 * 4 elements each timestep.
 *
 * Ed Hartnett, 2/14/17
 */
#include <pio.h>
#include <pio_internal.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_pioc_unlim"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

/* The number of dimensions in the example data. In this test, we
 * are using two-dimensional data. */
#define NDIM 2

/* The length of our sample data along each dimension. */
#define X_DIM_LEN 4

/* The number of timesteps of data to write. */
#define NUM_TIMESTEPS 2

/* The name of the variable in the netCDF output files. */
#define VAR_NAME "var_2D_with_unlim"

/* The meaning of life, the universe, and everything. */
#define START_DATA_VAL 42

/* The dimension names. */
char dim_name[NDIM][PIO_MAX_NAME + 1] = {"timestep", "x"};

/* Length of the dimensions in the sample data. */
int dim_len[NDIM] = {NC_UNLIMITED, X_DIM_LEN};

/* Create the decomposition to divide the 2-dimensional sample data
 * between the 4 tasks.
 *
 * @param ntasks the number of available tasks
 * @param my_rank rank of this task.
 * @param iosysid the IO system ID.
 * @param dim1_len the length of the dimension.
 * @param ioid a pointer that gets the ID of this decomposition.
 * @returns 0 for success, error code otherwise.
 **/
int create_decomposition(int ntasks, int my_rank, int iosysid, int dim1_len, int *ioid)
{
    PIO_Offset elements_per_pe;     /* Array elements per processing unit. */
    PIO_Offset *compdof;  /* The decomposition mapping. */
    int dim_len[NDIM] = {X_DIM_LEN};
    int ret;

    /* How many data elements per task? */
    elements_per_pe = X_DIM_LEN / ntasks;

    /* Allocate space for the decomposition array. */
    if (!(compdof = malloc(elements_per_pe * sizeof(PIO_Offset))))
        return PIO_ENOMEM;

    /* Describe the decomposition. This is a 1-based array, so add 1! */
    for (int i = 0; i < elements_per_pe; i++)
        compdof[i] = my_rank * elements_per_pe + i + 1;

    /* Create the PIO decomposition for this test. */
    printf("%d Creating decomposition elements_per_pe = %lld\n", my_rank, elements_per_pe);
    if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, NDIM - 1, dim_len, elements_per_pe,
                               compdof, ioid, NULL, NULL, NULL)))
        ERR(ret);

    printf("%d decomposition initialized.\n", my_rank);

    /* Free the mapping. */
    free(compdof);

    return 0;
}

/* Check the contents of the test file. */
int check_darray_file(int iosysid, int ntasks, int my_rank, char *filename)
{
    int ncid;
    int ndims, nvars, ngatts, unlimdimid;
    /* char dim_name_in[PIO_MAX_NAME + 1]; */
    /* PIO_Offset dim_len_in; */
    /* PIO_Offset arraylen = 1; */
    /* float data_in; */
    /* int ioid; */
    int ret;

    assert(filename);

    /* Open the file. */
    if ((ret = PIOc_open(iosysid, filename, NC_NOWRITE, &ncid)))
        return ret;

    /* Check metadata. */
    if ((ret = PIOc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid)))
        return ret;
    /* if (ndims != 1 || nvars != 1 || ngatts != 0 || unlimdimid != -1) */
    /*     return ERR_WRONG; */
    /* if ((ret = PIOc_inq_dim(ncid, 0, dim_name_in, &dim_len_in))) */
    /*     return ret; */
    /* if (strcmp(dim_name_in, DIM_NAME) || dim_len_in != DIM_LEN) */
    /*     return ERR_WRONG; */

    /* /\* Decompose the data over the tasks. *\/ */
    /* if ((ret = create_decomposition(ntasks, my_rank, iosysid, DIM_LEN, &ioid))) */
    /*     return ret; */

    /* /\* Read data. *\/ */
    /* if ((ret = PIOc_read_darray(ncid, 0, ioid, arraylen, &data_in))) */
    /*     return ret; */

    /* /\* Check data. *\/ */
    /* if (data_in != my_rank * 10) */
    /*     return ERR_WRONG; */

    /* /\* Close the file. *\/ */
    /* if ((ret = PIOc_closefile(ncid))) */
    /*     return ret; */

    /* /\* Free the PIO decomposition. *\/ */
    /* if ((ret = PIOc_freedecomp(iosysid, ioid))) */
    /*     ERR(ret); */

    return PIO_NOERR;
}

/* Create the test file. */
int create_test_file(int iosysid, int ioid, int iotype, int my_rank, int *ncid, int *varid)
{
    char filename[PIO_MAX_NAME + 1]; /* Name for the output files. */
    int dim_len[NDIM] = {NC_UNLIMITED, X_DIM_LEN}; /* Length of the dimensions in the sample data. */
    int dimids[NDIM];      /* The dimension IDs. */
    int ret;       /* Return code. */

    /* Create the filename. */
    sprintf(filename, "%s_iotype_%d.nc", TEST_NAME, iotype);
    
    /* Create the netCDF output file. */
    printf("rank: %d Creating sample file %s with format %d...\n", my_rank, filename,
           iotype);
    if ((ret = PIOc_createfile(iosysid, ncid, &iotype, filename, PIO_CLOBBER)))
        ERR(ret);
    
    /* Define netCDF dimensions and variable. */
    printf("rank: %d Defining netCDF metadata...\n", my_rank);
    if ((ret = PIOc_def_dim(*ncid, dim_name[0], (PIO_Offset)dim_len[0], &dimids[0])))
        ERR(ret);
    if ((ret = PIOc_def_dim(*ncid, dim_name[1], (PIO_Offset)dim_len[1], &dimids[1])))
        ERR(ret);
    
    /* Define a variable. */
    if ((ret = PIOc_def_var(*ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, varid)))
        ERR(ret);
    
    /* End define mode. */
    if ((ret = PIOc_enddef(*ncid)))
        ERR(ret);
    
    return PIO_NOERR;
}

/* Run all the tests. */
int test_all(int iosysid, int num_flavors, int *flavor, int my_rank, MPI_Comm test_comm,
             int async)
{
    int ioid;
    int ncid;
    int varid;
    int my_test_size;
    char filename[NC_MAX_NAME + 1];
    int ret; /* Return code. */

    if ((ret = MPI_Comm_size(test_comm, &my_test_size)))
        MPIERR(ret);
    
    /* This will be our file name for writing out decompositions. */
    sprintf(filename, "decomp_%d.txt", my_rank);

    if (!async)
    {
        printf("%d Testing darray. async = %d\n", my_rank, async);
        
        /* Decompose the data over the tasks. */
        if ((ret = create_decomposition(my_test_size, my_rank, iosysid, X_DIM_LEN, &ioid)))
            return ret;

        /* Use PIO to create the example file in each of the four
         * available ways. */
        for (int fmt = 0; fmt < num_flavors; fmt++)
        {
            if ((ret = create_test_file(iosysid, ioid, flavor[fmt], my_rank, &ncid, &varid)))
                return ret;
            if ((ret = PIOc_setframe(ncid, varid, 0)))
                return ret;
            if ((ret = PIOc_advanceframe(ncid, varid)))
                return ret;

            /* Look at the internals to check that the frame commands
             * worked. */
            file_desc_t *file;            
            if ((ret = pio_get_file(ncid, &file)))
                return ret;
            if (file->varlist[varid].record != 1)
                return ERR_WRONG;
            
            if ((PIOc_closefile(ncid)))
                return ret;
        }

        /* Free the PIO decomposition. */
        if ((ret = PIOc_freedecomp(iosysid, ioid)))
            ERR(ret);
    }

    return PIO_NOERR;
}

/* Run Tests for NetCDF-4 Functions. */
int main(int argc, char **argv)
{
    /* Change the 5th arg to 3 to turn on logging. */
    return run_test_main(argc, argv, MIN_NTASKS, TARGET_NTASKS, 3,
                         TEST_NAME, dim_len, COMPONENT_COUNT, NUM_IO_PROCS);
}
