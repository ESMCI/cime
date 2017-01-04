/*
 * Tests for NetCDF-4 Functions.
 *
 * There are some functions that apply only to netCDF-4 files. This
 * test checks those functions. PIO will return an error if these
 * functions are called on non-netCDF-4 files, and that is tested in
 * this code as well.
 *
 * Ed Hartnett
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_pioc"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 1

/* The number of dimensions in the example data. In this test, we
 * are using three-dimensional data. */
#define NDIM 3

/* The length of our sample data along each dimension. */
#define X_DIM_LEN 40
#define Y_DIM_LEN 40

/* The number of timesteps of data to write. */
#define NUM_TIMESTEPS 1

/* The name of the variable in the netCDF output files. */
#define VAR_NAME "foo"

/* The name of the attribute in the netCDF output files. */
#define ATT_NAME "bar"

/* The meaning of life, the universe, and everything. */
#define START_DATA_VAL 42

/* Values for some netcdf-4 settings. */
#define VAR_CACHE_SIZE (1024 * 1024)
#define VAR_CACHE_NELEMS 10
#define VAR_CACHE_PREEMPTION 0.5

/* Number of NetCDF classic types. */
#define NUM_CLASSIC_TYPES 6

/* Number of NetCDF-4 types. */
#define NUM_NETCDF4_TYPES 12

/* The dimension names. */
char dim_name[NDIM][PIO_MAX_NAME + 1] = {"timestep", "x", "y"};

/* Length of the dimensions in the sample data. */
int dim_len[NDIM] = {NC_UNLIMITED, X_DIM_LEN, Y_DIM_LEN};

/* Length of chunksizes to use in netCDF-4 files. */
PIO_Offset chunksize[NDIM] = {2, X_DIM_LEN/2, Y_DIM_LEN/2};

/* Some sample data values to write. */
char char_data = 2;
signed char byte_data = -42;
short short_data = -300;
int int_data = -10000;
float float_data = -42.42;
double double_data = -420000000000.5;
unsigned char ubyte_data = 43;
unsigned short ushort_data = 666;
unsigned int uint_data = 666666;
long long int64_data = -99999999999;
unsigned long long uint64_data = 99999999999;

char char_array[X_DIM_LEN][Y_DIM_LEN];
signed char byte_array[X_DIM_LEN][Y_DIM_LEN];
short short_array[X_DIM_LEN][Y_DIM_LEN];
int int_array[X_DIM_LEN][Y_DIM_LEN];
float float_array[X_DIM_LEN][Y_DIM_LEN];
double double_array[X_DIM_LEN][Y_DIM_LEN];
unsigned char ubyte_array[X_DIM_LEN][Y_DIM_LEN];
unsigned short ushort_array[X_DIM_LEN][Y_DIM_LEN];
unsigned int uint_array[X_DIM_LEN][Y_DIM_LEN];
long long int64_array[X_DIM_LEN][Y_DIM_LEN];
unsigned long long uint64_array[X_DIM_LEN][Y_DIM_LEN];

#define DIM_NAME "dim"
#define NDIM1 1
#define DIM_LEN 4

/* Fill up the data arrays with some values. */
void init_arrays()
{
    for (int x = 0; x < X_DIM_LEN; x++)
        for (int y = 0; y < Y_DIM_LEN; y++)
        {
            char_array[x][y] = char_data;
            byte_array[x][y] = byte_data;
            short_array[x][y] = short_data;
            int_array[x][y] = int_data;
            float_array[x][y] = float_data;
            double_array[x][y] = double_data;
            ubyte_array[x][y] = ubyte_data;
            ushort_array[x][y] = ushort_data;
            uint_array[x][y] = uint_data;
            int64_array[x][y] = int64_data;
            uint64_array[x][y] = uint64_data;
        }
}

/* Create the decomposition to divide the data between the 4 tasks. */
int create_decomposition(int ntasks, int my_rank, int iosysid, int *ioid)
{
    PIO_Offset elements_per_pe;     /* Array elements per processing unit. */
    PIO_Offset *compdof;  /* The decomposition mapping. */
    int dim_len[NDIM1] = {DIM_LEN};
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
    if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, NDIM1, dim_len, elements_per_pe,
                               compdof, ioid, NULL, NULL, NULL)))
        ERR(ret);

    printf("%d decomposition initialized.", my_rank);

    /* Free the mapping. */
    free(compdof);

    return 0;
}

/* Check the contents of the test file. */
int check_darray_file(int iosysid, int ntasks, int my_rank, char *filename)
{
    int ncid;
    int ndims, nvars, ngatts, unlimdimid;
    char dim_name_in[PIO_MAX_NAME + 1];
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
    char filename[PIO_MAX_NAME + 1]; /* Name for the output files. */
    int dim_len[NDIM1] = {DIM_LEN}; /* Length of the dimensions in the sample data. */
    int dimids[NDIM1];      /* The dimension IDs. */
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
        if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM1, dimids, &varid)))
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
        /* if ((ret = PIOc_write_darray(ncid, varid, ioid, arraylen, test_data, &fillvalue))) */
        /*     ERR(ret); */

        /* Close the netCDF file. */
        printf("rank: %d Closing the sample data file...\n", my_rank);
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

        /* Check the file contents. */
        /* if ((ret = check_darray_file(iosysid, TARGET_NTASKS, my_rank, filename))) */
        /*     ERR(ret); */
    }
    return PIO_NOERR;
}

/* Check the dimension names.
 *
 * @param my_rank rank of process
 * @param ncid ncid of open netCDF file
 * @returns 0 for success, error code otherwise. */
int check_dim_names(int my_rank, int ncid, MPI_Comm test_comm)
{
    char dim_name[PIO_MAX_NAME + 1];
    char zero_dim_name[PIO_MAX_NAME + 1];
    int my_test_rank;
    int ret;

    /* Find rank in test communicator. */
    if ((ret = MPI_Comm_rank(test_comm, &my_test_rank)))
        MPIERR(ret);

    for (int d = 0; d < NDIM; d++)
    {
        strcpy(dim_name, "11111111111111111111111111111111");
        if ((ret = PIOc_inq_dimname(ncid, d, dim_name)))
            return ret;
        printf("my_rank %d my_test_rank %d dim %d name %s\n", my_rank, my_test_rank, d, dim_name);

        /* Did other ranks get the same name? */
        if (!my_test_rank)
            strcpy(zero_dim_name, dim_name);
        printf("rank %d dim_name %s zero_dim_name %s\n", my_rank, dim_name, zero_dim_name);
        if ((ret = MPI_Bcast(&zero_dim_name, strlen(dim_name) + 1, MPI_CHAR, 0,
                             test_comm)))
            MPIERR(ret);
        printf("%d zero_dim_name = %s dim_name = %s\n", my_rank, zero_dim_name, dim_name);
        if (strcmp(dim_name, zero_dim_name))
            return ERR_AWFUL;
    }
    return 0;
}

/* Check the variable name.
 *
 * @param my_rank rank of process
 * @param ncid ncid of open netCDF file
 *
 * @returns 0 for success, error code otherwise. */
int check_var_name(int my_rank, int ncid, MPI_Comm test_comm)
{
    char var_name[PIO_MAX_NAME + 1];
    char zero_var_name[PIO_MAX_NAME + 1];
    int my_test_rank;
    int ret;

    /* Find rank in test communicator. */
    if ((ret = MPI_Comm_rank(test_comm, &my_test_rank)))
        MPIERR(ret);

    strcpy(var_name, "11111111111111111111111111111111");
    if ((ret = PIOc_inq_varname(ncid, 0, var_name)))
        return ret;
    printf("my_rank %d var name %s\n", my_rank, var_name);

    /* Did other ranks get the same name? */
    if (!my_test_rank)
        strcpy(zero_var_name, var_name);
    if ((ret = MPI_Bcast(&zero_var_name, strlen(var_name) + 1, MPI_CHAR, 0,
                         test_comm)))
        MPIERR(ret);
    if (strcmp(var_name, zero_var_name))
        return ERR_AWFUL;
    return 0;
}

/* Check the attribute name.
 *
 * @param my_rank rank of process
 * @param ncid ncid of open netCDF file
 *
 * @returns 0 for success, error code otherwise. */
