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
#define VAR_NAME "data_var"
#define DIM_NAME_X "dim_x"
#define DIM_NAME_Y "dim_y"
#define DIM_LEN_X 4
#define DIM_LEN_Y 4
#define NDIM2 2

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
        int ncid, ioid;
        int dimid[NDIM2], varid;
        int dimlen[NDIM2] = {DIM_LEN_X, DIM_LEN_Y};
        int iosysid;
        NC_Dispatch *disp_in;
        size_t elements_per_pe;
        size_t *compdof; /* The decomposition mapping. */
        int i;

        /* Turn on logging for PIO library. */
        PIOc_set_log_level(3);

        /* Initialize the intracomm. */
        if (nc_init_intracomm(MPI_COMM_WORLD, 1, 1, 0, 0, &iosysid)) ERR;

        /* Add our user defined format. */
        if (nc_def_user_format(NC_UDF0, &NCINT_dispatcher, NULL)) ERR;

        /* Create a file to play with. */
        if (nc_create(FILE_NAME, NC_UDF0, &ncid)) ERR;
        if (nc_def_dim(ncid, DIM_NAME_X, dimlen[0], &dimid[0])) ERR;
        if (nc_def_dim(ncid, DIM_NAME_Y, dimlen[1], &dimid[1])) ERR;
        if (nc_def_var(ncid, VAR_NAME, NC_INT, NDIM2, dimid, &varid)) ERR;

        /* Create a decomposition for distributed arrays. */
        elements_per_pe = DIM_LEN_X * DIM_LEN_Y / ntasks;
        if (!(compdof = malloc(elements_per_pe * sizeof(size_t))))
            ERR;
        for (i = 0; i < elements_per_pe; i++)
            compdof[i] = my_rank * elements_per_pe + i;

        /* Create the PIO decomposition for this test. */
        if (nc_init_decomp(iosysid, PIO_INT, NDIM2, dimlen, elements_per_pe,
                           compdof, &ioid, 0, NULL, NULL)) ERR;
        free(compdof);

        if (nc_close(ncid)) ERR;

        /* Check that our user-defined format has been added. */
        if (nc_inq_user_format(NC_UDF0, &disp_in, NULL)) ERR;
        if (disp_in != &NCINT_dispatcher) ERR;

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
