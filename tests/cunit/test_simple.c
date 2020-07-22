/*
 * This very simple test for PIO runs on 4 ranks.
 *
 * @author Ed Hartnett
 */
#include <config.h>
#include <pio.h>
#include <pio_tests.h>

/* The name of this test. */
#define TEST_NAME "test_simple"
#define DIM_NAME "a_dim"
#define VAR_NAME "a_var"
#define DIM_LEN 4
#define NDIM1 1

int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int num_iotasks = 1;
    int iosysid; /* The ID for the parallel I/O system. */
    int ncid, dimid, varid;
    int num_flavors; /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    int f;
    int ret; /* Return code. */

    /* Initialize MPI. */
    if ((ret = MPI_Init(&argc, &argv)))
        MPIERR(ret);

    /* Learn my rank and the total number of processors. */
    if ((ret = MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)))
        MPIERR(ret);
    if ((ret = MPI_Comm_size(MPI_COMM_WORLD, &ntasks)))
        MPIERR(ret);

    /* PIOc_set_log_level(4); */

    /* Change error handling so we can test inval parameters. */
    if ((ret = PIOc_set_iosystem_error_handling(PIO_DEFAULT, PIO_RETURN_ERROR, NULL)))
        ERR(ret);

    /* Initialize the IOsystem. */
    if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, num_iotasks, 1, 0, PIO_REARR_BOX,
				   &iosysid)))
	ERR(ret);

    /* Find out which IOtypes are available in this build by calling
     * this function from test_common.c. */
    if ((ret = get_iotypes(&num_flavors, flavor)))
	ERR(ret);

    /* Create a file with each available IOType. */
    for (f = 0; f < num_flavors; f++)
    {
	char filename[NC_MAX_NAME + 1];

	/* Create a file. */
	sprintf(filename, "%s_%d.nc", TEST_NAME, flavor[f]);
	if ((ret = PIOc_createfile(iosysid, &ncid, &flavor[f], filename, NC_CLOBBER)))
	    ERR(ret);

	/* Define a dim. */
	if ((ret = PIOc_def_dim(ncid, DIM_NAME, DIM_LEN, &dimid)))
	    ERR(ret);

	/* Define a var. */
	if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_INT, NDIM1, &dimid, &varid)))
	    ERR(ret);

	if ((ret = PIOc_enddef(ncid)))
	    ERR(ret);
	
	/* Close the file. */
	if ((ret = PIOc_closefile(ncid)))
	    ERR(ret);

	/* Check the file. */
	{
	    /* Reopen the file. */
	    if ((ret = PIOc_openfile(iosysid, &ncid, &flavor[f], filename, NC_NOWRITE)))
		ERR(ret);
	    
	    /* Close the file. */
	    if ((ret = PIOc_closefile(ncid)))
		ERR(ret);
	}
    } /* next IOType */

    /* Finalize the IOsystem. */
    if ((ret = PIOc_finalize(iosysid)))
	ERR(ret);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