int check_att_name(int my_rank, int ncid, MPI_Comm test_comm)
{
    char att_name[PIO_MAX_NAME + 1];
    char zero_att_name[PIO_MAX_NAME + 1];
    int my_test_rank;
    int ret;

    /* Find rank in test communicator. */
    if ((ret = MPI_Comm_rank(test_comm, &my_test_rank)))
        MPIERR(ret);

    strcpy(att_name, "11111111111111111111111111111111");
    if ((ret = PIOc_inq_attname(ncid, NC_GLOBAL, 0, att_name)))
        return ret;
    printf("my_rank %d att name %s\n", my_rank, att_name);

    /* Did everyone ranks get the same length name? */
/*    if (strlen(att_name) != strlen(ATT_NAME))
      return ERR_AWFUL;*/
    if (!my_test_rank)
        strcpy(zero_att_name, att_name);
    if ((ret = MPI_Bcast(&zero_att_name, strlen(att_name) + 1, MPI_CHAR, 0,
                         test_comm)))
        MPIERR(ret);
    if (strcmp(att_name, zero_att_name))
        return ERR_AWFUL;
    return 0;
}

/*
 * Check error strings.
 *
 * @param my_rank rank of this task.
 * @param num_tries number of errcodes to try.
 * @param errcode pointer to array of error codes, of length num_tries.
 * @param expected pointer to an array of strings, with the expected
 * error messages for each error code.
 * @returns 0 for success, error code otherwise.
 */
int check_error_strings(int my_rank, int num_tries, int *errcode,
                        const char **expected)
{
    int ret;

    /* Try each test code. */
    for (int try = 0; try < num_tries; try++)
    {
        char errstr[PIO_MAX_NAME + 1];

        /* Get the error string for this errcode. */
        if ((ret = PIOc_strerror(errcode[try], errstr)))
            return ret;

        printf("%d for errcode = %d message = %s\n", my_rank, errcode[try], errstr);

        /* Check that it was as expected. */
        if (strncmp(errstr, expected[try], strlen(expected[try])))
        {
            printf("%d expected %s got %s\n", my_rank, expected[try], errstr);
            return ERR_AWFUL;
        }
        if (!my_rank)
            printf("%d errcode = %d passed\n", my_rank, errcode[try]);
    }

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function for classic netCDF.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror_netcdf(int my_rank)
{
#ifdef _NETCDF
#define NUM_NETCDF_TRIES 4
    int errcode[NUM_NETCDF_TRIES] = {PIO_EBADID, NC4_LAST_ERROR - 1, 0, 1};
    const char *expected[NUM_NETCDF_TRIES] = {"NetCDF: Not a valid ID",
                                              "Unknown Error: Unrecognized error code", "No error",
                                              nc_strerror(1)};
    int ret;

    if ((ret = check_error_strings(my_rank, NUM_NETCDF_TRIES, errcode, expected)))
        return ret;

    if (!my_rank)
        printf("check_strerror_netcdf SUCCEEDED!\n");
#endif /* (_NETCDF) */

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function for netCDF-4.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror_netcdf4(int my_rank)
{
#ifdef _NETCDF4
#define NUM_NETCDF4_TRIES 2
    int errcode[NUM_NETCDF4_TRIES] = {NC_ENOTNC3, NC_ENOPAR};
    const char *expected[NUM_NETCDF4_TRIES] =
        {"NetCDF: Attempting netcdf-3 operation on netcdf-4 file",
         "NetCDF: Parallel operation on file opened for non-parallel access"};
    int ret;

    if ((ret = check_error_strings(my_rank, NUM_NETCDF4_TRIES, errcode, expected)))
        return ret;

    if (!my_rank)
        printf("check_strerror_netcdf4 SUCCEEDED!\n");
#endif /* _NETCDF4 */

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function for parallel-netCDF.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror_pnetcdf(int my_rank)
{
#ifdef _PNETCDF
#define NUM_PNETCDF_TRIES 2
    int errcode[NUM_PNETCDF_TRIES] = {NC_EMULTIDEFINE_VAR_NUM, NC_EMULTIDEFINE_ATTR_VAL};
    const char *expected[NUM_PNETCDF_TRIES] =
        {"Number of variables is",
         "Attribute value is inconsistent among processes."};
    int ret;

    if ((ret = check_error_strings(my_rank, NUM_PNETCDF_TRIES, errcode, expected)))
        return ret;

    if (!my_rank)
        printf("check_strerror_pnetcdf SUCCEEDED!\n");
#endif /* _PNETCDF */

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function for PIO.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror_pio(int my_rank)
{
#define NUM_PIO_TRIES 6
    int errcode[NUM_PIO_TRIES] = {PIO_EBADID,
                                  NC_ENOTNC3, NC4_LAST_ERROR - 1, 0, 1,
                                  PIO_EBADIOTYPE};
    const char *expected[NUM_PIO_TRIES] = {"NetCDF: Not a valid ID",
                                           "NetCDF: Attempting netcdf-3 operation on netcdf-4 file",
                                           "Unknown Error: Unrecognized error code", "No error",
                                           nc_strerror(1), "Bad IO type"};
    int ret;

    if ((ret = check_error_strings(my_rank, NUM_PIO_TRIES, errcode, expected)))
        return ret;

    if (!my_rank)
        printf("check_strerror_pio SUCCEEDED!\n");

    return PIO_NOERR;
}

/* Check the PIOc_strerror() function.
 *
 * @param my_rank the rank of this process.
 * @return 0 for success, error code otherwise.
 */
int check_strerror(int my_rank)
{
    int ret;

    printf("checking strerror for netCDF-classic error codes...\n");
    if ((ret = check_strerror_netcdf(my_rank)))
        return ret;

    printf("checking strerror for netCDF-4 error codes...\n");
    if ((ret = check_strerror_netcdf4(my_rank)))
        return ret;

    printf("checking strerror for pnetcdf error codes...\n");
    if ((ret = check_strerror_pnetcdf(my_rank)))
        return ret;

    printf("checking strerror for PIO error codes...\n");
    if ((ret = check_strerror_pio(my_rank)))
        return ret;

    return PIO_NOERR;
}

/* Define metadata for the test file. */
int define_metadata(int ncid, int my_rank)
{
    int dimids[NDIM]; /* The dimension IDs. */
    int varid; /* The variable ID. */
    int ret;

    for (int d = 0; d < NDIM; d++)
        if ((ret = PIOc_def_dim(ncid, dim_name[d], (PIO_Offset)dim_len[d], &dimids[d])))
            ERR(ret);

    if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_INT, NDIM, dimids, &varid)))
        ERR(ret);

    return PIO_NOERR;
}

/* Check the metadata in the test file. */
int check_metadata(int ncid, int my_rank)
{
    int ndims, nvars, ngatts, unlimdimid, natts, dimid[NDIM];
    PIO_Offset len_in;
    char name_in[PIO_MAX_NAME + 1];
    nc_type xtype_in;
    int ret;

    /* Check how many dims, vars, global atts there are, and the id of
     * the unlimited dimension. */
    if ((ret = PIOc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid)))
        return ret;
    if (ndims != NDIM || nvars != 1 || ngatts != 0 || unlimdimid != 0)
        return ERR_AWFUL;

    /* Check the dimensions. */
    for (int d = 0; d < NDIM; d++)
    {
        if ((ret = PIOc_inq_dim(ncid, d, name_in, &len_in)))
            ERR(ret);
        if (len_in != dim_len[d] || strcmp(name_in, dim_name[d]))
            return ERR_AWFUL;
    }

    /* Check the variable. */
    if ((ret = PIOc_inq_var(ncid, 0, name_in, &xtype_in, &ndims, dimid, &natts)))
        ERR(ret);
    if (strcmp(name_in, VAR_NAME) || xtype_in != PIO_INT || ndims != NDIM ||
        dimid[0] != 0 || dimid[1] != 1 || dimid[2] != 2 || natts != 0)
        return ERR_AWFUL;

    return PIO_NOERR;
}

/* Test file operations.
 *
 * @param iosysid the iosystem ID that will be used for the test.
 * @param num_flavors the number of different IO types that will be tested.
 * @param flavor an array of the valid IO types.
 * @param my_rank 0-based rank of task.
 * @returns 0 for success, error code otherwise.
 */
