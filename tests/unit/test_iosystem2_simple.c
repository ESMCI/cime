/**
 * @file Tests the PIO library with multiple iosysids in use at the
 * same time.
 *
 * This is a simplified, C version of the fortran pio_iosystem_tests2.F90.
 *
 * @author Ed Hartnett
 */
#include <pio.h>
#include <pio_tests.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 2

/* The name of this test. */
#define TEST_NAME "test_iosystem2_simple"

/* Used to define netcdf test file. */
#define PIO_TF_MAX_STR_LEN 100
#define ATTNAME "filename"
#define DIMNAME "filename_dim"

/* Number of test files generated. */
#define NUM_FILES 3

/* Needed to init intracomm. */
#define STRIDE 1
#define BASE 0
#define REARRANGER 1

/** This creates a netCDF file in the specified format, with some
 * sample values. */
int
create_file(int iosysid, int format, char *filename, int my_rank)
{
    int ncid, varid, dimid;
    int ret;

    /* Create the file. */
    if ((ret = PIOc_createfile(iosysid, &ncid, &format, filename, NC_CLOBBER)))
	return ret;
    printf("%d file created ncid = %d\n", my_rank, ncid);

    /* Define a dimension. */
    printf("%d defining dimension %s\n", my_rank, DIMNAME);
    if ((ret = PIOc_def_dim(ncid, DIMNAME, PIO_TF_MAX_STR_LEN, &dimid)))
	return ret;

    /* Define a 1-D variable. */
    printf("%d defining variable %s\n", my_rank, ATTNAME);
    if ((ret = PIOc_def_var(ncid, ATTNAME, NC_CHAR, 1, &dimid, &varid)))
    	return ret;

    /* Write an attribute. */
    if ((ret = PIOc_put_att_text(ncid, varid, ATTNAME, strlen(filename), filename)))
    	return ret;

    /* End define mode. */
    if ((ret = PIOc_enddef(ncid)))
	return ret;
    printf("%d define mode ended ncid = %d\n", my_rank, ncid);

    /* Close the file. */
    if ((ret = PIOc_closefile(ncid)))
	return ret;
    printf("%d closed file ncid = %d\n", my_rank, ncid);

    return PIO_NOERR;
}

/** Run test. */
int
main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks; /* Number of processors involved in current execution. */
    int iosysid; /* The ID for the parallel I/O system. */
    int iosysid_world; /* The ID for the parallel I/O system. */
    int ret; /* Return code. */

    int iotypes[NUM_FLAVORS] = {PIO_IOTYPE_PNETCDF, PIO_IOTYPE_NETCDF,
			       PIO_IOTYPE_NETCDF4C, PIO_IOTYPE_NETCDF4P};

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS)))
	ERR(ERR_INIT);

    /* Split world into odd and even. */
    MPI_Comm newcomm;
    int even = my_rank % 2 ? 0 : 1;
    if ((ret = MPI_Comm_split(MPI_COMM_WORLD, even, 0, &newcomm)))
	MPIERR(ret);
    printf("%d newcomm = %d even = %d\n", my_rank, newcomm, even);

    /* Get rank in new communicator and its size. */
    int new_rank, new_size;
    if ((ret = MPI_Comm_rank(newcomm, &new_rank)))
	MPIERR(ret);
    if ((ret = MPI_Comm_size(newcomm, &new_size)))
	MPIERR(ret);
    printf("%d newcomm = %d new_rank = %d new_size = %d\n", my_rank, newcomm,
	   new_rank, new_size);

    /* Initialize PIO system. */
    if ((ret = PIOc_Init_Intracomm(newcomm, new_size, STRIDE, BASE, REARRANGER, &iosysid)))
	ERR(ret);

    /* Initialize another PIO system. */
    if ((ret = PIOc_Init_Intracomm(MPI_COMM_WORLD, ntasks, STRIDE, BASE, REARRANGER,
				   &iosysid_world)))
	ERR(ret);

    int ncid[NUM_FLAVORS];
    int ncid2[NUM_FLAVORS];
    for (int i = 2; i < 4; i++)
    {
	char fn[NUM_FILES][NC_MAX_NAME + 1];
	for (int f = 0; f < NUM_FILES; f++)
	{
	    sprintf(fn[f], "pio_iosys_test_file%d.nc", f);
	    if ((ret = create_file(iosysid_world, iotypes[i], fn[f], my_rank)))
		ERR(ret);
	}

	MPI_Barrier(MPI_COMM_WORLD);

	/* Open the first file with world iosystem. */
	if ((ret = PIOc_openfile(iosysid_world, &ncid[i], &iotypes[i], fn[1], PIO_WRITE)))
	    return ret;

	/* Now have the odd/even communicators each check one of the
	 * remaining files. */
	char *fname = even ? fn[1] : fn[2];
	printf("\n***\n");
	if ((ret = PIOc_openfile(iosysid, &ncid2[i], &iotypes[i], fname, PIO_WRITE)))
	    return ret;
    } /* next iotype */

    /* Close the still-open files. */
    for (int i = 2; i < 4; i++)
    {
	if ((ret = PIOc_closefile(ncid[i])))
	    ERR(ret);
	if ((ret = PIOc_closefile(ncid2[i])))
	    ERR(ret);
    }

    /* Finalize PIO system. */
    if ((ret = PIOc_finalize(iosysid)))
	ERR(ret);

    /* Finalize PIO system. */
    if ((ret = PIOc_finalize(iosysid_world)))
	ERR(ret);

    /* Finalize test. */
    printf("%d %s finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
	ERR(ERR_AWFUL);

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
