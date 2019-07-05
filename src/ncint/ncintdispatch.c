/**
 * @file
 * @internal Dispatch layer for netcdf PIO integration.
 *
 * @author Ed Hartnett
 */

#include "config.h"
#include <stdlib.h>
#include "ncintdispatch.h"
#include "pio.h"

/* This is the dispatch object that holds pointers to all the
 * functions that make up the NCINT dispatch interface. */
NC_Dispatch NCINT_dispatcher = {

    NC_FORMATX_NC_HDF4,

    NC_RO_create,
    NC_NCINT_open,

    NC_RO_redef,
    NC_RO__enddef,
    NC_RO_sync,
    NC_NCINT_abort,
    NC_NCINT_close,
    NC_RO_set_fill,
    NC_NOTNC3_inq_base_pe,
    NC_NOTNC3_set_base_pe,
    NC_NCINT_inq_format,
    NC_NCINT_inq_format_extended,

    NC4_inq,
    NC4_inq_type,

    NC_RO_def_dim,
    NC4_inq_dimid,
    NC4_inq_dim,
    NC4_inq_unlimdim,
    NC_RO_rename_dim,

    NC4_inq_att,
    NC4_inq_attid,
    NC4_inq_attname,
    NC_RO_rename_att,
    NC_RO_del_att,
    NC4_get_att,
    NC_RO_put_att,

    NC_RO_def_var,
    NC4_inq_varid,
    NC_RO_rename_var,
    NC_NCINT_get_vara,
    NC_RO_put_vara,
    NCDEFAULT_get_vars,
    NCDEFAULT_put_vars,
    NCDEFAULT_get_varm,
    NCDEFAULT_put_varm,

    NC4_inq_var_all,

    NC_NOTNC4_var_par_access,
    NC_RO_def_var_fill,

    NC4_show_metadata,
    NC4_inq_unlimdims,

    NC4_inq_ncid,
    NC4_inq_grps,
    NC4_inq_grpname,
    NC4_inq_grpname_full,
    NC4_inq_grp_parent,
    NC4_inq_grp_full_ncid,
    NC4_inq_varids,
    NC4_inq_dimids,
    NC4_inq_typeids,
    NC4_inq_type_equal,
    NC_NOTNC4_def_grp,
    NC_NOTNC4_rename_grp,
    NC4_inq_user_type,
    NC4_inq_typeid,

    NC_NOTNC4_def_compound,
    NC_NOTNC4_insert_compound,
    NC_NOTNC4_insert_array_compound,
    NC_NOTNC4_inq_compound_field,
    NC_NOTNC4_inq_compound_fieldindex,
    NC_NOTNC4_def_vlen,
    NC_NOTNC4_put_vlen_element,
    NC_NOTNC4_get_vlen_element,
    NC_NOTNC4_def_enum,
    NC_NOTNC4_insert_enum,
    NC_NOTNC4_inq_enum_member,
    NC_NOTNC4_inq_enum_ident,
    NC_NOTNC4_def_opaque,
    NC_NOTNC4_def_var_deflate,
    NC_NOTNC4_def_var_fletcher32,
    NC_NOTNC4_def_var_chunking,
    NC_NOTNC4_def_var_endian,
    NC_NOTNC4_def_var_filter,
    NC_NOTNC4_set_var_chunk_cache,
    NC_NOTNC4_get_var_chunk_cache
};

const NC_Dispatch* NCINT_dispatch_table = NULL;

/**
 * @internal Initialize NCINT dispatch layer.
 *
 * @return ::NC_NOERR No error.
 * @author Ed Hartnett
 */
int
NC_NCINT_initialize(void)
{
    NCINT_dispatch_table = &NCINT_dispatcher;
    return NC_NOERR;
}

/**
 * @internal Finalize NCINT dispatch layer.
 *
 * @return ::NC_NOERR No error.
 * @author Ed Hartnett
 */
int
NC_NCINT_finalize(void)
{
    return NC_NOERR;
}

/** Default iosysid. */
int diosysid;

#define TEST_VAL_42 42
int
NC_NCINT_open(const char *path, int mode, int basepe, size_t *chunksizehintp,
              void *parameters, const NC_Dispatch *dispatch, NC *nc_file)
{
    int ret;
    nc_file->int_ncid = nc_file->ext_ncid;

    /* Turn of NC_UDF0 in the mode flag. */
    mode = mode & ~NC_UDF0;

    /* /\* Add necessary structs to hold netcdf-4 file data. *\/ */
    /* if ((retval = nc4_nc4f_list_add(nc_file, path, mode))) */
    /*     return retval; */

    /* /\* Open the file with PIO. *\/ */
    /* if ((ret = PIOc_open(diosysid, path, mode, &nc_file->ext_ncid))) */
    /*     return ret; */

    return NC_NOERR;
}

int
NC_NCINT_abort(int ncid)
{
    return TEST_VAL_42;
}

int
NC_NCINT_close(int ncid, void *v)
{
    return NC_NOERR;
}

int
NC_NCINT_inq_format(int ncid, int *formatp)
{
    return TEST_VAL_42;
}

int
NC_NCINT_inq_format_extended(int ncid, int *formatp, int *modep)
{
    return TEST_VAL_42;
}

int
NC_NCINT_get_vara(int ncid, int varid, const size_t *start, const size_t *count,
                  void *value, nc_type t)
{
    return TEST_VAL_42;
}