int test_names(int iosysid, int num_flavors, int *flavor, int my_rank,
               MPI_Comm test_comm)
{
    int ret;    /* Return code. */

    /* Use PIO to create the example file in each of the four
     * available ways. */
    for (int fmt = 0; fmt < num_flavors; fmt++)
    {
        int ncid;
        int varid;
        char filename[PIO_MAX_NAME + 1]; /* Test filename. */
        char iotype_name[PIO_MAX_NAME + 1];
        int dimids[NDIM];        /* The dimension IDs. */

        /* Create a filename. */
        if ((ret = get_iotype_name(flavor[fmt], iotype_name)))
            return ret;
        sprintf(filename, "%s_%s.nc", TEST_NAME, iotype_name);

        /* Create the netCDF output file. */
        printf("rank: %d Creating sample file %s with format %d...\n",
               my_rank, filename, flavor[fmt]);
        if ((ret = PIOc_createfile(iosysid, &ncid, &(flavor[fmt]), filename, PIO_CLOBBER)))
            ERR(ret);

        /* Define netCDF dimensions and variable. */
        printf("rank: %d Defining netCDF metadata...\n", my_rank);
        for (int d = 0; d < NDIM; d++)
        {
            printf("rank: %d Defining netCDF dimension %s, length %d\n", my_rank,
                   dim_name[d], dim_len[d]);
            if ((ret = PIOc_def_dim(ncid, dim_name[d], (PIO_Offset)dim_len[d], &dimids[d])))
                ERR(ret);
        }

        /* Check the dimension names. */
        if ((ret = check_dim_names(my_rank, ncid, test_comm)))
            ERR(ret);

        /* Define a global attribute. */
        int att_val = 42;
        if ((ret = PIOc_put_att_int(ncid, NC_GLOBAL, ATT_NAME, PIO_INT, 1, &att_val)))
            ERR(ret);

        /* Check the attribute name. */
        if ((ret = check_att_name(my_rank, ncid, test_comm)))
            ERR(ret);

        /* Define a variable. */
        if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, &varid)))
            ERR(ret);

        /* Check the variable name. */
        if ((ret = check_var_name(my_rank, ncid, test_comm)))
            ERR(ret);

        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Close the netCDF file. */
        printf("rank: %d Closing the sample data file...\n", my_rank);
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);
    }

    return PIO_NOERR;
}

/* Use the var1 functions to write some data to an open test file. */
int putget_write_var1(int ncid, int *varid, PIO_Offset *index, int flavor)
{
    int ret;

    /* if ((ret = PIOc_put_var1_text(ncid, varid[2], index, &char_data))) */
    /*     ERR(ret); */

    if ((ret = PIOc_put_var1_schar(ncid, varid[0], index, (signed char *)byte_array)))
        return ret;

    if ((ret = PIOc_put_var1_short(ncid, varid[2], index, &short_data)))
        return ret;

    if ((ret = PIOc_put_var1_int(ncid, varid[3], index, &int_data)))
        return ret;

    if ((ret = PIOc_put_var1_float(ncid, varid[4], index, &float_data)))
        return ret;

    if ((ret = PIOc_put_var1_double(ncid, varid[5], index, &double_data)))
        return ret;

    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
    {
        if ((ret = PIOc_put_var1_uchar(ncid, varid[6], index, &ubyte_data)))
            return ret;
        if ((ret = PIOc_put_var1_ushort(ncid, varid[7], index, &ushort_data)))
            return ret;
        if ((ret = PIOc_put_var1_uint(ncid, varid[8], index, &uint_data)))
            return ret;
        if ((ret = PIOc_put_var1_longlong(ncid, varid[9], index, &int64_data)))
            return ret;
        if ((ret = PIOc_put_var1_ulonglong(ncid, varid[10], index, &uint64_data)))
            return ret;
    }

    return 0;
}

/* Use the var1 functions to write some data to an open test file. */
int putget_write_var(int ncid, int *varid, int flavor)
{
    int ret;

    /* if ((ret = PIOc_put_var_text(ncid, varid[2], &char_array))) */
    /*     ERR(ret); */

    if ((ret = PIOc_put_var_schar(ncid, varid[0], (signed char *)byte_array)))
        return ret;

    if ((ret = PIOc_put_var_short(ncid, varid[2], (short *)short_array)))
        return ret;

    if ((ret = PIOc_put_var_int(ncid, varid[3], (int *)int_array)))
        return ret;

    if ((ret = PIOc_put_var_float(ncid, varid[4], (float *)float_array)))
        return ret;

    if ((ret = PIOc_put_var_double(ncid, varid[5], (double *)double_array)))
        return ret;

    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
    {
        if ((ret = PIOc_put_var_uchar(ncid, varid[6], (unsigned char *)ubyte_array)))
            return ret;
        if ((ret = PIOc_put_var_ushort(ncid, varid[7], (unsigned short *)ushort_array)))
            return ret;
        if ((ret = PIOc_put_var_uint(ncid, varid[8], (unsigned int *)uint_array)))
            return ret;
        if ((ret = PIOc_put_var_longlong(ncid, varid[9], (long long *)int64_array)))
            return ret;
        if ((ret = PIOc_put_var_ulonglong(ncid, varid[10], (unsigned long long *)uint64_array)))
            return ret;
    }

    return 0;
}

/* Use the vara functions to write some data to an open test file. */
int putget_write_vara(int ncid, int *varid, PIO_Offset *start, PIO_Offset *count,
                      int flavor)
{
    int ret;

    /* if ((ret = PIOc_put_vara_text(ncid, varid[2], start, count, char_array))) */
    /*     ERR(ret); */

    if ((ret = PIOc_put_vara_schar(ncid, varid[0], start, count, (signed char *)byte_array)))
        return ret;

    if ((ret = PIOc_put_vara_short(ncid, varid[2], start, count, (short *)short_array)))
        return ret;

    if ((ret = PIOc_put_vara_int(ncid, varid[3], start, count, (int *)int_array)))
        return ret;

    if ((ret = PIOc_put_vara_float(ncid, varid[4], start, count, (float *)float_array)))
        return ret;

    if ((ret = PIOc_put_vara_double(ncid, varid[5], start, count, (double *)double_array)))
        return ret;

    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
    {
        if ((ret = PIOc_put_vara_uchar(ncid, varid[6], start, count, (unsigned char *)ubyte_array)))
            return ret;
        if ((ret = PIOc_put_vara_ushort(ncid, varid[7], start, count, (unsigned short *)ushort_array)))
            return ret;
        if ((ret = PIOc_put_vara_uint(ncid, varid[8], start, count, (unsigned int *)uint_array)))
            return ret;
        if ((ret = PIOc_put_vara_longlong(ncid, varid[9], start, count, (long long *)int64_array)))
            return ret;
        if ((ret = PIOc_put_vara_ulonglong(ncid, varid[10], start, count, (unsigned long long *)uint64_array)))
            return ret;
    }

    return 0;
}

/* Use the vars functions to write some data to an open test file. */
int putget_write_vars(int ncid, int *varid, PIO_Offset *start, PIO_Offset *count,
                      PIO_Offset *stride, int flavor)
{
    int ret;

    /* if ((ret = PIOc_put_vara_text(ncid, varid[2], start, count, char_array))) */
    /*     ERR(ret); */

    if ((ret = PIOc_put_vars_schar(ncid, varid[0], start, count, stride, (signed char *)byte_array)))
        return ret;

    if ((ret = PIOc_put_vars_short(ncid, varid[2], start, count, stride, (short *)short_array)))
        return ret;

    if ((ret = PIOc_put_vars_int(ncid, varid[3], start, count, stride, (int *)int_array)))
        return ret;

    if ((ret = PIOc_put_vars_float(ncid, varid[4], start, count, stride, (float *)float_array)))
        return ret;

    if ((ret = PIOc_put_vars_double(ncid, varid[5], start, count, stride, (double *)double_array)))
        return ret;

    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
    {
        if ((ret = PIOc_put_vars_uchar(ncid, varid[6], start, count, stride, (unsigned char *)ubyte_array)))
            return ret;
        if ((ret = PIOc_put_vars_ushort(ncid, varid[7], start, count, stride, (unsigned short *)ushort_array)))
            return ret;
        if ((ret = PIOc_put_vars_uint(ncid, varid[8], start, count, stride, (unsigned int *)uint_array)))
            return ret;
        if ((ret = PIOc_put_vars_longlong(ncid, varid[9], start, count, stride, (long long *)int64_array)))
            return ret;
        if ((ret = PIOc_put_vars_ulonglong(ncid, varid[10], start, count, stride, (unsigned long long *)uint64_array)))
            return ret;
    }

    return 0;
}

