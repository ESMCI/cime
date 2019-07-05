/* Test netcdf integration layer.

   Ed Hartnett
*/

#include "config.h"
#include <nc_tests.h>
#include "err_macros.h"
#include "netcdf.h"
#include "nc4dispatch.h"
#include <pio.h>
#include <mpi.h>

#define FILE_NAME "tst_pio_udf.nc"

extern NC_Dispatch NCINT_dispatcher;

int
main(int argc, char **argv)
{
    int my_rank;
    int ntasks;

    /* Initialize MPI. */
    if (MPI_Init(&argc, &argv)) ERR;

    /* Learn my rank and the total number of processors. */
    if (MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)) ERR;
    if (MPI_Comm_size(MPI_COMM_WORLD, &ntasks)) ERR;

    printf("\n*** Testing netCDF integration layer.\n");
    printf("*** testing simple use of netCDF integration layer format...");
    {
        int ncid;
        int iosysid;
        NC_Dispatch *disp_in;

        /* Create an empty file to play with. */
        if (nc_create(FILE_NAME, NC_CLOBBER, &ncid)) ERR;
        if (nc_close(ncid)) ERR;

        /* Initialize the intracomm. */
        if (nc_init_intracomm(MPI_COMM_WORLD, 1, 1, 0, 0, &iosysid)) ERR;

        /* Add our user defined format. */
        if (nc_def_user_format(NC_UDF0, &NCINT_dispatcher, NULL)) ERR;

        /* Create an empty file to play with. */
        /* if (nc_create(FILE_NAME, NC_UDF0, &ncid)) ERR; */
        /* if (nc_close(ncid)) ERR; */

        /* Check that our user-defined format has been added. */
        if (nc_inq_user_format(NC_UDF0, &disp_in, NULL)) ERR;
        if (disp_in != &NCINT_dispatcher) ERR;
        PIOc_set_log_level(3);

        /* Open file with our defined functions. */
        if (nc_open(FILE_NAME, NC_UDF0, &ncid)) ERR;
        if (nc_close(ncid)) ERR;

        /* Close the iosystem. */
        if (nc_free_iosystem(iosysid)) ERR;
    }
    SUMMARIZE_ERR;

    /* Finalize MPI. */
    MPI_Finalize();
    FINAL_RESULTS;
}
