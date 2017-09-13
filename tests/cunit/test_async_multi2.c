/*
 * This tests async with multiple computation components. This is a
 * more comprehensive test than test_async_multicomp.c.
 *
 * @author Ed Hartnett
 * @date 9/12/17
 */
#include <config.h>
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 3

/* The name of this test. */
#define TEST_NAME "test_async_multi2"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of tasks in each computation component. */
#define NUM_COMP_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 2

/* Number of dims in test file. */
#define NDIM2 2
#define NDIM3 3

/* Number of vars in test file. */
#define NVAR2 2

/* The names of the variables created in test file. */
#define SCALAR_VAR_NAME "scalar_var"
#define THREED_VAR_NAME "threed_var"

/* Used to create dimension names. */
#define DIM_NAME "dim"

/* Dimension lengths. */
#define DIM_X_LEN 2
#define DIM_Y_LEN 3

/* Attribute name. */
#define GLOBAL_ATT_NAME "global_att"

/* Length of all attributes. */
#define ATT_LEN 3

#ifdef _NETCDF4
#define NUM_TYPES_TO_TEST 11
int pio_type[NUM_TYPES_TO_TEST] = {PIO_BYTE, PIO_CHAR, PIO_SHORT, PIO_INT, PIO_FLOAT, PIO_DOUBLE,
                                   PIO_UBYTE, PIO_USHORT, PIO_UINT, PIO_INT64, PIO_UINT64};
#else
#define NUM_TYPES_TO_TEST 6
int pio_type[NUM_TYPES_TO_TEST] = {PIO_BYTE, PIO_CHAR, PIO_SHORT, PIO_INT, PIO_FLOAT, PIO_DOUBLE};
#endif /* _NETCDF4 */

/* Attribute test data. */
signed char byte_att_data[ATT_LEN] = {NC_MAX_BYTE, NC_MIN_BYTE, NC_MAX_BYTE};
char char_att_data[ATT_LEN] = {NC_MAX_CHAR, 0, NC_MAX_CHAR};
short short_att_data[ATT_LEN] = {NC_MAX_SHORT, NC_MIN_SHORT, NC_MAX_SHORT};
int int_att_data[ATT_LEN] = {NC_MAX_INT, NC_MIN_INT, NC_MAX_INT};
float float_att_data[ATT_LEN] = {NC_MAX_FLOAT, NC_MIN_FLOAT, NC_MAX_FLOAT};
double double_att_data[ATT_LEN] = {NC_MAX_DOUBLE, NC_MIN_DOUBLE, NC_MAX_DOUBLE};
#ifdef _NETCDF4
unsigned char ubyte_att_data[ATT_LEN] = {NC_MAX_UBYTE, 0, NC_MAX_UBYTE};
unsigned short ushort_att_data[ATT_LEN] = {NC_MAX_USHORT, 0, NC_MAX_USHORT};
unsigned int uint_att_data[ATT_LEN] = {NC_MAX_UINT, 0, NC_MAX_UINT};
long long int64_att_data[ATT_LEN] = {NC_MAX_INT64, NC_MIN_INT64, NC_MAX_INT64};
unsigned long long uint64_att_data[ATT_LEN] = {NC_MAX_UINT64, 0, NC_MAX_UINT64};
#endif /* _NETCDF4 */

/* Pointers to the data. */
#ifdef _NETCDF4
void *att_data[NUM_TYPES_TO_TEST] = {&byte_att_data, &char_att_data, &short_att_data,
                                     int_att_data, float_att_data, double_att_data,
                                     ubyte_att_data, ushort_att_data, uint_att_data,
                                     int64_att_data, uint64_att_data};
#else
void *att_data[NUM_TYPES_TO_TEST] = {&byte_att_data, &char_att_data, &short_att_data,
                                     int_att_data, float_att_data, double_att_data};
#endif /* _NETCDF4 */