/* Use the var1 functions to read some data from an open test file. */
int putget_read_var1(int ncid, int *varid, PIO_Offset *index, int flavor)
{
    signed char byte_data_in;
    short short_data_in;
    unsigned char ubyte_data_in;
    int int_data_in;
    float float_data_in;
    double double_data_in;
    unsigned short ushort_data_in;
    unsigned int uint_data_in;
    long long int64_data_in;
    unsigned long long uint64_data_in;
    int ret;

    if ((ret = PIOc_get_var1_schar(ncid, varid[0], index, &byte_data_in)))
        return ret;
    if (byte_data_in != byte_data)
        return ERR_WRONG;

    if ((ret = PIOc_get_var1_short(ncid, varid[2], index, &short_data_in)))
        return ret;
    if (short_data_in != short_data)
        return ERR_WRONG;

    if ((ret = PIOc_get_var1_int(ncid, varid[3], index, &int_data_in)))
        return ret;
    if (int_data_in != int_data)
        return ERR_WRONG;

    if ((ret = PIOc_get_var1_float(ncid, varid[4], index, &float_data_in)))
        return ret;
    if (float_data_in != float_data)
        return ERR_WRONG;

    if ((ret = PIOc_get_var1_double(ncid, varid[5], index, &double_data_in)))
        return ret;
    if (double_data_in != double_data)
        return ERR_WRONG;

    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
    {
        if ((ret = PIOc_get_var1_uchar(ncid, varid[6], index, &ubyte_data_in)))
            return ret;
        if (ubyte_data_in != ubyte_data)
            return ERR_WRONG;
        if ((ret = PIOc_get_var1_ushort(ncid, varid[7], index, &ushort_data_in)))
            return ret;
        if (ushort_data_in != ushort_data)
            return ERR_WRONG;
        if ((ret = PIOc_get_var1_uint(ncid, varid[8], index, &uint_data_in)))
            return ret;
        if (uint_data_in != uint_data)
            return ERR_WRONG;
        if ((ret = PIOc_get_var1_longlong(ncid, varid[9], index, &int64_data_in)))
            return ret;
        if (int64_data_in != int64_data)
            return ERR_WRONG;
        if ((ret = PIOc_get_var1_ulonglong(ncid, varid[10], index, &uint64_data_in)))
            return ret;
        if (uint64_data_in != uint64_data)
            return ERR_WRONG;
    }

    return 0;
}

/* Use the var functions to read some data from an open test file.
 *
 * @param ncid the ncid of the test file to read.
 * @param varid an array of varids in the file.
 * @param unlim non-zero if unlimited dimension is in use.
 * @param flavor the PIO IO type of the test file.
 * @returns 0 for success, error code otherwise.
*/
int putget_read_var(int ncid, int *varid, int unlim, int flavor)
{
    signed char byte_array_in[X_DIM_LEN][Y_DIM_LEN];
    short short_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned char ubyte_array_in[X_DIM_LEN][Y_DIM_LEN];
    int int_array_in[X_DIM_LEN][Y_DIM_LEN];
    float float_array_in[X_DIM_LEN][Y_DIM_LEN];
    double double_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned short ushort_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned int uint_array_in[X_DIM_LEN][Y_DIM_LEN];
    long long int64_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned long long uint64_array_in[X_DIM_LEN][Y_DIM_LEN];
    int x, y;
    int ret;

    /* When using the unlimited dimension, no data are wrtten by the
     * put_var_TYPE() functions, since the length of the unlimited
     * dimension is still 0. So for reading, just confirm that the
     * data files are empty. */
    if (unlim)
    {
        return 0;
    }

    if ((ret = PIOc_get_var_schar(ncid, varid[0], (signed char *)byte_array_in)))
        return ret;
    if ((ret = PIOc_get_var_short(ncid, varid[2], (short *)short_array_in)))
        return ret;
    if ((ret = PIOc_get_var_int(ncid, varid[3], (int *)int_array_in)))
        return ret;
    if ((ret = PIOc_get_var_float(ncid, varid[4], (float *)float_array_in)))
        return ret;
    if ((ret = PIOc_get_var_double(ncid, varid[5], (double *)double_array_in)))
        return ret;
    for (x = 0; x < X_DIM_LEN; x++)
        for (y = 0; y < Y_DIM_LEN; y++)
        {
            if (byte_array_in[x][y] != byte_array[x][y])
                return ERR_WRONG;
            if (short_array_in[x][y] != short_array[x][y])
                return ERR_WRONG;
            if (int_array_in[x][y] != int_array[x][y])
                return ERR_WRONG;
            if (float_array_in[x][y] != float_array[x][y])
                return ERR_WRONG;
            if (double_array_in[x][y] != double_array[x][y])
                return ERR_WRONG;
        }

    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
    {
        if ((ret = PIOc_get_var_uchar(ncid, varid[6], (unsigned char *)ubyte_array_in)))
            return ret;
        if ((ret = PIOc_get_var_ushort(ncid, varid[7], (unsigned short *)ushort_array_in)))
            return ret;
        if ((ret = PIOc_get_var_uint(ncid, varid[8], (unsigned int *)uint_array_in)))
            return ret;
        if ((ret = PIOc_get_var_longlong(ncid, varid[9], (long long *)int64_array_in)))
            return ret;
        if ((ret = PIOc_get_var_ulonglong(ncid, varid[10], (unsigned long long *)uint64_array_in)))
            return ret;
        for (x = 0; x < X_DIM_LEN; x++)
            for (y = 0; y < Y_DIM_LEN; y++)
            {
                if (ubyte_array_in[x][y] != ubyte_array[x][y])
                    return ERR_WRONG;
                if (ushort_array_in[x][y] != ushort_array[x][y])
                    return ERR_WRONG;
                if (uint_array_in[x][y] != uint_array[x][y])
                    return ERR_WRONG;
                if (int64_array_in[x][y] != int64_array[x][y])
                    return ERR_WRONG;
                if (uint64_array_in[x][y] != uint64_array[x][y])
                    return ERR_WRONG;
            }
    }

    return 0;
}

/* Use the vara functions to read some data from an open test file. */
int putget_read_vara(int ncid, int *varid, PIO_Offset *start, PIO_Offset *count,
                     int flavor)
{
    signed char byte_array_in[X_DIM_LEN][Y_DIM_LEN];
    short short_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned char ubyte_array_in[X_DIM_LEN][Y_DIM_LEN];
    int int_array_in[X_DIM_LEN][Y_DIM_LEN];
    float float_array_in[X_DIM_LEN][Y_DIM_LEN];
    double double_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned short ushort_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned int uint_array_in[X_DIM_LEN][Y_DIM_LEN];
    long long int64_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned long long uint64_array_in[X_DIM_LEN][Y_DIM_LEN];
    int x, y;
    int ret;

    if ((ret = PIOc_get_vara_schar(ncid, varid[0], start, count, (signed char *)byte_array_in)))
        return ret;
    if ((ret = PIOc_get_vara_short(ncid, varid[2], start, count, (short *)short_array_in)))
        return ret;
    if ((ret = PIOc_get_vara_int(ncid, varid[3], start, count, (int *)int_array_in)))
        return ret;
    if ((ret = PIOc_get_vara_float(ncid, varid[4], start, count, (float *)float_array_in)))
        return ret;
    if ((ret = PIOc_get_vara_double(ncid, varid[5], start, count, (double *)double_array_in)))
        return ret;

    for (x = 0; x < X_DIM_LEN; x++)
        for (y = 0; y < Y_DIM_LEN; y++)
        {
            if (byte_array_in[x][y] != byte_array[x][y])
                return ERR_WRONG;
            if (short_array_in[x][y] != short_array[x][y])
                return ERR_WRONG;
            if (int_array_in[x][y] != int_array[x][y])
                return ERR_WRONG;
            if (float_array_in[x][y] != float_array[x][y])
                return ERR_WRONG;
            if (double_array_in[x][y] != double_array[x][y])
                return ERR_WRONG;
        }

    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
    {
        if ((ret = PIOc_get_vara_uchar(ncid, varid[6], start, count, (unsigned char *)ubyte_array_in)))
            return ret;

        if ((ret = PIOc_get_vara_ushort(ncid, varid[7], start, count, (unsigned short *)ushort_array_in)))
            return ret;
        if ((ret = PIOc_get_vara_uint(ncid, varid[8], start, count, (unsigned int *)uint_array_in)))
            return ret;
        if ((ret = PIOc_get_vara_longlong(ncid, varid[9], start, count, (long long *)int64_array_in)))
            return ret;
        if ((ret = PIOc_get_vara_ulonglong(ncid, varid[10], start, count, (unsigned long long *)uint64_array_in)))
            return ret;
        for (x = 0; x < X_DIM_LEN; x++)
            for (y = 0; y < Y_DIM_LEN; y++)
            {
                if (ubyte_array_in[x][y] != ubyte_array[x][y])
                    return ERR_WRONG;
                if (ushort_array_in[x][y] != ushort_array[x][y])
                    return ERR_WRONG;
                if (uint_array_in[x][y] != uint_array[x][y])
                    return ERR_WRONG;
                if (int64_array_in[x][y] != int64_array[x][y])
                    return ERR_WRONG;
                if (uint64_array_in[x][y] != uint64_array[x][y])
                    return ERR_WRONG;
            }
    }

    return 0;
}

