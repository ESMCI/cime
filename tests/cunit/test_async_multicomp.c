/*
 * This tests async with multiple computation components.
 *
 * @author Ed Hartnett
 * @date 8/25/17
 */
#include <config.h>
#include <pio.h>
#include <pio_tests.h>
#include <unistd.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 3

/* The name of this test. */
#define TEST_NAME "test_async_multicomp"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of tasks in each computation component. */
#define NUM_COMP_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 2

/* Number of dims in test file. */
#define NDIM2 2

/* Number of vars in test file. */
#define NVAR2 2

/* The names of the variables created in test file. */
#define SCALAR_VAR_NAME "scalar_var"
#define TWOD_VAR_NAME "twod_var"

/* Used to create dimension names. */
#define DIM_NAME "dim_name"

/* Dimension lengths. */
#define DIM_0_LEN 2
#define DIM_1_LEN 3

/* Attribute name. */
#define GLOBAL_ATT_NAME "global_att_name"

/* Check a test file for correctness. */
int check_test_file(int iosysid, int iotype, int my_rank, int my_comp_idx,
                    const char *filename)
{
    int ncid;
    int nvars;
    int ndims;
    int ngatts;
    int unlimdimid;
    PIO_Offset att_len;
    char att_name[PIO_MAX_NAME + 1];
    char var_name[PIO_MAX_NAME + 1];
    char var_name_expected[PIO_MAX_NAME + 1];
    int dimid[NDIM2];
    int xtype;
    int natts;
    int comp_idx_in;
    short data_2d[DIM_0_LEN * DIM_1_LEN];
    signed char att_data;
    int ret;

    /* Open the test file. */
    if ((ret = PIOc_openfile2(iosysid, &ncid, &iotype, filename, PIO_NOWRITE)))
        ERR(ret);

    /* Check file metadata. */
    if ((ret = PIOc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid)))
        ERR(ret);
    if (ndims != 2 || nvars != 2 || ngatts != 1 || unlimdimid != -1)
        ERR(ERR_WRONG);

    /* Check the global attribute. */
    sprintf(att_name, "%s_%d", GLOBAL_ATT_NAME, my_comp_idx);
    if ((ret = PIOc_inq_att(ncid, NC_GLOBAL, att_name, &xtype, &att_len)))
        ERR(ret);
    if (xtype != PIO_BYTE || att_len != 1)
        ERR(ERR_WRONG);
    if ((ret = PIOc_get_att_schar(ncid, PIO_GLOBAL, att_name, &att_data)))
        ERR(ret);
    if (att_data != my_comp_idx)
        ERR(ERR_WRONG);

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

    /* Check the 2D variable metadata. */
    if ((ret = PIOc_inq_var(ncid, 1, var_name, &xtype, &ndims, dimid, &natts)))
        ERR(ret);
    sprintf(var_name_expected, "%s_%d", TWOD_VAR_NAME, my_comp_idx);
    if (strcmp(var_name, var_name_expected) || xtype != PIO_SHORT || ndims != 2 || natts != 0)
        ERR(ERR_WRONG);

    /* Read the 2-D variable. */
    if ((ret = PIOc_get_var_short(ncid, 1, data_2d)))
        ERR(ret);

    /* Check 2D data for correctness. */
    for (int i = 0; i < DIM_0_LEN * DIM_1_LEN; i++)
        if (data_2d[i] != my_comp_idx + i)
            ERR(ERR_WRONG);

    /* Close the test file. */
    if ((ret = PIOc_closefile(ncid)))
        ERR(ret);
    return 0;
}

