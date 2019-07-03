/* Test netcdf integration layer.

   Ed Hartnett
*/

#include "config.h"
#include <nc_tests.h>
#include "err_macros.h"
#include "netcdf.h"
#include "nc4dispatch.h"

#define FILE_NAME "tst_pio_udf.nc"

extern NC_Dispatch NCINT_dispatcher;

int
main(int argc, char **argv)
{
   printf("\n*** Testing netCDF integration layer.\n");
   printf("*** testing simple use of netCDF integration layer format...");
   {
      int ncid;
      int iosysid;
      NC_Dispatch *disp_in;

      /* Create an empty file to play with. */
      if (nc_create(FILE_NAME, 0, &ncid)) ERR;
      if (nc_close(ncid)) ERR;

      /* Initialize the intracomm. */
      if (nc_init_intracomm(NULL, 1, 1, 0, 0, &iosysid)) ERR;

      /* Add our user defined format. */
      if (nc_def_user_format(NC_UDF0, &NCINT_dispatcher, NULL)) ERR;

      /* Check that our user-defined format has been added. */
      if (nc_inq_user_format(NC_UDF0, &disp_in, NULL)) ERR;
      if (disp_in != &NCINT_dispatcher) ERR;

      /* Open file with our defined functions. */
      if (nc_open(FILE_NAME, NC_UDF0, &ncid)) ERR;
      if (nc_close(ncid)) ERR;

         /* Open file again and abort, which is the same as closing it. */
      if (nc_open(FILE_NAME, NC_UDF0, &ncid)) ERR;
      if (nc_inq_format(ncid, NULL) != TEST_VAL_42) ERR;
      if (nc_inq_format_extended(ncid, NULL, NULL) != TEST_VAL_42) ERR;
      if (nc_abort(ncid) != TEST_VAL_42) ERR;
   }
   SUMMARIZE_ERR;
   FINAL_RESULTS;
}
