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

/* The name of the variable created in test file. */
#define VAR_NAME "Jack_London"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of tasks in each computation component. */
#define NUM_COMP_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 2

/* Check a test file for correctness. */
int check_test_file(int iosysid, int iotype, int my_rank, int my_comp_idx,
                    const char *filename)
{
    int ncid;
    int nvars;
    int ndims;
    int ngatts;
    int unlimdimid;
    char var_name[PIO_MAX_NAME + 1];
    int xtype;
    int natts;
    int ret;

    /* Open the test file. */
    if ((ret = PIOc_openfile2(iosysid, &ncid, &iotype, filename, PIO_NOWRITE)))
        ERR(ret);

    /* Check file metadata. */
    if ((ret = PIOc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid)))
        ERR(ret);
    if (ndims != 0 || nvars != 1 || ngatts != 0 || unlimdimid != -1)
        ERR(ERR_WRONG);

    /* Check the variable. */
    if ((ret = PIOc_inq_var(ncid, 0, var_name, &xtype, &ndims, NULL, &natts)))
        ERR(ret);
    if (strcmp(var_name, VAR_NAME) || xtype != PIO_INT || ndims != 0 || natts != 0)
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
    int ret;

    /* Learn name of IOTYPE. */
    if ((ret = get_iotype_name(iotype, iotype_name)))
        return ret;
    
    /* Create a filename. */
    sprintf(filename, "%s_%s_cmp_%d.nc", TEST_NAME, iotype_name, my_comp_idx);
    printf("my_rank %d creating test file %s for iosysid %d\n", my_rank, filename, iosysid);

    /* Create the file. */
    if ((ret = PIOc_createfile(iosysid, &ncid, &iotype, filename, NC_CLOBBER)))
        return ret;

    /* Define a variable. */
    int varid;
    if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_INT, 0, NULL, &varid)))
        return ret;

    /* End define mode. */
    if ((ret = PIOc_enddef(ncid)))
        return ret;

    /* Close the file if ncidp was not provided. */
    if ((ret = PIOc_closefile(ncid)))
        return ret;

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
                if ((ret = check_test_file(iosysid[my_comp_idx], flavor[flv], my_rank, my_comp_idx, filename)))
                    ERR(ret);
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
