/**
 * @file Tests the PIO library with multiple iosysids in use at the
 * same time.
 *
 * This is a simplified, C version of the fortran
 * pio_iosystem_tests3.F90.
 *
 * @author Ed Hartnett
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_iosystem3"

/* Used to define netcdf test file. */
#define PIO_TF_MAX_STR_LEN 100
#define ATTNAME "filename"
#define DIMNAME "filename_dim"

/* Used when initializing PIO. */
#define STRIDE1 1
#define STRIDE2 2
#define BASE0 0
#define BASE1 1
#define NUM_IO1 1
#define NUM_IO2 2
#define NUM_IO4 4
#define REARRANGER 1

/** This creates a netCDF file in the specified format, with some
 * sample values. */
int
create_file(MPI_Comm comm, int iosysid, int format, char *filename,
	    char *attname, char *dimname, int my_rank)
{
    int ncid, varid, dimid;
    int ret;

    /* Create the file. */
    if ((ret = PIOc_createfile(iosysid, &ncid, &format, filename, NC_CLOBBER)))
	return ret;
    printf("%d file created ncid = %d\n", my_rank, ncid);

    /* Define a dimension. */
    printf("%d defining dimension %s\n", my_rank, dimname);
    if ((ret = PIOc_def_dim(ncid, dimname, PIO_TF_MAX_STR_LEN, &dimid)))
	return ret;

    /* Define a 1-D variable. */
    printf("%d defining variable %s\n", my_rank, attname);
    if ((ret = PIOc_def_var(ncid, attname, NC_CHAR, 1, &dimid, &varid)))
    	return ret;

    /* Write an attribute. */
    if ((ret = PIOc_put_att_text(ncid, varid, attname, strlen(filename), filename)))
    	return ret;

    /* End define mode. */
    printf("%d ending define mode ncid = %d\n", my_rank, ncid);
    if ((ret = PIOc_enddef(ncid)))
	return ret;
    printf("%d define mode ended ncid = %d\n", my_rank, ncid);

    /* Close the file. */
    printf("%d closing file ncid = %d\n", my_rank, ncid);
    if ((ret = PIOc_closefile(ncid)))
	return ret;
    printf("%d closed file ncid = %d\n", my_rank, ncid);
    
    return PIO_NOERR;
}

/** This checks an already-open netCDF file. */
int
check_file(MPI_Comm comm, int iosysid, int format, int ncid, char *filename,
	   char *attname, char *dimname, int my_rank)
{
    int dimid;
    int ret;

    /* Check the file. */
    if ((ret = PIOc_inq_dimid(ncid, dimname, &dimid)))
	return ret;
    printf("%d dimid = %d\n", my_rank, dimid);

    return PIO_NOERR;
}

/** This opens and checks a netCDF file. */
int open_and_check_file(MPI_Comm comm, int iosysid, int iotype, int *ncid, char *fname,
		    char *attname, char *dimname, int disable_close, int my_rank)
{
    int mode = PIO_WRITE;
    int ret;

    /* Open the file. */
    if ((ret = PIOc_openfile(iosysid, ncid, &iotype, fname, mode)))
	return ret;

    /* Check the file. */
    if ((ret = check_file(comm, iosysid, iotype, *ncid, fname, attname, dimname, my_rank)))
    	return ret;

    /* Close the file, maybe. */
    if (!disable_close)
	if ((ret = PIOc_closefile(*ncid)))
	    return ret;
	
    return PIO_NOERR;
}

/** Run async tests. */
int
main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid; /* The ID for the parallel I/O system. */
    int iosysid_world; /* The ID for the parallel I/O system. */
    MPI_Group world_group; /* An MPI group of world. */
    int ret; /* Return code. */

    int iotypes[NUM_FLAVORS] = {PIO_IOTYPE_PNETCDF, PIO_IOTYPE_NETCDF,
				PIO_IOTYPE_NETCDF4C, PIO_IOTYPE_NETCDF4P};

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS)))
	ERR(ERR_INIT);

    /* Initialize PIO system on world. */
    if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, NUM_IO4, STRIDE1, BASE0, REARRANGER, &iosysid_world)))
    	ERR(ret);

    /* Get MPI_Group of world comm. */
    if ((ret = MPI_Comm_group(MPI_COMM_WORLD, &world_group)))
	ERR(ret);

/*    for (int i = 0; i < NUM_FLAVORS; i++)*/
    for (int i = 2; i < 4; i++)
    {
    	char fname0[] = "pio_iosys_test_file0.nc";
    	printf("\n\n%d i = %d\n", my_rank, i);

    	if ((ret = create_file(MPI_COMM_WORLD, iosysid_world, iotypes[i], fname0, ATTNAME,
    			       DIMNAME, my_rank)))
    	    ERR(ret);

    	MPI_Barrier(MPI_COMM_WORLD);

    	/* Now check the first file from WORLD communicator. */
    	int ncid;
    	if ((ret = open_and_check_file(MPI_COMM_WORLD, iosysid_world, iotypes[i], &ncid, fname0,
    				       ATTNAME, DIMNAME, 1, my_rank)))
    	    ERR(ret);

    } /* next iotype */

    /* Finalize PIO systems. */
    printf("%d pio finalizing\n", my_rank);
    if ((ret = PIOc_finalize(iosysid_world)))
    	ERR(ret);

    if ((ret = MPI_Group_free(&world_group)))
	ERR(ret);

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
	ERR(ERR_AWFUL);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