/* Use the vars functions to read some data from an open test file. */
int putget_read_vars(int ncid, int *varid, PIO_Offset *start, PIO_Offset *count,
                     PIO_Offset *stride, int flavor)
{
    signed char byte_array_in[X_DIM_LEN][Y_DIM_LEN];
    short short_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned char ubyte_array_in[X_DIM_LEN][Y_DIM_LEN];
    int int_array_in[X_DIM_LEN][Y_DIM_LEN];
    float float_array_in[X_DIM_LEN][Y_DIM_LEN];
    double double_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned short ushort_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned int uint_array_in[X_DIM_LEN][Y_DIM_LEN];
    long long int64_array_in[X_DIM_LEN][Y_DIM_LEN];
    unsigned long long uint64_array_in[X_DIM_LEN][Y_DIM_LEN];
    int x, y;
    int ret;

    if ((ret = PIOc_get_vars_schar(ncid, varid[0], start, count, stride, (signed char *)byte_array_in)))
        return ret;
    if ((ret = PIOc_get_vars_short(ncid, varid[2], start, count, stride, (short *)short_array_in)))
        return ret;
    if ((ret = PIOc_get_vars_int(ncid, varid[3], start, count, stride, (int *)int_array_in)))
        return ret;
    if ((ret = PIOc_get_vars_float(ncid, varid[4], start, count, stride, (float *)float_array_in)))
        return ret;
    if ((ret = PIOc_get_vars_double(ncid, varid[5], start, count, stride, (double *)double_array_in)))
        return ret;

    for (x = 0; x < X_DIM_LEN; x++)
        for (y = 0; y < Y_DIM_LEN; y++)
        {
            if (byte_array_in[x][y] != byte_array[x][y])
                return ERR_WRONG;
            if (short_array_in[x][y] != short_array[x][y])
                return ERR_WRONG;
            if (int_array_in[x][y] != int_array[x][y])
                return ERR_WRONG;
            if (float_array_in[x][y] != float_array[x][y])
                return ERR_WRONG;
            if (double_array_in[x][y] != double_array[x][y])
                return ERR_WRONG;
        }

    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
    {
        if ((ret = PIOc_get_vars_uchar(ncid, varid[6], start, count, stride, (unsigned char *)ubyte_array_in)))
            return ret;

        if ((ret = PIOc_get_vars_ushort(ncid, varid[7], start, count, stride, (unsigned short *)ushort_array_in)))
            return ret;
        if ((ret = PIOc_get_vars_uint(ncid, varid[8], start, count, stride, (unsigned int *)uint_array_in)))
            return ret;
        if ((ret = PIOc_get_vars_longlong(ncid, varid[9], start, count, stride, (long long *)int64_array_in)))
            return ret;
        if ((ret = PIOc_get_vars_ulonglong(ncid, varid[10], start, count, stride, (unsigned long long *)uint64_array_in)))
            return ret;
        for (x = 0; x < X_DIM_LEN; x++)
            for (y = 0; y < Y_DIM_LEN; y++)
            {
                if (ubyte_array_in[x][y] != ubyte_array[x][y])
                    return ERR_WRONG;
                if (ushort_array_in[x][y] != ushort_array[x][y])
                    return ERR_WRONG;
                if (uint_array_in[x][y] != uint_array[x][y])
                    return ERR_WRONG;
                if (int64_array_in[x][y] != int64_array[x][y])
                    return ERR_WRONG;
                if (uint64_array_in[x][y] != uint64_array[x][y])
                    return ERR_WRONG;
            }
    }

    return 0;
}

/* Create a test file for the putget tests to write data to and check
 * by reading it back. In this function we create the file, define the
 * dims and vars, and pass back the ncid.
 *
 * @param iosysid the IO system ID.
 * @param try the number of the test run, 0 for var, 1 for var1, 2 for
 * vara, 3 for vars.
 * @param unlim non-zero if unlimited dimension should be used.
 * @param flavor the PIO IO type.
 * @param dim_len array of length NDIM of the dimension lengths.
 * @param varid array of varids for the variables in the test file.
 * @param filename the name of the test file to create.
 * @param ncidp pointer that gets the ncid of the created file.
 * @returns 0 for success, error code otherwise.
 */
int create_putget_file(int iosysid, int access, int unlim, int flavor, int *dim_len,
                       int *varid, char *filename, int *ncidp)
{
    char iotype_name[PIO_MAX_NAME + 1];
    int dimids[NDIM];        /* The dimension IDs. */
    int num_vars = NUM_CLASSIC_TYPES;
    int xtype[NUM_NETCDF4_TYPES] = {PIO_BYTE, PIO_CHAR, PIO_SHORT, PIO_INT, PIO_FLOAT,
                                    PIO_DOUBLE, PIO_UBYTE, PIO_USHORT, PIO_UINT, PIO_INT64,
                                    PIO_UINT64, PIO_STRING};
    int ncid;
    int ret;

    /* Create a filename. */
    if ((ret = get_iotype_name(flavor, iotype_name)))
        return ret;
    sprintf(filename, "%s_putget_access_%d_unlim_%d_%s.nc", TEST_NAME, access, unlim,
            iotype_name);

    /* Create the netCDF output file. */
    if ((ret = PIOc_createfile(iosysid, &ncid, &flavor, filename, PIO_CLOBBER)))
        return ret;

    /* Are we using unlimited dimension? */
    if (!unlim)
        dim_len[0] = NUM_TIMESTEPS;

    /* Define netCDF dimensions and variable. */
    for (int d = 0; d < NDIM; d++)
        if ((ret = PIOc_def_dim(ncid, dim_name[d], (PIO_Offset)dim_len[d], &dimids[d])))
            return ret;

    /* For netcdf-4, there are extra types. */
    if (flavor == PIO_IOTYPE_NETCDF4C || flavor == PIO_IOTYPE_NETCDF4P)
        num_vars = NUM_NETCDF4_TYPES;

    /* Define variables. */
    for (int v = 0; v < num_vars; v++)
    {
        char var_name[PIO_MAX_NAME + 1];
        snprintf(var_name, PIO_MAX_NAME, "%s_%d", VAR_NAME, xtype[v]);
        if ((ret = PIOc_def_var(ncid, var_name, xtype[v], NDIM, dimids, &varid[v])))
            return ret;
    }

    if ((ret = PIOc_enddef(ncid)))
        return ret;

    /* Pass back the ncid. */
    *ncidp = ncid;

    return 0;
}

/* Test data read/write operations.
 *
 * This function creates a file with 3 dimensions, with a var of each
 * type. Then it uses the var/var1/vars/vars functions to write, and
 * then read data from the test file.
 *
 * @param iosysid the iosystem ID that will be used for the test.
 * @param num_flavors the number of different IO types that will be tested.
 * @param flavor an array of the valid IO types.
 * @param my_rank 0-based rank of task.
 * @returns 0 for success, error code otherwise.
 */
