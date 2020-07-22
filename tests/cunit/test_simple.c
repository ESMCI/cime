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
#define DIM_NAME_UNLIM "an_unlimited_dim"
#define VAR_NAME "a_var"
#define DIM_LEN 4
#define NDIM1 1
#define NDIM2 2

int main(int argc, char **argv)
{
    int my_rank; 
    int ntasks; 
    int num_iotasks = 1;
    int iosysid, ioid; 
    int gdimlen, maplen;
    PIO_Offset *compmap;
    int ncid, dimid[NDIM2], varid;
    int num_flavors;         /* Number of PIO netCDF flavors in this build. */
    int flavor[NUM_FLAVORS]; /* iotypes for the supported netCDF IO flavors. */
    int i, f;
    int ret; 

    /* Initialize MPI. */
    if ((ret = MPI_Init(&argc, &argv)))
        MPIERR(ret);

    /* Learn my rank and the total number of processors. */
    if ((ret = MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)))
        MPIERR(ret);
    if ((ret = MPI_Comm_size(MPI_COMM_WORLD, &ntasks)))
        MPIERR(ret);

    /* PIOc_set_log_level(4); */
    if (ntasks != 1 && ntasks != 4)
    {
	if (!my_rank)
	    printf("Test must be run on 1 or 4 tasks.\n");
	return ERR_AWFUL;
    }

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

    /* Initialize the decomposition. */
    gdimlen = DIM_LEN;
    maplen = DIM_LEN/ntasks;
    if (!(compmap = malloc(maplen * sizeof(PIO_Offset))))
	ERR(ERR_MEM);
    for (i = 0; i < maplen; i++)
	compmap[i] = i * my_rank;
    if ((ret = PIOc_init_decomp(iosysid, PIO_INT, NDIM1, &gdimlen, maplen, compmap,
				&ioid, PIO_REARR_BOX, NULL, NULL)))
	ERR(ret);
    free(compmap);

    /* Create a file with each available IOType. */
    for (f = 0; f < num_flavors; f++)
    {
	char filename[NC_MAX_NAME + 1];

	/* Create a file. */
	sprintf(filename, "%s_%d.nc", TEST_NAME, flavor[f]);
	if ((ret = PIOc_createfile(iosysid, &ncid, &flavor[f], filename, NC_CLOBBER)))
	    ERR(ret);

	/* Define dims. */
	if ((ret = PIOc_def_dim(ncid, DIM_NAME_UNLIM, PIO_UNLIMITED, &dimid[0])))
	    ERR(ret);
	if ((ret = PIOc_def_dim(ncid, DIM_NAME, DIM_LEN, &dimid[1])))
	    ERR(ret);

	/* Define a var. */
	if ((ret = PIOc_def_var(ncid, VAR_NAME, PIO_INT, NDIM2, dimid, &varid)))
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

    /* Free the decomposition. */
    if ((ret = PIOc_freedecomp(iosysid, ioid)))
	ERR(ret);

    /* Finalize the IOsystem. */
    if ((ret = PIOc_finalize(iosysid)))
	ERR(ret);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