/* This creates an empty netCDF file in the specified format. */
int create_test_file(int iosysid, int iotype, int my_rank, int my_comp_idx, char *filename)
{
    char iotype_name[NC_MAX_NAME + 1];
    int ncid;
    signed char my_char_comp_idx = my_comp_idx;
    int varid[NVAR2];
    char att_name[PIO_MAX_NAME + 1];
    char var_name[PIO_MAX_NAME + 1];
    char dim_name[PIO_MAX_NAME + 1];
    int dimid[NDIM2];
    int dim_len[NDIM2] = {DIM_0_LEN, DIM_1_LEN};
    short data_2d[DIM_0_LEN * DIM_1_LEN];
    int ret;

    /* Learn name of IOTYPE. */
    if ((ret = get_iotype_name(iotype, iotype_name)))
        ERR(ret);
    
    /* Create a filename. */
    sprintf(filename, "%s_%s_cmp_%d.nc", TEST_NAME, iotype_name, my_comp_idx);
    printf("my_rank %d creating test file %s for iosysid %d\n", my_rank, filename, iosysid);

    /* Create the file. */
    if ((ret = PIOc_createfile(iosysid, &ncid, &iotype, filename, NC_CLOBBER)))
        ERR(ret);

    /* Create a global attribute. */
    sprintf(att_name, "%s_%d", GLOBAL_ATT_NAME, my_comp_idx);
    if ((ret = PIOc_put_att_schar(ncid, PIO_GLOBAL, att_name, PIO_BYTE, 1, &my_char_comp_idx)))
        ERR(ret);

    /* Define a scalar variable. */
    sprintf(var_name, "%s_%d", SCALAR_VAR_NAME, my_comp_idx);
    if ((ret = PIOc_def_var(ncid, var_name, PIO_INT, 0, NULL, &varid[0])))
        ERR(ret);

    /* Define two dimensions. */
    for (int d = 0; d < NDIM2; d++)
    {
        sprintf(dim_name, "%s_%d_cmp_%d", DIM_NAME, d, my_comp_idx);
        if ((ret = PIOc_def_dim(ncid, dim_name, dim_len[d], &dimid[d])))
            ERR(ret);
    }

    /* Define a 2D variable. */
    sprintf(var_name, "%s_%d", TWOD_VAR_NAME, my_comp_idx);
    if ((ret = PIOc_def_var(ncid, var_name, PIO_SHORT, NDIM2, dimid, &varid[1])))
        ERR(ret);

    /* End define mode. */
    if ((ret = PIOc_enddef(ncid)))
        ERR(ret);

    /* Write the scalar variable. */
    if ((ret = PIOc_put_var_int(ncid, 0, &my_comp_idx)))
        ERR(ret);

    /* Write the 2-D variable. */
    for (int i = 0; i < DIM_0_LEN * DIM_1_LEN; i++)
        data_2d[i] = my_comp_idx + i;
    if ((ret = PIOc_put_var_short(ncid, 1, data_2d)))
        ERR(ret);

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
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    int ret; /* Return code. */
    int num_procs[COMPONENT_COUNT] = {1, 1}; /* Num procs for IO and computation. */
    int io_proc_list[NUM_IO_PROCS] = {0};
    int comp_proc_list1[NUM_COMP_PROCS] = {1};
    int comp_proc_list2[NUM_COMP_PROCS] = {2};
    int *proc_list[COMPONENT_COUNT] = {comp_proc_list1, comp_proc_list2};
    MPI_Comm test_comm;

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
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);

        /* Initialize the IO system. The IO task will not return from
         * this call, but instead will go into a loop, listening for
         * messages. */
        if ((ret = PIOc_init_async(test_comm, NUM_IO_PROCS, io_proc_list, COMPONENT_COUNT,
                                   num_procs, (int **)proc_list, NULL, NULL, PIO_REARR_BOX, iosysid)))
            ERR(ERR_INIT);
        for (int c = 0; c < COMPONENT_COUNT; c++)
            printf("my_rank %d cmp %d iosysid[%d] %d\n", my_rank, c, c, iosysid[c]);

        /* All the netCDF calls are only executed on the computation
         * tasks. */
        if (comp_task)
        {
            /* for (int flv = 0; flv < num_flavors; flv++) */
            for (int flv = 0; flv < 1; flv++)
            {
                char filename[NC_MAX_NAME + 1]; /* Test filename. */
                int my_comp_idx = my_rank - 1; /* Index in iosysid array. */

                /* Create sample file. */
                if ((ret = create_test_file(iosysid[my_comp_idx], flavor[flv], my_rank, my_comp_idx, filename)))
                    ERR(ret);

                /* Check the file for correctness. */
                /* if ((ret = check_test_file(iosysid[my_comp_idx], flavor[flv], my_rank, my_comp_idx, filename))) */
                /*     ERR(ret); */
            } /* next netcdf flavor */

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
