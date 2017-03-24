/*
 * @file
 * @brief A simple C example for the ParallelIO Library.
 *
 * This example creates a netCDF output file with three dimensions
 * (one unlimited) and one variable. It first writes, then reads the
 * sample file using distributed arrays.
 *
 * This example can be run in parallel for 4 processors.
 */

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <mpi.h>
#include <pio.h>
#ifdef TIMING
#include <gptl.h>
#endif

/* The number of possible output netCDF output flavors available to
 * the ParallelIO library. */
#define NUM_NETCDF_FLAVORS 4

/* The number of dimensions in the example data. */
#define NDIM3 3

/* The length of our sample data in X dimension.*/
#define DIM_LEN_X 16

/* The length of our sample data in Y dimension.*/
#define DIM_LEN_Y 16

/* The name of the dimension in the netCDF output file. */
#define DIM_NAME "x"

/* The name of the variable in the netCDF output file. */
#define VAR_NAME "foo"

/* Return code when netCDF output file does not match
 * expectations. */
#define ERR_BAD 1001

/* The meaning of life, the universe, and everything. */
#define START_DATA_VAL 42

/* Number of tasks this example runs on. */
#define TARGET_NTASKS 4

/* Logging level. */
#define LOG_LEVEL 3

/* Handle MPI errors. This should only be used with MPI library
 * function calls. */
#define MPIERR(e) do {                                                  \
	MPI_Error_string(e, err_buffer, &resultlen);			\
	printf("MPI error, line %d, file %s: %s\n", __LINE__, __FILE__, err_buffer); \
	MPI_Finalize();							\
	return 2;							\
    } while (0)

/* Handle non-MPI errors by finalizing the MPI library and exiting
 * with an exit code. */
#define ERR(e) do {				\
	MPI_Finalize();				\
	return e;				\
    } while (0)

/* Global err buffer for MPI. When there is an MPI error, this buffer
 * is used to store the error message that is associated with the MPI
 * error. */
char err_buffer[MPI_MAX_ERROR_STRING];

/* This is the length of the most recent MPI error message, stored
 * int the global error string. */
int resultlen;

/* @brief Check the output file.
 *
 *  Use netCDF to check that the output is as expected.
 *
 * @param ntasks The number of processors running the example.
 * @param filename The name of the example file to check.
 *
 * @return 0 if example file is correct, non-zero otherwise. */
/* int check_file(int ntasks, char *filename) { */

/*     int ncid;         /\* File ID from netCDF. *\/ */
/*     int ndims;        /\* Number of dimensions. *\/ */
/*     int nvars;        /\* Number of variables. *\/ */
/*     int ngatts;       /\* Number of global attributes. *\/ */
/*     int unlimdimid;   /\* ID of unlimited dimension. *\/ */
/*     size_t dimlen;    /\* Length of the dimension. *\/ */
/*     int natts;        /\* Number of variable attributes. *\/ */
/*     nc_type xtype;    /\* NetCDF data type of this variable. *\/ */
/*     int ret;          /\* Return code for function calls. *\/ */
/*     int dimids[NDIM3]; /\* Dimension ids for this variable. *\/ */
/*     char dim_name[NC_MAX_NAME];   /\* Name of the dimension. *\/ */
/*     char var_name[NC_MAX_NAME];   /\* Name of the variable. *\/ */
/*     /\* size_t start[NDIM3];           /\\* Zero-based index to start read. *\\/ *\/ */
/*     /\* size_t count[NDIM3];           /\\* Number of elements to read. *\\/ *\/ */
/*     /\* int buffer[DIM_LEN_X];          /\\* Buffer to read in data. *\\/ *\/ */
/*     /\* int expected[DIM_LEN_X];        /\\* Data values we expect to find. *\\/ *\/ */

/*     /\* Open the file. *\/ */
/*     if ((ret = nc_open(filename, 0, &ncid))) */
/* 	return ret; */

/*     /\* Check the metadata. *\/ */
/*     if ((ret = nc_inq(ncid, &ndims, &nvars, &ngatts, &unlimdimid))) */
/* 	return ret; */
/*     /\* if (ndims != NDIM3 || nvars != 1 || ngatts != 0 || unlimdimid != -1) *\/ */
/*     /\*     return ERR_BAD; *\/ */
/*     /\* if ((ret = nc_inq_dim(ncid, 0, dim_name, &dimlen))) *\/ */
/*     /\*     return ret; *\/ */
/*     /\* if (dimlen != DIM_LEN || strcmp(dim_name, DIM_NAME)) *\/ */
/*     /\*     return ERR_BAD; *\/ */
/*     /\* if ((ret = nc_inq_var(ncid, 0, var_name, &xtype, &ndims, dimids, &natts))) *\/ */
/*     /\*     return ret; *\/ */
/*     /\* if (xtype != NC_INT || ndims != NDIM || dimids[0] != 0 || natts != 0) *\/ */
/*     /\*     return ERR_BAD; *\/ */