/* Check a test file for correctness. */
int check_test_file(int iosysid, int iotype, int my_rank, int my_comp_idx,
                    const char *filename, int verbose, int num_types)
{
    int ncid;
    int nvars;
    int ndims;
    int ngatts;
    int unlimdimid;
    /* PIO_Offset att_len; */
    /* char att_name[PIO_MAX_NAME + 1]; */
    char var_name[PIO_MAX_NAME + 1];
    char var_name_expected[PIO_MAX_NAME + 1];
    int dimid[NDIM2];
    int xtype;
    int natts;
    int comp_idx_in;
    short data_2d[DIM_X_LEN * DIM_Y_LEN];
    int ret;

    /* Open the test file. */
    if ((ret = PIOc_openfile2(iosysid, &ncid, &iotype, filename, PIO_NOWRITE)))
        ERR(ret);

    /* Check file metadata. */
    if ((ret = PIOc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid)))
        ERR(ret);
    if (ndims != NDIM3 || nvars != 2 || ngatts != num_types || unlimdimid != 0)
        ERR(ERR_WRONG);

    /* Check the global attributes. */
    for (int t = 0; t < num_types; t++)
    {
        PIO_Offset type_size;
        PIO_Offset att_len_in;
        void *att_data_in;
        char att_name[PIO_MAX_NAME + 1];
        
        sprintf(att_name, "%s_cmp_%d_type_%d", GLOBAL_ATT_NAME, my_comp_idx, pio_type[t]);
        if ((ret = PIOc_inq_att(ncid, NC_GLOBAL, att_name, &xtype, &att_len_in)))
            ERR(ret);
        if (xtype != pio_type[t] || att_len_in != ATT_LEN)
            ERR(ERR_WRONG);
        if ((ret = PIOc_inq_type(ncid, xtype, NULL, &type_size)))
            ERR(ret);
        if (!(att_data_in = malloc(type_size * ATT_LEN)))
            ERR(ERR_AWFUL);
        if (verbose)
            printf("my_rank %d t %d pio_type[t] %d type_size %lld\n", my_rank, t, pio_type[t],
                   type_size);
        if ((ret = PIOc_get_att(ncid, PIO_GLOBAL, att_name, att_data_in)))
            ERR(ret);
        if (memcmp(att_data_in, att_data[t], type_size * ATT_LEN))
            ERR(ERR_WRONG);
        free(att_data_in);
    }

    /* Check the scalar variable metadata. */
    if ((ret = PIOc_inq_var(ncid, 0, var_name, &xtype, &ndims, NULL, &natts)))
        ERR(ret);
    sprintf(var_name_expected, "%s_%d", SCALAR_VAR_NAME, my_comp_idx);
    if (strcmp(var_name, var_name_expected) || xtype != PIO_INT || ndims != 0 || natts != 0)
        ERR(ERR_WRONG);

    /* Check the scalar variable data. */
    if ((ret = PIOc_get_var_int(ncid, 0, &comp_idx_in)))
        ERR(ret);
    if (comp_idx_in != my_comp_idx)
        ERR(ERR_WRONG);

    /* /\* Check the 2D variable metadata. *\/ */
    /* if ((ret = PIOc_inq_var(ncid, 1, var_name, &xtype, &ndims, dimid, &natts))) */
    /*     ERR(ret); */
    /* sprintf(var_name_expected, "%s_%d", THREED_VAR_NAME, my_comp_idx); */
    /* if (strcmp(var_name, var_name_expected) || xtype != PIO_SHORT || ndims != 2 || natts != 0) */
    /*     ERR(ERR_WRONG); */

    /* /\* Read the 2-D variable. *\/ */
    /* if ((ret = PIOc_get_var_short(ncid, 1, data_2d))) */
    /*     ERR(ret); */

    /* /\* Check 2D data for correctness. *\/ */
    /* for (int i = 0; i < DIM_X_LEN * DIM_Y_LEN; i++) */
    /*     if (data_2d[i] != my_comp_idx + i) */
    /*         ERR(ERR_WRONG); */

    /* Close the test file. */
    if ((ret = PIOc_closefile(ncid)))
        ERR(ret);
    return 0;
}

/* This creates an empty netCDF file in the specified format. */
int create_test_file(int iosysid, int iotype, int my_rank, int my_comp_idx,
                     char *filename, int verbose, int num_types)
{
    char iotype_name[NC_MAX_NAME + 1];
    int ncid;
    int varid[NVAR2];
    char att_name[PIO_MAX_NAME + 1];
    char var_name[PIO_MAX_NAME + 1];
    char dim_name[PIO_MAX_NAME + 1];
    int dimid[NDIM3];
    int dim_len[NDIM3] = {PIO_UNLIMITED, DIM_X_LEN, DIM_Y_LEN};
    short data_2d[DIM_X_LEN * DIM_Y_LEN];
    int ret;

    /* Learn name of IOTYPE. */
    if ((ret = get_iotype_name(iotype, iotype_name)))
        ERR(ret);
    
    /* Create a filename. */
    sprintf(filename, "%s_%s_cmp_%d.nc", TEST_NAME, iotype_name, my_comp_idx);
    if (verbose)
        printf("my_rank %d creating test file %s for iosysid %d\n", my_rank, filename, iosysid);

    /* Create the file. */
    if ((ret = PIOc_createfile(iosysid, &ncid, &iotype, filename, NC_CLOBBER)))
        ERR(ret);

    /* Create a global attributes of all types. */
    for (int t = 0; t < num_types; t++)
    {
        sprintf(att_name, "%s_cmp_%d_type_%d", GLOBAL_ATT_NAME, my_comp_idx, pio_type[t]);
        if ((ret = PIOc_put_att(ncid, PIO_GLOBAL, att_name, pio_type[t], ATT_LEN, att_data[t])))
            ERR(ret);
    }

    /* Define a scalar variable. */
    sprintf(var_name, "%s_%d", SCALAR_VAR_NAME, my_comp_idx);
    if ((ret = PIOc_def_var(ncid, var_name, PIO_INT, 0, NULL, &varid[0])))
        ERR(ret);

    /* Define dimensions. */
    for (int d = 0; d < NDIM3; d++)
    {
        sprintf(dim_name, "%s_%d_cmp_%d", DIM_NAME, d, my_comp_idx);
        if ((ret = PIOc_def_dim(ncid, dim_name, dim_len[d], &dimid[d])))
            ERR(ret);
    }

    /* Define a 3D variable. */
    sprintf(var_name, "%s_%d", THREED_VAR_NAME, my_comp_idx);
    if ((ret = PIOc_def_var(ncid, var_name, PIO_SHORT, NDIM2, dimid, &varid[1])))
        ERR(ret);

    /* End define mode. */
    if ((ret = PIOc_enddef(ncid)))
        ERR(ret);

    /* Write the scalar variable. */
    if ((ret = PIOc_put_var_int(ncid, 0, &my_comp_idx)))
        ERR(ret);

    /* Write the 2-D variable. */
    /* for (int i = 0; i < DIM_X_LEN * DIM_Y_LEN; i++) */
    /*     data_2d[i] = my_comp_idx + i; */
    /* if ((ret = PIOc_put_var_short(ncid, 1, data_2d))) */
    /*     ERR(ret); */

    /* Close the file if ncidp was not provided. */
    if ((ret = PIOc_closefile(ncid)))
        ERR(ret);

    return PIO_NOERR;
}

