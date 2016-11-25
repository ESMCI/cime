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
#define MIN_NTASKS 1

/* The name of this test. */
#define TEST_NAME "test_nc4"

/* The number of dimensions in the example data. In this test, we
 * are using three-dimensional data. */
#define NDIM 3

/* The length of our sample data along each dimension. */
#define X_DIM_LEN 400
#define Y_DIM_LEN 400

/* The number of timesteps of data to write. */
#define NUM_TIMESTEPS 6

/* The name of the variable in the netCDF output file. */
#define VAR_NAME "foo"

/* The meaning of life, the universe, and everything. */
#define START_DATA_VAL 42

/* Values for some netcdf-4 settings. */
#define VAR_CACHE_SIZE (1024 * 1024)
#define VAR_CACHE_NELEMS 10
#define VAR_CACHE_PREEMPTION 0.5

/* The dimension names. */
char dim_name[NDIM][NC_MAX_NAME + 1] = {"timestep", "x", "y"};

/* Length of the dimensions in the sample data. */
int dim_len[NDIM] = {NC_UNLIMITED, X_DIM_LEN, Y_DIM_LEN};

/* Length of chunksizes to use in netCDF-4 files. */
PIO_Offset chunksize[NDIM] = {2, X_DIM_LEN/2, Y_DIM_LEN/2};

