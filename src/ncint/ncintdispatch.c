/**
 * @file
 * @internal Dispatch layer for netcdf PIO integration.
 *
 * @author Ed Hartnett
 */

#include "config.h"
#include <stdlib.h>
#include "ncintdispatch.h"
#include "nc4dispatch.h"
#include "nc4internal.h"
#include "pio.h"
#include "pio_internal.h"

/** Default iosysid. */
int diosysid;

/** Did we initialize user-defined format? */
int ncint_initialized = 0;

#define TEST_VAL_42 42

/* This is the dispatch object that holds pointers to all the
 * functions that make up the NCINT dispatch interface. */
NC_Dispatch NCINT_dispatcher = {

    NC_FORMATX_UDF0,

    PIO_NCINT_create,
    PIO_NCINT_open,

    PIO_NCINT_redef,
    PIO_NCINT__enddef,
    PIO_NCINT_sync,
    PIO_NCINT_abort,
    PIO_NCINT_close,
    PIO_NCINT_set_fill,
    NC_NOTNC3_inq_base_pe,
    NC_NOTNC3_set_base_pe,
    PIO_NCINT_inq_format,
    PIO_NCINT_inq_format_extended,

    PIO_NCINT_inq,
    NC4_inq_type,

    PIO_NCINT_def_dim,
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

    PIO_NCINT_def_var,
    NC4_inq_varid,
    NC_RO_rename_var,
    PIO_NCINT_get_vara,
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
PIO_NCINT_initialize(void)
{
    int ret;

    NCINT_dispatch_table = &NCINT_dispatcher;

    /* Add our user defined format. */
    if ((ret = nc_def_user_format(NC_UDF0, &NCINT_dispatcher, NULL)))
        return ret;
    ncint_initialized++;

    return NC_NOERR;
}

/**
 * @internal Finalize NCINT dispatch layer.
 *
 * @return ::NC_NOERR No error.
 * @author Ed Hartnett
 */
int
PIO_NCINT_finalize(void)
{
    return NC_NOERR;
}

int
PIO_NCINT_create(const char* path, int cmode, size_t initialsz, int basepe,
                 size_t *chunksizehintp, void *parameters,
                 const NC_Dispatch *dispatch, NC *nc_file)
{
    int iotype;
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    int ret;

    LOG((1, "PIO_NCINT_create path = %s mode = %x", path, mode));

    /* Get the IO system info from the id. */
    if (!(ios = pio_get_iosystem_from_id(diosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* Turn of NC_UDF0 in the mode flag. */
    cmode = cmode & ~NC_UDF0;

    /* Find the IOTYPE from the mode flag. */
    if ((ret = find_iotype_from_omode(cmode, &iotype)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    /* Add necessary structs to hold netcdf-4 file data. */
    if ((ret = nc4_nc4f_list_add(nc_file, path, cmode)))
        return ret;

    /* Open the file with PIO. Tell openfile_retry to accept the
     * externally assigned ncid. */
    if ((ret = PIOc_createfile_int(diosysid,  &nc_file->ext_ncid, &iotype,
                                   path, cmode, 1)))
        return ret;

    return PIO_NOERR;
}

int
PIO_NCINT_open(const char *path, int mode, int basepe, size_t *chunksizehintp,
               void *parameters, const NC_Dispatch *dispatch, NC *nc_file)
{
    int iotype;
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    int ret;

    LOG((1, "PIO_NCINT_open path = %s mode = %x", path, mode));

    /* Get the IO system info from the id. */
    if (!(ios = pio_get_iosystem_from_id(diosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* Turn of NC_UDF0 in the mode flag. */
    mode = mode & ~NC_UDF0;

    /* Find the IOTYPE from the mode flag. */
    if ((ret = find_iotype_from_omode(mode, &iotype)))
        return pio_err(ios, NULL, ret, __FILE__, __LINE__);

    /* Add necessary structs to hold netcdf-4 file data. */
    if ((ret = nc4_nc4f_list_add(nc_file, path, mode)))
        return ret;

    /* Open the file with PIO. Tell openfile_retry to accept the
     * externally assigned ncid. */
    if ((ret = PIOc_openfile_retry(diosysid, &nc_file->ext_ncid, &iotype,
                                   path, mode, 0, 1)))
        return ret;

    return NC_NOERR;
}

int
PIO_NCINT_def_dim(int ncid, const char *name, size_t len, int *idp)
{
    return PIOc_def_dim(ncid, name, len, idp);
}

int
PIO_NCINT_def_var(int ncid, const char *name, nc_type xtype, int ndims,
                  const int *dimidsp, int *varidp)
{
    return PIOc_def_var(ncid, name, xtype, ndims, dimidsp, varidp);
}

/**
 * @internal This just calls nc_enddef, ignoring the extra parameters.
 *
 * @param ncid File and group ID.
 * @param h_minfree Ignored.
 * @param v_align Ignored.
 * @param v_minfree Ignored.
 * @param r_align Ignored.
 *
 * @return ::NC_NOERR No error.
 * @author Ed Hartnett
 */
int
PIO_NCINT__enddef(int ncid, size_t h_minfree, size_t v_align,
                  size_t v_minfree, size_t r_align)
{
    return PIOc_enddef(ncid);
}

/**
 * @internal Put the file back in redef mode. This is done
 * automatically for netcdf-4 files, if the user forgets.
 *
 * @param ncid File and group ID.
 *
 * @return ::NC_NOERR No error.
 * @author Ed Hartnett
 */
int
PIO_NCINT_redef(int ncid)
{
    return PIOc_redef(ncid);
}

/**
 * @internal Flushes all buffers associated with the file, after
 * writing all changed metadata. This may only be called in data mode.
 *
 * @param ncid File and group ID.
 *
 * @return ::NC_NOERR No error.
 * @return ::NC_EBADID Bad ncid.
 * @return ::NC_EINDEFINE Classic model file is in define mode.
 * @author Ed Hartnett
 */
int
PIO_NCINT_sync(int ncid)
{
    return PIOc_sync(ncid);
}

int
PIO_NCINT_abort(int ncid)
{
    return TEST_VAL_42;
}

int
PIO_NCINT_close(int ncid, void *v)
{
    return PIOc_closefile(ncid);
}

/**
 * @internal Set fill mode.
 *
 * @param ncid File ID.
 * @param fillmode File mode.
 * @param old_modep Pointer that gets old mode. Ignored if NULL.
 *
 * @return ::NC_NOERR No error.
 * @author Ed Hartnett
 */
int
PIO_NCINT_set_fill(int ncid, int fillmode, int *old_modep)
{
    return PIOc_set_fill(ncid, fillmode, old_modep);
}

int
PIO_NCINT_inq_format(int ncid, int *formatp)
{
    return TEST_VAL_42;
}

int
PIO_NCINT_inq_format_extended(int ncid, int *formatp, int *modep)
{
    return TEST_VAL_42;
}

/**
 * @internal Learn number of dimensions, variables, global attributes,
 * and the ID of the first unlimited dimension (if any).
 *
 * @note It's possible for any of these pointers to be NULL, in which
 * case don't try to figure out that value.
 *
 * @param ncid File and group ID.
 * @param ndimsp Pointer that gets number of dimensions.
 * @param nvarsp Pointer that gets number of variables.
 * @param nattsp Pointer that gets number of global attributes.
 * @param unlimdimidp Pointer that gets first unlimited dimension ID,
 * or -1 if there are no unlimied dimensions.
 *
 * @return ::NC_NOERR No error.
 * @author Ed Hartnett
 */
int
PIO_NCINT_inq(int ncid, int *ndimsp, int *nvarsp, int *nattsp, int *unlimdimidp)
{
    return PIOc_inq(ncid, ndimsp, nvarsp, nattsp, unlimdimidp);
}

/**
 * @internal Get the name and size of a type. For strings, 1 is
 * returned. For VLEN the base type len is returned.
 *
 * @param ncid File and group ID.
 * @param typeid1 Type ID.
 * @param name Gets the name of the type.
 * @param size Gets the size of one element of the type in bytes.
 *
 * @return ::NC_NOERR No error.
 * @return ::NC_EBADID Bad ncid.
 * @return ::NC_EBADTYPE Type not found.
 * @author Ed Hartnett
 */
int
PIO_NCINT_inq_type(int ncid, nc_type typeid1, char *name, size_t *size)
{
    return PIOc_inq_type(ncid, typeid1, name, (PIO_Offset *)size);
}

int
PIO_NCINT_get_vara(int ncid, int varid, const size_t *start, const size_t *count,
                   void *value, nc_type t)
{
    return TEST_VAL_42;
}