/*     /\* Use the number of processors to figure out what the data in the */
/*      * file should look like. *\/ */
/*     /\* int div = DIM_LEN/ntasks; *\/ */
/*     /\* for (int d = 0; d < DIM_LEN; d++) *\/ */
/*     /\*     expected[d] = START_DATA_VAL + d/div; *\/ */

/*     /\* /\\* Check the data. *\\/ *\/ */
/*     /\* start[0] = 0; *\/ */
/*     /\* count[0] = DIM_LEN; *\/ */
/*     /\* if ((ret = nc_get_vara(ncid, 0, start, count, buffer))) *\/ */
/*     /\*     return ret; *\/ */
/*     /\* for (int d = 0; d < DIM_LEN; d++) *\/ */
/*     /\*     if (buffer[d] != expected[d]) *\/ */
/*     /\*         return ERR_BAD; *\/ */

/*     /\* Close the file. *\/ */
/*     if ((ret = nc_close(ncid))) */
/* 	return ret; */

/*     /\* Everything looks good! *\/ */
/*     return 0; */
/* } */

/* Write, then read, a simple example with darrays.

    The example can be run from the command line (on system that
    support it) like this:

    <pre>
    mpiexec -n 4 ./darray_no_async
    </pre>

    The sample file created by this program is a small netCDF file. It
    has the following contents (as shown by ncdump):

    <pre>

    </pre>

*/
    int main(int argc, char* argv[])
    {
	int my_rank;  /* Zero-based rank of processor. */
	int ntasks;   /* Number of processors involved in current execution. */
	int niotasks; /* Number of processors that will do IO. */
	int ioproc_stride = 1;	    /* Stride in the mpi rank between io tasks. */
	int ioproc_start = 0; 	    /* Rank of first task to be used for I/O. */
        PIO_Offset elements_per_pe; /* Array elements per processing unit. */
	int iosysid;  /* The ID for the parallel I/O system. */	
	int ncid;     /* The ncid of the netCDF file. */
	int dimid[NDIM3];    /* The dimension ID. */
	int varid;    /* The ID of the netCDF varable. */
	int ioid;     /* The I/O description ID. */
	/* int *buffer;  /\* A buffer for sample data. *\/ */
	PIO_Offset *compdof;            /* Array of decomposition mapping. */
        char filename[NC_MAX_NAME + 1]; /* Test filename. */
        int num_flavors = 0;            /* Number of iotypes available in this build. */
	int format[NUM_NETCDF_FLAVORS]; /* Different output flavors. */
	int dim_len[NDIM3] = {NC_UNLIMITED, DIM_LEN_X, DIM_LEN_Y};
	char dim_name[NDIM3][PIO_MAX_NAME + 1] = {"unlimted", "x", "y"};
	int ret;                        /* Return value. */

#ifdef TIMING
	/* Initialize the GPTL timing library. */
	if ((ret = GPTLinitialize ()))
	    return ret;
#endif

	/* Initialize MPI. */
	if ((ret = MPI_Init(&argc, &argv)))
	    MPIERR(ret);
	if ((ret = MPI_Comm_set_errhandler(MPI_COMM_WORLD, MPI_ERRORS_RETURN)))
	    MPIERR(ret);

	/* Learn my rank and the total number of processors. */
	if ((ret = MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)))
	    MPIERR(ret);
	if ((ret = MPI_Comm_size(MPI_COMM_WORLD, &ntasks)))
	    MPIERR(ret);

	/* Check that a valid number of processors was specified. */
	if (ntasks != 4)
	    fprintf(stderr, "Number of processors must be 4!\n");
        printf("%d: ParallelIO Library darray_no_async example running on %d processors.\n",
               my_rank, ntasks);

        /* Turn on logging. */
        if ((ret = PIOc_set_log_level(LOG_LEVEL)))
            return ret;
        
	/* keep things simple - 1 iotask per MPI process */
	niotasks = ntasks;

	/* Initialize the PIO IO system. This specifies how
	 * many and which processors are involved in I/O. */
	if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, niotasks, ioproc_stride,
				       ioproc_start, PIO_REARR_SUBSET, &iosysid)))
	    ERR(ret);

	/* Describe the decomposition. This is a 1-based array, so add 1! */
	elements_per_pe = DIM_LEN_X * DIM_LEN_Y / ntasks;
	if (!(compdof = malloc(elements_per_pe * sizeof(PIO_Offset))))
	    return PIO_ENOMEM;
	for (int i = 0; i < elements_per_pe; i++)
	    compdof[i] = my_rank * elements_per_pe + i + 1;

	/* Create the PIO decomposition for this example. */
        printf("rank: %d Creating decomposition...\n", my_rank);
	if ((ret = PIOc_InitDecomp(iosysid, PIO_INT, NDIM3 - 1, &dim_len[1], (PIO_Offset)elements_per_pe,
				   compdof, &ioid, NULL, NULL, NULL)))
	    ERR(ret);
	free(compdof);

        /* The number of favors may change with the build parameters. */