int test_putget(int iosysid, int num_flavors, int *flavor, int my_rank,
                MPI_Comm test_comm)
{
    int dim_len[NDIM] = {NC_UNLIMITED, X_DIM_LEN, Y_DIM_LEN};
    
#define NUM_ACCESS 4
    for (int unlim = 0; unlim < 2; unlim++)
        for (int access = 0; access < NUM_ACCESS; access++)
        {
            /* Use PIO to create the example file in each of the four
             * available ways. */
            for (int fmt = 0; fmt < num_flavors; fmt++)
            {
                char filename[PIO_MAX_NAME + 1]; /* Test filename. */
                int ncid;
                int varid[NUM_NETCDF4_TYPES];
                int ret;    /* Return code. */

                /* Create test file with dims and vars defined. */
                printf("%d Access %d creating test file for flavor = %d...\n",
                       my_rank, access, flavor[fmt]);
                if ((ret = create_putget_file(iosysid, access, unlim, flavor[fmt],
                                              dim_len, varid, filename, &ncid)))
                    return ret;

                /* Write some data. */
                PIO_Offset index[NDIM] = {0, 0, 0};
                PIO_Offset start[NDIM] = {0, 0, 0};
                PIO_Offset count[NDIM] = {1, X_DIM_LEN, Y_DIM_LEN};
                PIO_Offset stride[NDIM] = {1, 1, 1};

                switch (access)
                {
                case 0:
                    printf("%d Access %d writing data with var functions for flavor = %d...\n",
                           my_rank, access, flavor[fmt]);
                    /* Use the var functions to write some data. */
                    if ((ret = putget_write_var(ncid, varid, flavor[fmt])))
                        return ret;
                    break;

                case 1:
                    /* Use the var1 functions to write some data. */
                    if ((ret = putget_write_var1(ncid, varid, index, flavor[fmt])))
                        return ret;
                    break;

                case 2:
                    /* Use the vara functions to write some data. */
                    if ((ret = putget_write_vara(ncid, varid, start, count, flavor[fmt])))
                        return ret;
                    break;

                case 3:
                    /* Use the vara functions to write some data. */
                    if ((ret = putget_write_vars(ncid, varid, start, count, stride, flavor[fmt])))
                        return ret;
                    break;
                }

                /* Make sure all data are written (pnetcdf needs this). */
                if ((ret = PIOc_sync(ncid)))
                    return ret;

                switch (access)
                {
                case 0:
                    /* Use the vara functions to read some data. */
                    if ((ret = putget_read_var(ncid, varid, unlim, flavor[fmt])))
                        return ret;
                    break;

                case 1:
                    /* Use the var1 functions to read some data. */
                    if ((ret = putget_read_var1(ncid, varid, index, flavor[fmt])))
                        return ret;
                    break;

                case 2:
                    /* Use the vara functions to read some data. */
                    if ((ret = putget_read_vara(ncid, varid, start, count, flavor[fmt])))
                        return ret;
                    break;

                case 3:
                    /* Use the vara functions to read some data. */
                    if ((ret = putget_read_vars(ncid, varid, start, count, stride, flavor[fmt])))
                        return ret;
                    break;
                }

                /* Close the netCDF file. */
                printf("%d Closing the sample data file...\n", my_rank);
                if ((ret = PIOc_closefile(ncid)))
                    ERR(ret);

                /* Access to read it. */
                if ((ret = PIOc_openfile(iosysid, &ncid, &(flavor[fmt]), filename, PIO_NOWRITE)))
                    ERR(ret);

                switch (access)
                {
                case 0:
                    /* Use the vara functions to read some data. */
                    if ((ret = putget_read_var(ncid, varid, unlim, flavor[fmt])))
                        return ret;
                    break;

                case 1:
                    /* Use the var1 functions to read some data. */
                    if ((ret = putget_read_var1(ncid, varid, index, flavor[fmt])))
                        return ret;
                    break;

                case 2:
                    /* Use the vara functions to read some data. */
                    if ((ret = putget_read_vara(ncid, varid, start, count, flavor[fmt])))
                        return ret;
                    break;

                case 3:
                    /* Use the vara functions to read some data. */
                    if ((ret = putget_read_vars(ncid, varid, start, count, stride, flavor[fmt])))
                        return ret;
                    break;
                }

                /* Close the netCDF file. */
                printf("%d Closing the sample data file...\n", my_rank);
                if ((ret = PIOc_closefile(ncid)))
                    ERR(ret);

            } /* next flavor */
        } /* next access */

    return PIO_NOERR;
}

/* Test file operations.
 *
 * @param iosysid the iosystem ID that will be used for the test.
 * @param num_flavors the number of different IO types that will be tested.
 * @param flavor an array of the valid IO types.
 * @param my_rank 0-based rank of task.
 * @returns 0 for success, error code otherwise.
 */