/* Run simple async test. */
int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid[COMPONENT_COUNT]; /* The ID for the parallel I/O system. */
    int num_iotypes; /* Number of PIO netCDF iotypes in this build. */
    int iotype[NUM_IOTYPES]; /* iotypes for the supported netCDF IO iotypes. */
    int num_procs[COMPONENT_COUNT] = {1, 1}; /* Num procs for IO and computation. */
    int io_proc_list[NUM_IO_PROCS] = {0};
    int comp_proc_list1[NUM_COMP_PROCS] = {1};
    int comp_proc_list2[NUM_COMP_PROCS] = {2};
    int *proc_list[COMPONENT_COUNT] = {comp_proc_list1, comp_proc_list2};
    MPI_Comm test_comm;
    int verbose = 1;
    int ret; /* Return code. */

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, TARGET_NTASKS, TARGET_NTASKS,
                              3, &test_comm)))
        ERR(ERR_INIT);

    /* Is the current process a computation task? */    
    int comp_task = my_rank < NUM_IO_PROCS ? 0 : 1;
    
    /* Only do something on TARGET_NTASKS tasks. */
    if (my_rank < TARGET_NTASKS)
    {
        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_iotypes, iotype)))
            ERR(ret);

        /* Initialize the IO system. The IO task will not return from
         * this call, but instead will go into a loop, listening for
         * messages. */
        if ((ret = PIOc_init_async(test_comm, NUM_IO_PROCS, io_proc_list, COMPONENT_COUNT,
                                   num_procs, (int **)proc_list, NULL, NULL, PIO_REARR_BOX, iosysid)))
            ERR(ERR_INIT);
        if (verbose)
            for (int c = 0; c < COMPONENT_COUNT; c++)
                printf("my_rank %d cmp %d iosysid[%d] %d\n", my_rank, c, c, iosysid[c]);

        /* All the netCDF calls are only executed on the computation
         * tasks. */
        if (comp_task)
        {
            for (int i = 0; i < num_iotypes; i++)
            {
                char filename[NC_MAX_NAME + 1]; /* Test filename. */
                int my_comp_idx = my_rank - 1; /* Index in iosysid array. */
                int num_types = (iotype[i] == PIO_IOTYPE_NETCDF4C ||
                                 iotype[i] == PIO_IOTYPE_NETCDF4P) ? NUM_NETCDF_TYPES - 1 : NUM_CLASSIC_TYPES;

                /* Create sample file. */
                if ((ret = create_test_file(iosysid[my_comp_idx], iotype[i], my_rank, my_comp_idx,
                                            filename, verbose, num_types)))
                    ERR(ret);

                /* Check the file for correctness. */
                if ((ret = check_test_file(iosysid[my_comp_idx], iotype[i], my_rank, my_comp_idx,
                                           filename, verbose, num_types)))
                    ERR(ret);
            } /* next netcdf iotype */

            /* Finalize the IO system. Only call this from the computation tasks. */
            for (int c = 0; c < COMPONENT_COUNT; c++)
                if ((ret = PIOc_finalize(iosysid[c])))
                    ERR(ret);
        } /* endif comp_task */
    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize test. */
    if ((ret = pio_test_finalize(&test_comm)))
        return ERR_AWFUL;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