/* Run Tests for NetCDF-4 Functions. */
int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iotype; /* Specifies the flavor of netCDF output format. */
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    int niotasks;    /* Number of processors that will do IO. */
    int ioproc_stride = 1;    /* Stride in the mpi rank between io tasks. */
    int numAggregator = 0;    /* Number of the aggregator? Always 0 in this test. */
    int ioproc_start = 0;    /* Zero based rank of first processor to be used for I/O. */
    int dimids[NDIM];    /* The dimension IDs. */
    PIO_Offset elements_per_pe;    /* Array index per processing unit. */
    int iosysid;    /* The ID for the parallel I/O system. */
    int ncid;    /* The ncid of the netCDF file. */
    int varid;    /* The ID of the netCDF varable. */
    int storage;    /* Storage of netCDF-4 files (contiguous vs. chunked). */
    PIO_Offset my_chunksize[NDIM];    /* Chunksizes set in the file. */
    int shuffle;    /* The shuffle filter setting in the netCDF-4 test file. */
    int deflate;    /* Non-zero if deflate set for the variable in the netCDF-4 test file. */
    int deflate_level;    /* The deflate level set for the variable in the netCDF-4 test file. */
    int endianness;    /* Endianness of variable. */
    PIO_Offset var_cache_size;    /* Size of the var chunk cache. */
    PIO_Offset var_cache_nelems; /* Number of elements in var cache. */
    float var_cache_preemption;     /* Var cache preemption. */
    int ioid; /* The I/O description ID. */
    PIO_Offset *compdof; /* The decomposition mapping. */
    int ret;    /* Return code. */

    /* Index for loops. */
    int fmt, d, d1, i;

    /* For setting the chunk cache. */
    PIO_Offset chunk_cache_size = 1024*1024;
    PIO_Offset chunk_cache_nelems = 1024;
    float chunk_cache_preemption = 0.5;

    /* For reading the chunk cache. */
    PIO_Offset chunk_cache_size_in;
    PIO_Offset chunk_cache_nelems_in;
    float chunk_cache_preemption_in;

    char varname[15];

    MPI_Comm test_comm; /* A communicator for this test. */

    /* Initialize test. */
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS,
                              TARGET_NTASKS, &test_comm)))
        ERR(ERR_INIT);

    /* Only do something on TARGET_NTASKS tasks. */
    if (my_rank < TARGET_NTASKS)
    {
        /* Figure out iotypes. */
        if ((ret = get_iotypes(&num_flavors, flavor)))
            ERR(ret);

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
        for (i = 0; i < elements_per_pe; i++)
            compdof[i] = my_rank * elements_per_pe + i + 1;

        /* Create the PIO decomposition for this test. */
        printf("rank: %d Creating decomposition...\n", my_rank);
        if ((ret = PIOc_InitDecomp(iosysid, PIO_FLOAT, 2, &dim_len[1], (PIO_Offset)elements_per_pe,
                                   compdof, &ioid, NULL, NULL, NULL)))
            ERR(ret);
        free(compdof);

#ifdef HAVE_MPE
        /* Log with MPE that we are done with INIT. */
        if ((ret = MPE_Log_event(event_num[END][INIT], 0, "end init")))
            MPIERR(ret);
#endif /* HAVE_MPE */

        /* Use PIO to create the example file in each of the four
         * available ways. */
        for (fmt = 0; fmt < num_flavors; fmt++)
        {
            char filename[NC_MAX_NAME + 1]; /* Test filename. */
            char iotype_name[NC_MAX_NAME + 1];

#ifdef HAVE_MPE
            /* Log with MPE that we are starting CREATE. */
            if ((ret = MPE_Log_event(event_num[START][CREATE_PNETCDF+fmt], 0, "start create")))
                MPIERR(ret);
#endif /* HAVE_MPE */

            /* Create a filename. */
            if ((ret = get_iotype_name(flavor[fmt], iotype_name)))
                return ret;
            sprintf(filename, "%s_%s.nc", TEST_NAME, iotype_name);

            printf("rank: %d Setting chunk cache for file %s with format %d...\n",
                   my_rank, filename, flavor[fmt]);

            /* Try to set the chunk cache with invalid preemption to check error handling. */
            chunk_cache_preemption = 50.0;
            ret = PIOc_set_chunk_cache(iosysid, flavor[fmt], chunk_cache_size,
                                       chunk_cache_nelems, chunk_cache_preemption);
            if (flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
            {
                if (ret != NC_EINVAL)
                    ERR(ERR_AWFUL);
            }
            else
            {
                if (ret != NC_ENOTNC4)
                    ERR(ERR_AWFUL);
            }

            /* Try to set the chunk cache. */
            chunk_cache_preemption = 0.5;
            ret = PIOc_set_chunk_cache(iosysid, flavor[fmt], chunk_cache_size,
                                       chunk_cache_nelems, chunk_cache_preemption);

            /* Should only have worked for netCDF-4 iotypes. */
            if (flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
            {
                if (ret != PIO_NOERR)
                    ERR(ret);
            }
            else
            {
                if (ret != PIO_ENOTNC4)
                    ERR(ERR_AWFUL);
            }

            /* Now check the chunk cache. */
            ret = PIOc_get_chunk_cache(iosysid, flavor[fmt], &chunk_cache_size_in,
                                       &chunk_cache_nelems_in, &chunk_cache_preemption_in);

            /* Should only have worked for netCDF-4 iotypes. */
            if (flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
            {
                /* Check that there was no error. */
                if (ret != PIO_NOERR)
                    ERR(ret);

                /* Check that we got the correct values. */
                if (chunk_cache_size_in != chunk_cache_size || chunk_cache_nelems_in != chunk_cache_nelems ||
                    chunk_cache_preemption_in != chunk_cache_preemption)
                    ERR(ERR_AWFUL);
            }
            else
            {
                if (ret != PIO_ENOTNC4)
                    ERR(ERR_AWFUL);
            }

            /* Create the netCDF output file. */
            printf("rank: %d Creating sample file %s with format %d...\n",
                   my_rank, filename, flavor[fmt]);
            if ((ret = PIOc_createfile(iosysid, &ncid, &(flavor[fmt]), filename,
                                       PIO_CLOBBER)))
                ERR(ret);

            /* Set error handling. */
            PIOc_Set_File_Error_Handling(ncid, PIO_BCAST_ERROR);

            /* Define netCDF dimensions and variable. */
            printf("rank: %d Defining netCDF metadata...\n", my_rank);
            for (d = 0; d < NDIM; d++) {
                printf("rank: %d Defining netCDF dimension %s, length %d\n", my_rank,
                       dim_name[d], dim_len[d]);
                if ((ret = PIOc_def_dim(ncid, dim_name[d], (PIO_Offset)dim_len[d], &dimids[d])))
                    ERR(ret);
            }
            printf("rank: %d Defining netCDF variable %s, ndims %d\n", my_rank, VAR_NAME, NDIM);
            if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_FLOAT, NDIM, dimids, &varid)))
                ERR(ret);

            /* For netCDF-4 files, set the chunksize to improve performance. */
            if (flavor[fmt] == PIO_IOTYPE_NETCDF4C || flavor[fmt] == PIO_IOTYPE_NETCDF4P)
            {
                printf("rank: %d Defining chunksizes\n", my_rank);
                if ((ret = PIOc_def_var_chunking(ncid, 0, NC_CHUNKED, chunksize)))
                    ERR(ret);

                /* Check that the inq_varname function works. */
                printf("rank: %d Checking varname\n", my_rank);
                ret = PIOc_inq_varname(ncid, 0, varname);
                printf("rank: %d ret: %d varname: %s\n", my_rank, ret, varname);

                /* Check that the inq_var_chunking function works. */
                printf("rank: %d Checking chunksizes\n", my_rank);
                ret = PIOc_inq_var_chunking(ncid, 0, &storage, my_chunksize);

                if ((ret = PIOc_inq_var_chunking(ncid, 0, &storage, my_chunksize)))
                    ERR(ret);
                {
                    printf("rank: %d ret: %d storage: %d\n", my_rank, ret, storage);
                    for (d1 = 0; d1 < NDIM; d1++)
                    {
                        printf("chunksize[%d]=%d\n", d1, my_chunksize[d1]);
                    }
                }

                /* Check the answers. */
                if (flavor[fmt] == PIO_IOTYPE_NETCDF4C ||
                    flavor[fmt] == PIO_IOTYPE_NETCDF4P)
                {
                    if (storage != NC_CHUNKED)
                        ERR(ERR_AWFUL);
                    for (d1 = 0; d1 < NDIM; d1++)
                        if (my_chunksize[d1] != chunksize[d1])
                            ERR(ERR_AWFUL);
                }

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
                printf("rank: %d PIOc_set_var_chunk_cache...\n", my_rank);
                if ((ret = PIOc_set_var_chunk_cache(ncid, 0, VAR_CACHE_SIZE, VAR_CACHE_NELEMS,
                                                    VAR_CACHE_PREEMPTION)))
                    ERR(ret);

                /* Check getting the chunk cache values for the variable. */
                printf("rank: %d PIOc_get_var_chunk_cache...\n", my_rank);
                if ((ret = PIOc_get_var_chunk_cache(ncid, 0, &var_cache_size, &var_cache_nelems,
                                                    &var_cache_preemption)))
                    ERR(ret);
                PIO_Offset len;
                if ((ret = PIOc_inq_dimlen(ncid, 0, &len)))
                    ERR(ret);

                /* Check that we got expected values. */
                printf("rank: %d var_cache_size = %d\n", my_rank, var_cache_size);
                if (var_cache_size != VAR_CACHE_SIZE)
                    ERR(ERR_AWFUL);
                if (var_cache_nelems != VAR_CACHE_NELEMS)
                    ERR(ERR_AWFUL);
                if (var_cache_preemption != VAR_CACHE_PREEMPTION)
                    ERR(ERR_AWFUL);
            } else {
                /* Trying to set or inq netCDF-4 settings for non-netCDF-4
                 * files results in the PIO_ENOTNC4 error. */
                if ((ret = PIOc_def_var_chunking(ncid, 0, NC_CHUNKED, chunksize)) != PIO_ENOTNC4)
                    ERR(ERR_AWFUL);
                /* if ((ret = PIOc_inq_var_chunking(ncid, 0, &storage, my_chunksize)) != PIO_ENOTNC4) */
                /*     ERR(ERR_AWFUL); */
                if ((ret = PIOc_inq_var_deflate(ncid, 0, &shuffle, &deflate, &deflate_level))
                    != PIO_ENOTNC4)
                    ERR(ret);
                if ((ret = PIOc_def_var_endian(ncid, 0, 1)) != PIO_ENOTNC4)
                    ERR(ERR_AWFUL);
                if ((ret = PIOc_inq_var_endian(ncid, 0, &endianness)) != PIO_ENOTNC4)
                    ERR(ERR_AWFUL);
                if ((ret = PIOc_set_var_chunk_cache(ncid, 0, VAR_CACHE_SIZE, VAR_CACHE_NELEMS,
                                                    VAR_CACHE_PREEMPTION)) != PIO_ENOTNC4)
                    ERR(ret);
                if ((ret = PIOc_get_var_chunk_cache(ncid, 0, &var_cache_size, &var_cache_nelems,
                                                    &var_cache_preemption)) != PIO_ENOTNC4)
                    ERR(ret);
                if ((ret = PIOc_set_chunk_cache(iosysid, flavor[fmt], chunk_cache_size, chunk_cache_nelems,
                                                chunk_cache_preemption)) != PIO_ENOTNC4)
                    ERR(ret);
                if ((ret = PIOc_get_chunk_cache(iosysid, flavor[fmt], &chunk_cache_size,
                                                &chunk_cache_nelems, &chunk_cache_preemption)) != PIO_ENOTNC4)
                    ERR(ret);
            }

            if ((ret = PIOc_enddef(ncid)))
                ERR(ret);

            /* Close the netCDF file. */
            printf("rank: %d Closing the sample data file...\n", my_rank);
            if ((ret = PIOc_closefile(ncid)))
                ERR(ret);
        }

        /* Free the PIO decomposition. */
        printf("rank: %d Freeing PIO decomposition...\n", my_rank);
        if ((ret = PIOc_freedecomp(iosysid, ioid)))
            ERR(ret);
    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