int test_files(int iosysid, int num_flavors, int *flavor, int my_rank)
{
    int ncid;
    int ret;    /* Return code. */

    /* Use PIO to create the example file in each of the four
     * available ways. */
    for (int fmt = 0; fmt < num_flavors; fmt++)
    {
        char filename[PIO_MAX_NAME + 1]; /* Test filename. */
        char iotype_name[PIO_MAX_NAME + 1];

        /* Overwrite existing test file. */
        int mode = PIO_CLOBBER;

        /* If this is netCDF-4, add the netCDF4 flag. */
        if (flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
        {
            printf("%d adding NC_NETCDF4 flag\n", my_rank);
            mode |= NC_NETCDF4;
        }

        /* If this is pnetcdf or netCDF-4 parallel, add the MPIIO flag. */
        if (flavor[fmt] == PIO_IOTYPE_PNETCDF || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
        {
            printf("%d adding NC_MPIIO flag\n", my_rank);
            mode |= NC_MPIIO;
        }

        /* Create a filename. */
        if ((ret = get_iotype_name(flavor[fmt], iotype_name)))
            return ret;
        sprintf(filename, "%s_%s.nc", TEST_NAME, iotype_name);

        /* Create the netCDF output file. */
        printf("%d Creating sample file %s with format %d...\n",
               my_rank, filename, flavor[fmt]);
        if ((ret = PIOc_create(iosysid, filename, mode, &ncid)))
            ERR(ret);

        /* Define the test file metadata. */
        if ((ret = define_metadata(ncid, my_rank)))
            ERR(ret);

        /* End define mode. */
        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Close the netCDF file. */
        printf("%d Closing the sample data file...\n", my_rank);
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

        /* Reopen the test file. */
        printf("%d Re-opening sample file %s with format %d...\n",
               my_rank, filename, flavor[fmt]);
        if ((ret = PIOc_open(iosysid, filename, mode, &ncid)))
            ERR(ret);

        /* Check the test file metadata. */
        if ((ret = check_metadata(ncid, my_rank)))
            ERR(ret);

        /* Close the netCDF file. */
        printf("%d Closing the sample data file...\n", my_rank);
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

    }

    return PIO_NOERR;
}

/* Test the deletion of files.
 *
 * @param iosysid the iosystem ID that will be used for the test.
 * @param num_flavors the number of different IO types that will be tested.
 * @param flavor an array of the valid IO types.
 * @param my_rank 0-based rank of task.
 * @returns 0 for success, error code otherwise.
 */
int test_deletefile(int iosysid, int num_flavors, int *flavor, int my_rank)
{
    int ncid;
    int ret;    /* Return code. */

    /* Use PIO to create the example file in each of the four
     * available ways. */
    for (int fmt = 0; fmt < num_flavors; fmt++)
    {
        char filename[PIO_MAX_NAME + 1]; /* Test filename. */
        char iotype_name[PIO_MAX_NAME + 1];
        int old_method;

        /* Set error handling. */
        if ((ret = PIOc_set_iosystem_error_handling(iosysid, PIO_RETURN_ERROR, &old_method)))
            return ret;
        if (old_method != PIO_INTERNAL_ERROR && old_method != PIO_RETURN_ERROR)
            return ERR_WRONG;

        /* Create a filename. */
        if ((ret = get_iotype_name(flavor[fmt], iotype_name)))
            return ret;
        sprintf(filename, "delete_me_%s_%s.nc", TEST_NAME, iotype_name);

        printf("%d testing delete for file %s with format %d...\n",
               my_rank, filename, flavor[fmt]);
        if ((ret = PIOc_createfile(iosysid, &ncid, &(flavor[fmt]), filename, PIO_CLOBBER)))
            ERR(ret);

        /* End define mode. */
        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Close the netCDF file. */
        printf("%d Closing the sample data file...\n", my_rank);
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);

        /* Now delete the file. */
        printf("%d Deleting %s...\n", my_rank, filename);
        if ((ret = PIOc_deletefile(iosysid, filename)))
            ERR(ret);

        /* Make sure it is gone. Openfile will now return an error
         * code when I try to open the file. */
        if (!PIOc_openfile(iosysid, &ncid, &(flavor[fmt]), filename, PIO_NOWRITE))
            ERR(ERR_WRONG);
    }

    return PIO_NOERR;
}

/* Test the netCDF-4 optimization functions. */
int test_nc4(int iosysid, int num_flavors, int *flavor, int my_rank)
{
    int ncid;    /* The ncid of the netCDF file. */
    int dimids[NDIM];    /* The dimension IDs. */
    int varid;    /* The ID of the netCDF varable. */

    /* For setting the chunk cache. */
    PIO_Offset chunk_cache_size = 1024*1024;
    PIO_Offset chunk_cache_nelems = 1024;
    float chunk_cache_preemption = 0.5;

    /* For reading the chunk cache. */
    PIO_Offset chunk_cache_size_in;
    PIO_Offset chunk_cache_nelems_in;
    float chunk_cache_preemption_in;

    int storage = NC_CHUNKED; /* Storage of netCDF-4 files (contiguous vs. chunked). */
    PIO_Offset my_chunksize[NDIM]; /* Chunksizes we get from file. */
    int shuffle;    /* The shuffle filter setting in the netCDF-4 test file. */
    int deflate;    /* Non-zero if deflate set for the variable in the netCDF-4 test file. */
    int deflate_level;    /* The deflate level set for the variable in the netCDF-4 test file. */
    int endianness;    /* Endianness of variable. */
    PIO_Offset var_cache_size;    /* Size of the var chunk cache. */
    PIO_Offset var_cache_nelems; /* Number of elements in var cache. */
    float var_cache_preemption;     /* Var cache preemption. */
    char varname_in[PIO_MAX_NAME];
    int expected_ret; /* The return code we expect to get. */
    int ret;    /* Return code. */

    /* Use PIO to create the example file in each of the four
     * available ways. */
    for (int fmt = 0; fmt < num_flavors; fmt++)
    {
        char filename[PIO_MAX_NAME + 1]; /* Test filename. */
        char iotype_name[PIO_MAX_NAME + 1];

        /* Create a filename. */
        if ((ret = get_iotype_name(flavor[fmt], iotype_name)))
            return ret;
        sprintf(filename, "%s_%s.nc", TEST_NAME, iotype_name);

        printf("%d Setting chunk cache for file %s with format %d...\n",
               my_rank, filename, flavor[fmt]);

        /* Try to set the chunk cache with invalid preemption to check
         * error handling. Can't do this because correct bahavior is
         * to MPI_Abort, and code now does that. But how to test? */
        /* chunk_cache_preemption = 50.0; */
        /* ret = PIOc_set_chunk_cache(iosysid, flavor[fmt], chunk_cache_size, */
        /*                            chunk_cache_nelems, chunk_cache_preemption); */

        /* printf("%d Set chunk cache ret = %d.\n", my_rank, ret); */

        /* /\* What result did we expect to get? *\/ */
        /* expected_ret = flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P ? */
        /*     NC_EINVAL : NC_ENOTNC4; */

        /* /\* Check the result. *\/ */
        /* if (ret != expected_ret) */
        /*     ERR(ERR_AWFUL); */

        /* Try to set the chunk cache for netCDF-4 iotypes. */
        chunk_cache_preemption = 0.5;
        if (flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
            if ((ret = PIOc_set_chunk_cache(iosysid, flavor[fmt], chunk_cache_size,
                                            chunk_cache_nelems, chunk_cache_preemption)))
                ERR(ERR_AWFUL);

        /* Now check the chunk cache. */
        if (flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
        {
            if ((ret = PIOc_get_chunk_cache(iosysid, flavor[fmt], &chunk_cache_size_in,
                                            &chunk_cache_nelems_in, &chunk_cache_preemption_in)))
                ERR(ERR_AWFUL);

            /* Check that we got the correct values. */
            if (chunk_cache_size_in != chunk_cache_size || chunk_cache_nelems_in != chunk_cache_nelems ||
                chunk_cache_preemption_in != chunk_cache_preemption)
                ERR(ERR_AWFUL);
        }

        /* Create the netCDF output file. */
        printf("%d Creating sample file %s with format %d...\n",
               my_rank, filename, flavor[fmt]);
        if ((ret = PIOc_createfile(iosysid, &ncid, &(flavor[fmt]), filename, PIO_CLOBBER)))
            ERR(ret);

        /* Define netCDF dimensions and variable. */
        printf("%d Defining netCDF metadata...\n", my_rank);
        for (int d = 0; d < NDIM; d++)
        {
            printf("%d Defining netCDF dimension %s, length %d\n", my_rank,
                   dim_name[d], dim_len[d]);
            if ((ret = PIOc_def_dim(ncid, dim_name[d], (PIO_Offset)dim_len[d], &dimids[d])))
                ERR(ret);
        }
        printf("%d Defining netCDF variable %s, ndims %d\n", my_rank, VAR_NAME, NDIM);
        if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, &varid)))
            ERR(ret);

        /* For netCDF-4 files, set the chunksize to improve performance. */
        if (flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
        {
            printf("%d Defining chunksizes\n", my_rank);
            if ((ret = PIOc_def_var_chunking(ncid, 0, NC_CHUNKED, chunksize)))
                ERR(ret);

            /* Check that the inq_varname function works. */
            printf("%d Checking varname\n", my_rank);
            ret = PIOc_inq_varname(ncid, 0, varname_in);
            printf("%d ret: %d varname_in: %s\n", my_rank, ret, varname_in);

            /* Check that the inq_var_chunking function works. */
            printf("%d Checking chunksizes\n", my_rank);
            if ((ret = PIOc_inq_var_chunking(ncid, 0, &storage, my_chunksize)))
                ERR(ret);

            /* Check the answers. */
            if (storage != NC_CHUNKED)
                ERR(ERR_AWFUL);
            for (int d1 = 0; d1 < NDIM; d1++)
                if (my_chunksize[d1] != chunksize[d1])
                    ERR(ERR_AWFUL);

            /* Check that the inq_var_deflate functions works. */
            if ((ret = PIOc_inq_var_deflate(ncid, 0, &shuffle, &deflate, &deflate_level)))
                ERR(ret);

            /* For serial netCDF-4 deflate is turned on by default */
            if (flavor[fmt] == PIO_IOTYPE_NETCDF4C)
                if (shuffle || !deflate || deflate_level != 1)
                    ERR(ERR_AWFUL);

            /* For parallel netCDF-4, no compression available. :-( */
            if (flavor[fmt] == PIO_IOTYPE_NETCDF4P)
                if (shuffle || deflate)
                    ERR(ERR_AWFUL);

            /* Check setting the chunk cache for the variable. */
            printf("%d PIOc_set_var_chunk_cache...\n", my_rank);
            if ((ret = PIOc_set_var_chunk_cache(ncid, 0, VAR_CACHE_SIZE, VAR_CACHE_NELEMS,
                                                VAR_CACHE_PREEMPTION)))
                ERR(ret);

            /* Check getting the chunk cache values for the variable. */
            printf("%d PIOc_get_var_chunk_cache...\n", my_rank);
            if ((ret = PIOc_get_var_chunk_cache(ncid, 0, &var_cache_size, &var_cache_nelems,
                                                &var_cache_preemption)))
                ERR(ret);

            /* Check that we got expected values. */
            printf("%d var_cache_size = %d\n", my_rank, var_cache_size);
            if (var_cache_size != VAR_CACHE_SIZE)
                ERR(ERR_AWFUL);
            if (var_cache_nelems != VAR_CACHE_NELEMS)
                ERR(ERR_AWFUL);
            if (var_cache_preemption != VAR_CACHE_PREEMPTION)
                ERR(ERR_AWFUL);

            if ((ret = PIOc_def_var_endian(ncid, 0, 1)))
                ERR(ERR_AWFUL);
            if ((ret = PIOc_inq_var_endian(ncid, 0, &endianness)))
                ERR(ERR_AWFUL);
            if (endianness != 1)
                ERR(ERR_WRONG);

    /*     } */
    /*     else */
    /*     { */
    /*         /\* Trying to set or inq netCDF-4 settings for non-netCDF-4 */
    /*          * files results in the PIO_ENOTNC4 error. *\/ */
    /*         if ((ret = PIOc_def_var_chunking(ncid, 0, NC_CHUNKED, chunksize)) != PIO_ENOTNC4) */
    /*             ERR(ERR_AWFUL); */
    /*         /\* if ((ret = PIOc_inq_var_chunking(ncid, 0, &storage, my_chunksize)) != PIO_ENOTNC4) *\/ */
    /*         /\*     ERR(ERR_AWFUL); *\/ */
    /*         if ((ret = PIOc_inq_var_deflate(ncid, 0, &shuffle, &deflate, &deflate_level)) */
    /*             != PIO_ENOTNC4) */
    /*             ERR(ret); */
    /*         if ((ret = PIOc_def_var_endian(ncid, 0, 1)) != PIO_ENOTNC4) */
    /*             ERR(ERR_AWFUL); */
    /*         if ((ret = PIOc_inq_var_endian(ncid, 0, &endianness)) != PIO_ENOTNC4) */
    /*             ERR(ERR_AWFUL); */
    /*         if ((ret = PIOc_set_var_chunk_cache(ncid, 0, VAR_CACHE_SIZE, VAR_CACHE_NELEMS, */
    /*                                             VAR_CACHE_PREEMPTION)) != PIO_ENOTNC4) */
    /*             ERR(ret); */
    /*         if ((ret = PIOc_get_var_chunk_cache(ncid, 0, &var_cache_size, &var_cache_nelems, */
    /*                                             &var_cache_preemption)) != PIO_ENOTNC4) */
    /*             ERR(ret); */
    /*         if ((ret = PIOc_set_chunk_cache(iosysid, flavor[fmt], chunk_cache_size, chunk_cache_nelems, */
    /*                                         chunk_cache_preemption)) != PIO_ENOTNC4) */
    /*             ERR(ret); */
    /*         if ((ret = PIOc_get_chunk_cache(iosysid, flavor[fmt], &chunk_cache_size, */
    /*                                         &chunk_cache_nelems, &chunk_cache_preemption)) != PIO_ENOTNC4) */
    /*             ERR(ret); */
        }

        /* End define mode. */
        if ((ret = PIOc_enddef(ncid)))
            ERR(ret);

        /* Close the netCDF file. */
        printf("%d Closing the sample data file...\n", my_rank);
        if ((ret = PIOc_closefile(ncid)))
            ERR(ret);
    }
    return PIO_NOERR;
}

/* Run all the tests. */
int test_all(int iosysid, int num_flavors, int *flavor, int my_rank, MPI_Comm test_comm,
             int async)
{
    int ioid;
    int my_test_size;
    int ret; /* Return code. */

    if ((ret = MPI_Comm_size(test_comm, &my_test_size)))
        MPIERR(ret);

    /* Test read/write stuff. */
    printf("%d Testing putget. async = %d\n", my_rank, async);
    if ((ret = test_putget(iosysid, num_flavors, flavor, my_rank, test_comm)))
        return ret;

    if (!async)
    {
        /* Decompose the data over the tasks. */
        if ((ret = create_decomposition(my_test_size, my_rank, iosysid, &ioid)))
            return ret;

        if ((ret = test_darray(iosysid, ioid, num_flavors, flavor, my_rank)))
            return ret;

        /* Free the PIO decomposition. */
        if ((ret = PIOc_freedecomp(iosysid, ioid)))
            ERR(ret);
    }


    /* Check the error string function. */
    printf("%d Testing streror. async = %d\n", my_rank, async);
    if ((ret = check_strerror(my_rank)))
        ERR(ret);

    /* Test file stuff. */
    printf("%d Testing file creation. async = %d\n", my_rank, async);
    if ((ret = test_files(iosysid, num_flavors, flavor, my_rank)))
        return ret;

    /* Test file deletes. */
    printf("%d Testing deletefile. async = %d\n", my_rank, async);
    if ((ret = test_deletefile(iosysid, num_flavors, flavor, my_rank)))
        return ret;

    /* Test name stuff. */
    printf("%d Testing names. async = %d\n", my_rank, async);
    if ((ret = test_names(iosysid, num_flavors, flavor, my_rank, test_comm)))
        return ret;

    /* Test netCDF-4 functions. */
    printf("%d Testing nc4 functions. async = %d\n", my_rank, async);
    if ((ret = test_nc4(iosysid, num_flavors, flavor, my_rank)))
        return ret;

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
int test_no_async(int my_rank, int num_flavors, int *flavor, MPI_Comm test_comm)
{
    int niotasks;    /* Number of processors that will do IO. */
    int ioproc_stride = 1;    /* Stride in the mpi rank between io tasks. */
    int numAggregator = 0;    /* Number of the aggregator? Always 0 in this test. */
    int ioproc_start = 0;     /* Zero based rank of first processor to be used for I/O. */
    PIO_Offset elements_per_pe; /* Array index per processing unit. */
    int iosysid;  /* The ID for the parallel I/O system. */
    int ioid;     /* The I/O description ID. */
    PIO_Offset *compdof; /* The decomposition mapping. */
    int ret;      /* Return code. */

    /* keep things simple - 1 iotask per MPI process */
    niotasks = TARGET_NTASKS;

    /* Initialize the PIO IO system. This specifies how
     * many and which processors are involved in I/O. */
    if ((ret = PIOc_Init_Intracomm(test_comm, niotasks, ioproc_stride,
                                   ioproc_start, PIO_REARR_SUBSET, &iosysid)))
        ERR(ret);

    /* Describe the decomposition. This is a 1-based array, so add 1! */
    elements_per_pe = X_DIM_LEN * Y_DIM_LEN / TARGET_NTASKS;
    if (!(compdof = malloc(elements_per_pe * sizeof(PIO_Offset))))
        return PIO_ENOMEM;
    for (int i = 0; i < elements_per_pe; i++)
        compdof[i] = my_rank * elements_per_pe + i + 1;

    /* Create the PIO decomposition for this test. */
    printf("%d Creating decomposition...\n", my_rank);
    if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, 2, &dim_len[1], (PIO_Offset)elements_per_pe,
                               compdof, &ioid, NULL, NULL, NULL)))
        ERR(ret);
    free(compdof);

    /* Run tests. */
    printf("%d Running tests...\n", my_rank);
    if ((ret = test_all(iosysid, num_flavors, flavor, my_rank, test_comm, 0)))
        return ret;

    /* Free the PIO decomposition. */
    printf("%d Freeing PIO decomposition...\n", my_rank);
    if ((ret = PIOc_freedecomp(iosysid, ioid)))
        ERR(ret);

    /* Finalize PIO system. */
    if ((ret = PIOc_finalize(iosysid)))
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
int test_async(int my_rank, int num_flavors, int *flavor, MPI_Comm test_comm)
{
    int niotasks;            /* Number of processors that will do IO. */
    int ioproc_stride = 1;   /* Stride in the mpi rank between io tasks. */
    int ioproc_start = 0;    /* 0 based rank of first task to be used for I/O. */
    PIO_Offset elements_per_pe;    /* Array index per processing unit. */
    int iosysid[COMPONENT_COUNT];  /* The ID for the parallel I/O system. */
    int ioid;                      /* The I/O description ID. */
    PIO_Offset *compdof;           /* The decomposition mapping. */
    int num_procs[COMPONENT_COUNT + 1] = {1, TARGET_NTASKS - 1}; /* Num procs in each component. */
    MPI_Comm io_comm;              /* Will get a duplicate of IO communicator. */
    MPI_Comm comp_comm[COMPONENT_COUNT]; /* Will get duplicates of computation communicators. */
    int mpierr;  /* Return code from MPI functions. */
    int ret;     /* Return code. */

    /* Is the current process a computation task? */
    int comp_task = my_rank < NUM_IO_PROCS ? 0 : 1;
    printf("%d comp_task = %d\n", my_rank, comp_task);

    /* Initialize the IO system. */
    if ((ret = PIOc_Init_Async(test_comm, NUM_IO_PROCS, NULL, COMPONENT_COUNT,
                               num_procs, NULL, &io_comm, comp_comm, iosysid)))
        ERR(ERR_INIT);
    for (int c = 0; c < COMPONENT_COUNT; c++)
        printf("%d iosysid[%d] = %d\n", my_rank, c, iosysid[c]);

    /* All the netCDF calls are only executed on the computation
     * tasks. The IO tasks have not returned from PIOc_Init_Intercomm,
     * and when the do, they should go straight to finalize. */
    if (comp_task)
    {
        for (int c = 0; c < COMPONENT_COUNT; c++)
        {
            printf("%d Running tests...\n", my_rank);
            if ((ret = test_all(iosysid[c], num_flavors, flavor, my_rank, comp_comm[0], 1)))
                return ret;

            /* Finalize the IO system. Only call this from the computation tasks. */
            printf("%d %s Freeing PIO resources\n", my_rank, TEST_NAME);
            if ((ret = PIOc_finalize(iosysid[c])))
                ERR(ret);
            printf("%d %s PIOc_finalize completed for iosysid = %d\n", my_rank, TEST_NAME,
                   iosysid[c]);
            if ((mpierr = MPI_Comm_free(&comp_comm[c])))
                MPIERR(mpierr);
        }
    }
    else
    {
        if ((mpierr = MPI_Comm_free(&io_comm)))
            MPIERR(mpierr);
    } /* endif comp_task */

    return PIO_NOERR;
}

/* Run Tests for NetCDF-4 Functions. */
int main(int argc, char **argv)
{
    int my_rank;     /* Zero-based rank of processor. */
    int ntasks;      /* Number of processors involved in current execution. */
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    MPI_Comm test_comm; /* A communicator for this test. */
    int ret;         /* Return code. */

    /* Initialize data arrays with sample data. */
    init_arrays();

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS,
                              TARGET_NTASKS, 0, &test_comm)))
        ERR(ERR_INIT);

    /* Only do something on TARGET_NTASKS tasks. */
    if (my_rank < TARGET_NTASKS)
    {
        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);

        /* Run tests without async feature. */
        if ((ret = test_no_async(my_rank, num_flavors, flavor, test_comm)))
            return ret;

        /* Run tests with async. */
        if ((ret = test_async(my_rank, num_flavors, flavor, test_comm)))
            return ret;

    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