#ifdef _PNETCDF
        format[num_flavors++] = PIO_IOTYPE_PNETCDF;
#endif
        format[num_flavors++] = PIO_IOTYPE_NETCDF;
#ifdef _NETCDF4
        format[num_flavors++] = PIO_IOTYPE_NETCDF4C;
        format[num_flavors++] = PIO_IOTYPE_NETCDF4P;
#endif

	/* Use PIO to create the example file in each of the four
	 * available ways. */
	for (int fmt = 0; fmt < num_flavors; fmt++)
	{
            /* Create a filename. */
            sprintf(filename, "darray_no_async_iotype_%d.nc", fmt);

	    /* Create the netCDF output file. */
            printf("rank: %d Creating sample file %s with format %d...\n",
                   my_rank, filename, format[fmt]);
	    if ((ret = PIOc_createfile(iosysid, &ncid, &(format[fmt]), filename, PIO_CLOBBER)))
		ERR(ret);

	    /* Define netCDF dimension and variable. */
            /* printf("rank: %d Defining netCDF metadata...\n", my_rank); */
            /* for (int d = 0; d < NDIM3; d++) */
            /*     if ((ret = PIOc_def_dim(ncid, dim_name[d], dim_len[d], &dimid[d]))) */
            /*         ERR(ret); */
	    /* if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_INT, NDIM3, dimid, &varid))) */
	    /*     ERR(ret); */
	    if ((ret = PIOc_enddef(ncid)))
	        ERR(ret);

	    /* /\* Prepare sample data. *\/ */
	    /* if (!(buffer = malloc(elements_per_pe * sizeof(int)))) */
	    /*     return PIO_ENOMEM; */
	    /* for (int i = 0; i < elements_per_pe; i++) */
	    /*     buffer[i] = START_DATA_VAL + my_rank; */

	    /* /\* Write data to the file. *\/ */
            /* printf("rank: %d Writing sample data...\n", my_rank); */
	    /* if ((ret = PIOc_write_darray(ncid, varid, ioid, (PIO_Offset)elements_per_pe, */
	    /* 			     buffer, NULL))) */
	    /*     ERR(ret); */
	    /* if ((ret = PIOc_sync(ncid))) */
	    /*     ERR(ret); */

	    /* /\* Free buffer space used in this example. *\/ */
	    /* free(buffer); */

	    /* Close the netCDF file. */
            printf("rank: %d Closing the sample data file...\n", my_rank);
	    if ((ret = PIOc_closefile(ncid)))
		ERR(ret);
	}

	/* Free the PIO decomposition. */
        printf("rank: %d Freeing PIO decomposition...\n", my_rank);
	if ((ret = PIOc_freedecomp(iosysid, ioid)))
	    ERR(ret);

	/* Finalize the IO system. */
        printf("rank: %d Freeing PIO resources...\n", my_rank);
	if ((ret = PIOc_finalize(iosysid)))
	    ERR(ret);

	/* Check the output file. */
	/* if (!my_rank) */
	/*     for (int fmt = 0; fmt < num_flavors; fmt++) */
        /*     { */
        /*         sprintf(filename, "example1_%d.nc", fmt); */
	/* 	if ((ret = check_file(ntasks, filename))) */
	/* 	    ERR(ret); */
        /*     } */

	/* Finalize the MPI library. */
	MPI_Finalize();

#ifdef TIMING
	/* Finalize the GPTL timing library. */
	if ((ret = GPTLfinalize ()))
	    return ret;
#endif

        printf("rank: %d SUCCESS!\n", my_rank);
	return 0;
    }
