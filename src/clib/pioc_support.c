/** @file
 * Support functions for the PIO library.
 */
#include <config.h>
#if PIO_ENABLE_LOGGING
#include <stdarg.h>
#include <unistd.h>
#endif /* PIO_ENABLE_LOGGING */
#include <pio.h>
#include <pio_internal.h>

#include <execinfo.h>

#define VERSNO 2001

/* Some logging constants. */
#if PIO_ENABLE_LOGGING
#define MAX_LOG_MSG 1024
#define MAX_RANK_STR 12
#define ERROR_PREFIX "ERROR: "
#define NC_LEVEL_DIFF 3
int pio_log_level = 0;
int pio_log_ref_cnt = 0;
int my_rank;
FILE *LOG_FILE = NULL;
#endif /* PIO_ENABLE_LOGGING */

/**
 * The PIO library maintains its own set of ncids. This is the next
 * ncid number that will be assigned.
*/
extern int pio_next_ncid;

/** The default error handler used when iosystem cannot be located. */
extern int default_error_handler;

/** Default settings for swap memory. */
static pio_swapm_defaults swapm_defaults;

/**
 * Return a string description of an error code. If zero is passed,
 * the errmsg will be "No error".
 *
 * @param pioerr the error code returned by a PIO function call.
 * @param errmsg Pointer that will get the error message. The message
 * will be PIO_MAX_NAME chars or less.
 * @return 0 on success.
 */
int PIOc_strerror(int pioerr, char *errmsg)
{
    LOG((1, "PIOc_strerror pioerr = %d", pioerr));

    /* Caller must provide this. */
    pioassert(errmsg, "pointer to errmsg string must be provided", __FILE__, __LINE__);

    /* System error? NetCDF and pNetCDF errors are always negative. */
    if (pioerr > 0)
    {
        const char *cp = (const char *)strerror(pioerr);
        if (cp)
            strncpy(errmsg, cp, PIO_MAX_NAME);
        else
            strcpy(errmsg, "Unknown Error");
    }
    else if (pioerr == PIO_NOERR)
        strcpy(errmsg, "No error");
#if defined(_NETCDF)
    else if (pioerr <= NC2_ERR && pioerr >= NC4_LAST_ERROR)     /* NetCDF error? */
        strncpy(errmsg, nc_strerror(pioerr), NC_MAX_NAME);
#endif /* endif defined(_NETCDF) */
#if defined(_PNETCDF)
    else if (pioerr > PIO_FIRST_ERROR_CODE)     /* pNetCDF error? */
        strncpy(errmsg, ncmpi_strerror(pioerr), NC_MAX_NAME);
#endif /* defined( _PNETCDF) */
    else
        /* Handle PIO errors. */
        switch(pioerr)
        {
        case PIO_EBADIOTYPE:
            strcpy(errmsg, "Bad IO type");
            break;
        default:
            strcpy(errmsg, "Unknown Error: Unrecognized error code");
        }

    return PIO_NOERR;
}

/**
 * Set the logging level if PIO was built with
 * PIO_ENABLE_LOGGING. Set to -1 for nothing, 0 for errors only, 1 for
 * important logging, and so on. Log levels below 1 are only printed
 * on the io/component root.
 *
 * A log file is also produced for each task. The file is called
 * pio_log_X.txt, where X is the (0-based) task number.
 *
 * If the library is not built with logging, this function does
 * nothing.
 *
 * @param level the logging level, 0 for errors only, 5 for max
 * verbosity.
 * @returns 0 on success, error code otherwise.
 */
int PIOc_set_log_level(int level)
{
    int ret;

#if PIO_ENABLE_LOGGING
    /* Set the log level. */
    pio_log_level = level;

#if NETCDF_C_LOGGING_ENABLED
    /* If netcdf logging is available turn it on starting at level = 4. */
    if (level > NC_LEVEL_DIFF)
        if ((ret = nc_set_log_level(level - NC_LEVEL_DIFF)))
            return pio_err(NULL, NULL, ret, __FILE__, __LINE__);
#endif /* NETCDF_C_LOGGING_ENABLED */
#endif /* PIO_ENABLE_LOGGING */

    return PIO_NOERR;
}

/**
 * Initialize logging.  Open log file, if not opened yet, or increment
 * ref count if already open.
 */
void pio_init_logging(void)
{
#if PIO_ENABLE_LOGGING
    char log_filename[NC_MAX_NAME];

    if (!LOG_FILE)
    {
        /* Create a filename with the rank in it. */
        MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
        sprintf(log_filename, "pio_log_%d.txt", my_rank);

        /* Open a file for this rank to log messages. */
        LOG_FILE = fopen(log_filename, "w");

        pio_log_ref_cnt = 1;
    }
    else
    {
        pio_log_ref_cnt++;
    }
#endif /* PIO_ENABLE_LOGGING */
}

/**
 * Finalize logging - close log files, if open.
 */
void pio_finalize_logging(void )
{
#if PIO_ENABLE_LOGGING
    pio_log_ref_cnt -= 1;
    if (LOG_FILE)
    {
        if (pio_log_ref_cnt == 0)
        {
            fclose(LOG_FILE);
            LOG_FILE = NULL;
        }
        else
            LOG((2, "pio_finalize_logging, postpone close, ref_cnt = %d",
                 pio_log_ref_cnt));
    }
#endif /* PIO_ENABLE_LOGGING */
}

#if PIO_ENABLE_LOGGING
/**
 * This function prints out a message, if the severity of the message
 * is lower than the global pio_log_level. To use it, do something
 * like this:
 *
 * pio_log(0, "this computer will explode in %d seconds", i);
 *
 * After the first arg (the severity), use the rest like a normal
 * printf statement. Output will appear on stdout.
 * This function is heavily based on the function in section 15.5 of
 * the C FAQ.
 *
 * In code this functions should be wrapped in the LOG(()) macro.
 *
 * @param severity the severity of the message, 0 for error messages,
 * then increasing levels of verbosity.
 * @param fmt the format string.
 * @param ... the arguments used in format string.
 */
void pio_log(int severity, const char *fmt, ...)
{
    va_list argp;
    int t;
    int rem_len = MAX_LOG_MSG;
    char msg[MAX_LOG_MSG];
    char *ptr = msg;
    char rank_str[MAX_RANK_STR];

    /* If the severity is greater than the log level, we don't print
       this message. */
    if (severity > pio_log_level)
        return;

    /* If the severity is 0, only print on rank 0. */
    if (severity < 1 && my_rank != 0)
        return;

    /* If the severity is zero, this is an error. Otherwise insert that
       many tabs before the message. */
    if (!severity)
    {
        strncpy(ptr, ERROR_PREFIX, (rem_len > 0) ? rem_len : 0);
        ptr += strlen(ERROR_PREFIX);
        rem_len -= strlen(ERROR_PREFIX);
    }
    for (t = 0; t < severity; t++)
    {
        strncpy(ptr++, "\t", (rem_len > 0) ? rem_len : 0);
        rem_len--;
    }

    /* Show the rank. */
    snprintf(rank_str, MAX_RANK_STR, "%d ", my_rank);
    strncpy(ptr, rank_str, (rem_len > 0) ? rem_len : 0);
    ptr += strlen(rank_str);
    rem_len -= strlen(rank_str);

    /* Print out the variable list of args with vprintf. */
    va_start(argp, fmt);
    vsnprintf(ptr, ((rem_len > 0) ? rem_len : 0), fmt, argp);
    va_end(argp);

    /* Put on a final linefeed. */
    ptr = msg + strlen(msg);
    rem_len = MAX_LOG_MSG - strlen(msg);
    strncpy(ptr, "\n\0", (rem_len > 0) ? rem_len : 0);

    /* Send message to stdout. */
    fprintf(stdout, "%s", msg);

    /* Send message to log file. */
    if (LOG_FILE)
        fprintf(LOG_FILE, "%s", msg);

    /* Ensure an immediate flush of stdout. */
    fflush(stdout);
    if (LOG_FILE)
        fflush(LOG_FILE);
}
#endif /* PIO_ENABLE_LOGGING */

/**
 * Obtain a backtrace and print it to stderr.
 *
 * @param fp file pointer to send output to
 */
void print_trace(FILE *fp)
{
    void *array[10];
    size_t size;
    char **strings;
    size_t i;

    /* Note that this won't actually work. */
    if (fp == NULL)
        fp = stderr;

    size = backtrace(array, 10);
    strings = backtrace_symbols(array, size);

    fprintf(fp,"Obtained %zd stack frames.\n", size);

    for (i = 0; i < size; i++)
        fprintf(fp,"%s\n", strings[i]);

    free(strings);
}

/**
 * Exit due to lack of memory.
 *
 * @param ios the iosystem description struct
 * @param req amount of memory that was being requested
 * @param fname name of code file where error occured
 * @param line the line of code where the error occurred.
 */
void piomemerror(iosystem_desc_t ios, size_t req, char *fname, int line)
{
    char msg[80];
    sprintf(msg, "out of memory requesting: %ld", req);
    cn_buffer_report(ios, false);
    piodie(msg, fname, line);
}

/**
 * Abort program and call MPI_Abort().
 *
 * @param msg an error message
 * @param fname name of code file where error occured
 * @param line the line of code where the error occurred.
 */
void piodie(const char *msg, const char *fname, int line)
{
    fprintf(stderr,"Abort with message %s in file %s at line %d\n",
            msg ? msg : "_", fname ? fname : "_", line);

    print_trace(stderr);
#ifdef MPI_SERIAL
    abort();
#else
    MPI_Abort(MPI_COMM_WORLD, -1);
#endif
}

/**
 * Perform an assert. Note that this function does nothing if NDEBUG
 * is defined.
 *
 * @param expression the expression to be evaluated
 * @param msg an error message
 * @param fname name of code file where error occured
 * @param line the line of code where the error occurred.
 */
void pioassert(_Bool expression, const char *msg, const char *fname, int line)
{
#ifndef NDEBUG
    if (!expression)
        piodie(msg, fname, line);
#endif
}

/**
 * Handle MPI errors. An error message is sent to stderr, then the
 * check_netcdf() function is called with PIO_EIO.
 *
 * @param file pointer to the file_desc_t info. Ignored if NULL.
 * @param mpierr the MPI return code to handle
 * @param filename the name of the code file where error occured.
 * @param line the line of code where error occured.
 * @return PIO_NOERR for no error, otherwise PIO_EIO.
 */
int check_mpi(file_desc_t *file, int mpierr, const char *filename,
              int line)
{
    return check_mpi2(NULL, file, mpierr, filename, line);
}

/**
 * Handle MPI errors. An error message is sent to stderr, then the
 * check_netcdf() function is called with PIO_EIO. This version of the
 * function accepts an ios parameter, for the (rare) occasions where
 * we have an ios but not a file.
 *
 * @param ios pointer to the iosystem_info_t. May be NULL.
 * @param file pointer to the file_desc_t info. May be NULL.
 * @param mpierr the MPI return code to handle
 * @param filename the name of the code file where error occured.
 * @param line the line of code where error occured.
 * @return PIO_NOERR for no error, otherwise PIO_EIO.
 */
int check_mpi2(iosystem_desc_t *ios, file_desc_t *file, int mpierr,
               const char *filename, int line)
{
    if (mpierr)
    {
        char errstring[MPI_MAX_ERROR_STRING];
        int errstrlen;

        /* If we can get an error string from MPI, print it to stderr. */
        if (!MPI_Error_string(mpierr, errstring, &errstrlen))
            fprintf(stderr, "MPI ERROR: %s in file %s at line %d\n",
                    errstring, filename ? filename : "_", line);

        /* Handle all MPI errors as PIO_EIO. */
        return pio_err(ios, file, PIO_EIO, filename, line);
    }
    return PIO_NOERR;
}

/**
 * Check the result of a netCDF API call.
 *
 * @param file pointer to the PIO structure describing this
 * file. Ignored if NULL.
 * @param status the return value from the netCDF call.
 * @param fname the name of the code file.
 * @param line the line number of the netCDF call in the code.
 * @return the error code
 */
int check_netcdf(file_desc_t *file, int status, const char *fname, int line)
{
    return check_netcdf2(NULL, file, status, fname, line);
}

/**
 * Check the result of a netCDF API call. This is the same as
 * check_netcdf() except for the extra iosystem_desc_t pointer, which
 * is used to determine error handling when there is no file_desc_t
 * pointer.
 *
 * @param ios pointer to the iosystem description struct. Ignored if NULL.
 * @param file pointer to the PIO structure describing this file. Ignored if NULL.
 * @param status the return value from the netCDF call.
 * @param fname the name of the code file.
 * @param line the line number of the netCDF call in the code.
 * @return the error code
 */
int check_netcdf2(iosystem_desc_t *ios, file_desc_t *file, int status,
                  const char *fname, int line)
{
    int eh = default_error_handler; /* Error handler that will be used. */
    char errmsg[PIO_MAX_NAME + 1];  /* Error message. */

    /* User must provide this. */
    pioassert(fname, "code file name must be provided", __FILE__, __LINE__);

    /* No harm, no foul. */
    if (status == PIO_NOERR)
        return PIO_NOERR;

    LOG((1, "check_netcdf2 status = %d fname = %s line = %d", status, fname, line));

    /* Pick an error handler. File settings override iosystem
     * settings. */
    if (ios)
        eh = ios->error_handler;
    if (file)
        eh = file->iosystem->error_handler;
    pioassert(eh == PIO_INTERNAL_ERROR || eh == PIO_BCAST_ERROR || eh == PIO_RETURN_ERROR,
              "invalid error handler", __FILE__, __LINE__);
    LOG((2, "check_netcdf2 chose error handler = %d", eh));

    /* Get an error message. */
    if (!PIOc_strerror(status, errmsg))
    {
        fprintf(stderr, "%s\n", errmsg);
        LOG((1, "check_netcdf2 errmsg = %s", errmsg));
    }

    /* Decide what to do based on the error handler. */
    if (eh == PIO_INTERNAL_ERROR)
        piodie(errmsg, fname, line);        /* Die! */
    else if (eh == PIO_BCAST_ERROR && ios)  /* Not sure what this will do. */
        MPI_Bcast(&status, 1, MPI_INTEGER, ios->ioroot, ios->my_comm);

    /* For PIO_RETURN_ERROR, just return the error. */
    return status;
}

/**
 * Handle an error in PIO. This will consult the error handler
 * settings and either call MPI_Abort() or return an error code.
 *
 * The error hanlder has three settings:
 *
 * Errors cause abort: PIO_INTERNAL_ERROR.
 *
 * Error codes are broadcast to all tasks: PIO_BCAST_ERROR.
 *
 * Errors are returned to caller with no internal action:
 * PIO_RETURN_ERROR.
 *
 * @param ios pointer to the IO system info. Ignored if NULL.
 * @param file pointer to the file description data. Ignored if
 * NULL. If not NULL, then file level error handling is applied before
 * IO system level error handling.
 * @param err_num the error code
 * @param fname name of code file where error occured.
 * @param line the line of code where the error occurred.
 * @returns err_num if abort is not called.
 */
int pio_err(iosystem_desc_t *ios, file_desc_t *file, int err_num, const char *fname,
            int line)
{
    char err_msg[PIO_MAX_NAME + 1];
    int err_handler = default_error_handler; /* Default error handler. */
    int ret;

    /* User must provide this. */
    pioassert(fname, "file name must be provided", __FILE__, __LINE__);

    /* No harm, no foul. */
    if (err_num == PIO_NOERR)
        return PIO_NOERR;

    /* Get the error message. */
    if ((ret = PIOc_strerror(err_num, err_msg)))
        return ret;

    /* If logging is in use, log an error message. */
    LOG((0, "%s err_num = %d fname = %s line = %d", err_msg, err_num, fname ? fname : '\0', line));

    /* What error handler should we use? */
    if (file)
        err_handler = file->iosystem->error_handler;
    else if (ios)
        err_handler = ios->error_handler;

    LOG((2, "pio_err chose error handler = %d", err_handler));

    /* Should we abort? */
    if (err_handler == PIO_INTERNAL_ERROR)
    {
        /* For debugging only, this will print a traceback of the call tree.  */
        print_trace(stderr);
        MPI_Abort(MPI_COMM_WORLD, -1);
    }

    /* What should we do here??? */
    if (err_handler == PIO_BCAST_ERROR)
    {
        /* ??? */
    }

    /* If abort was not called, we'll get here. */
    return err_num;
}

/**
 * Allocate an region.
 *
 * ndims the number of dimensions for the data in this region.
 * @returns a pointer to the newly allocated io_region struct.
 */
io_region *alloc_region(int ndims)
{
    io_region *region;

    /* Allocate memory for the io_region struct. */
    if (!(region = bget(sizeof(io_region))))
        return NULL;

    /* Allocate memory for the array of start indicies. */
    if (!(region->start = bget(ndims * sizeof(PIO_Offset))))
    {
        brel(region);
        return NULL;
    }

    /* Allocate memory for the array of counts. */
    if (!(region->count = bget(ndims * sizeof(PIO_Offset))))
    {
        brel(region);
        brel(region->start);
        return NULL;
    }

    region->loffset = 0;
    region->next = NULL;

    /* Initialize start and count arrays to zero. */
    for (int i = 0; i < ndims; i++)
    {
        region->start[i] = 0;
        region->count[i] = 0;
    }

    return region;
}

/**
 * Allocate space for an IO description struct.
 *
 * @param piotype the PIO data type (ex. PIO_FLOAT, PIO_INT, etc.).
 * @param ndims the number of dimensions.
 * @returns pointer to the newly allocated io_desc_t or NULL if
 * allocation failed.
 */
io_desc_t *malloc_iodesc(int piotype, int ndims)
{
    io_desc_t *iodesc;

    /* Allocate space for the io_desc_t struct. */
    if (!(iodesc = calloc(1, sizeof(io_desc_t))))
        return NULL;

    /* Decide on the base type. */
    switch(piotype)
    {
    case PIO_REAL:
        iodesc->basetype = MPI_FLOAT;
        break;
    case PIO_DOUBLE:
        iodesc->basetype = MPI_DOUBLE;
        break;
    case PIO_CHAR:
        iodesc->basetype = MPI_CHAR;
        break;
    case PIO_INT:
    default:
        iodesc->basetype = MPI_INTEGER;
        break;
    }

    /* Initialize some values in the struct. */
    iodesc->maxregions = 1;
    iodesc->ioid = -1;
    iodesc->ndims = ndims;
    iodesc->firstregion = alloc_region(ndims);

    /* Set the swap memory settings to defaults. */
    iodesc->handshake = swapm_defaults.handshake;
    iodesc->isend = swapm_defaults.isend;
    iodesc->max_requests = swapm_defaults.nreqs;

    return iodesc;
}

/**
 * Free a region list.
 *
 * top a pointer to the start of the list to free.
 */
void free_region_list(io_region *top)
{
    io_region *ptr, *tptr;

    ptr = top;
    while (ptr)
    {
        if (ptr->start)
            brel(ptr->start);
        if (ptr->count)
            brel(ptr->count);
        tptr = ptr;
        ptr = ptr->next;
        brel(tptr);
    }
}

/**
 * Free a decomposition map.
 *
 * @param iosysid the IO system ID.
 * @param ioid the ID of the decomposition map to free.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_freedecomp(int iosysid, int ioid)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    int i;
    int mpierr; /* Return code for MPI calls. */

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    if (!(iodesc = pio_get_iodesc_from_id(ioid)))
        return pio_err(ios, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* Free the map. */
    free(iodesc->map);

    /* Free the dimlens. */
    free(iodesc->dimlen);

    if (iodesc->gsize)
        free(iodesc->gsize);

    if (iodesc->rfrom)
        free(iodesc->rfrom);

    if (iodesc->rtype)
    {
        for (i = 0; i < iodesc->nrecvs; i++)
            if (iodesc->rtype[i] != PIO_DATATYPE_NULL)
                if ((mpierr = MPI_Type_free(iodesc->rtype + i)))
                    return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);

        free(iodesc->rtype);
    }

    if (iodesc->stype)
    {
        for (i = 0; i < iodesc->num_stypes; i++)
            if (iodesc->stype[i] != PIO_DATATYPE_NULL)
                if ((mpierr = MPI_Type_free(iodesc->stype + i)))
                    return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);

        iodesc->num_stypes = 0;
        free(iodesc->stype);
    }

    if (iodesc->scount)
        free(iodesc->scount);

    if (iodesc->rcount)
        free(iodesc->rcount);

    if (iodesc->sindex)
        free(iodesc->sindex);

    if (iodesc->rindex)
        free(iodesc->rindex);

    if (iodesc->firstregion)
        free_region_list(iodesc->firstregion);

    if (iodesc->fillregion)
        free_region_list(iodesc->fillregion);

    if (iodesc->rearranger == PIO_REARR_SUBSET)
        if ((mpierr = MPI_Comm_free(&iodesc->subset_comm)))
            return check_mpi2(ios, NULL, mpierr, __FILE__, __LINE__);

    return pio_delete_iodesc_from_list(ioid);
}

/**
 * Read a decomposition map from a file.
 *
 * @param file the filename
 * @param ndims pointer to an int with the number of dims.
 * @param gdims pointer to an array of dimension ids.
 * @param fmaplen
 * @param map
 * @param comm
 * @returns 0 for success, error code otherwise.
 */
int PIOc_readmap(const char *file, int *ndims, int **gdims, PIO_Offset *fmaplen,
                 PIO_Offset **map, MPI_Comm comm)
{
    int npes, myrank;
    int rnpes, rversno;
    int j;
    int *tdims;
    PIO_Offset *tmap;
    MPI_Status status;
    PIO_Offset maplen;
    int mpierr; /* Return code for MPI calls. */

    /* Check inputs. */
    if (!ndims || !gdims || !fmaplen || !map)
        return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

    if ((mpierr = MPI_Comm_size(comm, &npes)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    if ((mpierr = MPI_Comm_rank(comm, &myrank)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    if (myrank == 0)
    {
        FILE *fp = fopen(file, "r");
        if (!fp)
            piodie("Failed to open dof file",__FILE__,__LINE__);

        fscanf(fp,"version %d npes %d ndims %d\n",&rversno, &rnpes, ndims);

        if (rversno != VERSNO)
            return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

        if (rnpes < 1 || rnpes > npes)
            return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

        if ((mpierr = MPI_Bcast(&rnpes, 1, MPI_INT, 0, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        if ((mpierr = MPI_Bcast(ndims, 1, MPI_INT, 0, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        if (!(tdims = calloc(*ndims, sizeof(int))))
            return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);
        for (int i = 0; i < *ndims; i++)
            fscanf(fp,"%d ", tdims + i);

        if ((mpierr = MPI_Bcast(tdims, *ndims, MPI_INT, 0, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);

        for (int i = 0; i < rnpes; i++)
        {
            fscanf(fp, "%d %ld", &j, &maplen);
            if (j != i)  // Not sure how this could be possible
                return pio_err(NULL, NULL, PIO_EINVAL, __FILE__, __LINE__);

            if (!(tmap = malloc(maplen * sizeof(PIO_Offset))))
                return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);
            for (j = 0; j < maplen; j++)
                fscanf(fp, "%ld ", tmap+j);

            if (i > 0)
            {
                if ((mpierr = MPI_Send(&maplen, 1, PIO_OFFSET, i, i + npes, comm)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                if ((mpierr = MPI_Send(tmap, maplen, PIO_OFFSET, i, i, comm)))
                    return check_mpi(NULL, mpierr, __FILE__, __LINE__);
                free(tmap);
            }
            else
            {
                *map = tmap;
                *fmaplen = maplen;
            }
        }
        fclose(fp);
    }
    else
    {
        if ((mpierr = MPI_Bcast(&rnpes, 1, MPI_INT, 0, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        if ((mpierr = MPI_Bcast(ndims, 1, MPI_INT, 0, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        if (!(tdims = calloc(*ndims, sizeof(int))))
            return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);
        if ((mpierr = MPI_Bcast(tdims, *ndims, MPI_INT, 0, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);

        if (myrank < rnpes)
        {
            if ((mpierr = MPI_Recv(&maplen, 1, PIO_OFFSET, 0, myrank + npes, comm, &status)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            if (!(tmap = malloc(maplen * sizeof(PIO_Offset))))
                piodie("Memory allocation error ", __FILE__, __LINE__);
            if ((mpierr = MPI_Recv(tmap, maplen, PIO_OFFSET, 0, myrank, comm, &status)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            *map = tmap;
        }
        else
        {
            tmap = NULL;
            maplen = 0;
        }
        *fmaplen = maplen;
    }
    *gdims = tdims;
    return PIO_NOERR;
}

/**
 * Read a decomposition map from file.
 *
 * @param file the filename
 * @param ndims pointer to the number of dimensions
 * @param gdims pointer to an array of dimension ids
 * @param maplen pointer to the length of the map
 * @param map pointer to the map array
 * @param f90_comm
 * @returns 0 for success, error code otherwise.
 */
int PIOc_readmap_from_f90(const char *file, int *ndims, int **gdims, PIO_Offset *maplen,
                          PIO_Offset **map, int f90_comm)
{
    return PIOc_readmap(file, ndims, gdims, maplen, map, MPI_Comm_f2c(f90_comm));
}

/**
 * Write the decomposition map to a file.
 *
 * @param file the filename to be used.
 * @param iosysid the IO system ID.
 * @param ioid the ID of the IO description.
 * @param comm an MPI communicator.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_write_decomp(const char *file, int iosysid, int ioid, MPI_Comm comm)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;

    LOG((1, "PIOc_write_decomp file = %s iosysid = %d ioid = %d", file, iosysid, ioid));

    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    if (!(iodesc = pio_get_iodesc_from_id(ioid)))
        return pio_err(ios, NULL, PIO_EBADID, __FILE__, __LINE__);

    return PIOc_writemap(file, iodesc->ndims, iodesc->dimlen, iodesc->maplen, iodesc->map,
                         comm);
}

/**
 * Write the decomposition map to a file.
 *
 * @param file the filename
 * @param ndims the number of dimensions
 * @param gdims an array of dimension ids
 * @param maplen the length of the map
 * @param map the map array
 * @param comm an MPI communicator.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_writemap(const char *file, int ndims, const int *gdims, PIO_Offset maplen,
                  PIO_Offset *map, MPI_Comm comm)
{
    int npes, myrank;
    PIO_Offset *nmaplen = NULL;
    MPI_Status status;
    int i;
    PIO_Offset *nmap;
    int mpierr; /* Return code for MPI calls. */

    LOG((1, "PIOc_writemap file = %s ndims = %d maplen = %d", file, ndims, maplen));

    if ((mpierr = MPI_Comm_size(comm, &npes)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    if ((mpierr = MPI_Comm_rank(comm, &myrank)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);
    LOG((2, "npes = %d myrank = %d", npes, myrank));

    /* Allocate memory for the nmaplen. */
    if (myrank == 0)
        if (!(nmaplen = malloc(npes * sizeof(PIO_Offset))))
            return pio_err(NULL, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    if ((mpierr = MPI_Gather(&maplen, 1, PIO_OFFSET, nmaplen, 1, PIO_OFFSET, 0, comm)))
        return check_mpi(NULL, mpierr, __FILE__, __LINE__);

    /* Only rank 0 writes the file. */
    if (myrank == 0)
    {
        FILE *fp;

        /* Open the file to write. */
        if (!(fp = fopen(file, "w")))
            return pio_err(NULL, NULL, PIO_EIO, __FILE__, __LINE__);

        /* Write the version and dimension info. */
        fprintf(fp,"version %d npes %d ndims %d \n", VERSNO, npes, ndims);
        for (i = 0; i < ndims; i++)
            fprintf(fp, "%d ", gdims[i]);
        fprintf(fp, "\n");

        /* Write the map. */
        fprintf(fp, "0 %ld\n", nmaplen[0]);
        for (i = 0; i < nmaplen[0]; i++)
            fprintf(fp, "%ld ", map[i]);
        fprintf(fp,"\n");

        for (i = 1; i < npes; i++)
        {
            LOG((2, "creating nmap for i = %d", i));
            nmap = (PIO_Offset *)malloc(nmaplen[i] * sizeof(PIO_Offset));

            if ((mpierr = MPI_Send(&i, 1, MPI_INT, i, npes + i, comm)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            if ((mpierr = MPI_Recv(nmap, nmaplen[i], PIO_OFFSET, i, i, comm, &status)))
                return check_mpi(NULL, mpierr, __FILE__, __LINE__);
            LOG((2,"MPI_Recv map complete"));

            fprintf(fp, "%d %ld\n", i, nmaplen[i]);
            for (int j = 0; j < nmaplen[i]; j++)
                fprintf(fp, "%ld ", nmap[j]);
            fprintf(fp, "\n");

            free(nmap);
        }
        /* Free memory for the nmaplen. */
        free(nmaplen);
        fprintf(fp, "\n");
        print_trace(fp);

        /* Close the file. */
        fclose(fp);
        LOG((2,"decomp file closed."));
    }
    else
    {
        LOG((2,"ready to MPI_Recv..."));
        if ((mpierr = MPI_Recv(&i, 1, MPI_INT, 0, npes+myrank, comm, &status)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        LOG((2,"MPI_Recv got %d", i));
        if ((mpierr = MPI_Send(map, maplen, PIO_OFFSET, 0, myrank, comm)))
            return check_mpi(NULL, mpierr, __FILE__, __LINE__);
        LOG((2,"MPI_Send map complete"));
    }

    return PIO_NOERR;
}

/**
 * Write the decomposition map to a file for F90.
 *
 * @param file the filename
 * @param ndims the number of dimensions
 * @param gdims an array of dimension ids
 * @param maplen the length of the map
 * @param map the map array
 * @param comm an MPI communicator.
 * @returns 0 for success, error code otherwise.
 */
int PIOc_writemap_from_f90(const char *file, int ndims, const int *gdims,
                           PIO_Offset maplen, const PIO_Offset *map, int f90_comm)
{
    return PIOc_writemap(file, ndims, gdims, maplen, (PIO_Offset *)map,
                         MPI_Comm_f2c(f90_comm));
}

/**
 * Open an existing file using PIO library. This is an internal
 * function. Depending on the value of the retry parameter, a failed
 * open operation will be handled differently. If retry is non-zero,
 * then a failed attempt to open a file with netCDF-4 (serial or
 * parallel), or parallel-netcdf will be followed by an attempt to
 * open the file as a serial classic netCDF file. This is an important
 * feature to some NCAR users. The functionality is exposed to the
 * user as PIOc_openfile() (which does the retry), and PIOc_open()
 * (which does not do the retry).
 *
 * Input parameters are read on comp task 0 and ignored elsewhere.
 *
 * @param iosysid: A defined pio system descriptor (input)
 * @param ncidp: A pio file descriptor (output)
 * @param iotype: A pio output format (input)
 * @param filename: The filename to open
 * @param mode: The netcdf mode for the open operation
 * @param retry: non-zero to automatically retry with netCDF serial
 * classic.
 *
 * @return 0 for success, error code otherwise.
 * @ingroup PIO_openfile
 */
int PIOc_openfile_retry(int iosysid, int *ncidp, int *iotype,
                        const char *filename, int mode, int retry)
{
    iosystem_desc_t *ios;  /** Pointer to io system information. */
    file_desc_t *file;     /** Pointer to file information. */
    int ierr = PIO_NOERR;  /** Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /** Return code from MPI function codes. */

    /* Get the IO system info from the iosysid. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* User must provide valid input for these parameters. */
    if (!ncidp || !iotype || !filename)
        return pio_err(ios, NULL, PIO_EINVAL, __FILE__, __LINE__);
    if (*iotype < PIO_IOTYPE_PNETCDF || *iotype > PIO_IOTYPE_NETCDF4P)
        return pio_err(ios, NULL, PIO_EINVAL, __FILE__, __LINE__);

    LOG((2, "PIOc_openfile_retry iosysid = %d iotype = %d filename = %s mode = %d retry = %d",
         iosysid, *iotype, filename, mode, retry));

    /* Allocate space for the file info. */
    if (!(file = calloc(sizeof(*file), 1)))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);

    /* Fill in some file values. */
    file->fh = -1;
    file->iotype = *iotype;
    file->iosystem = ios;
    file->mode = mode;

    for (int i = 0; i < PIO_MAX_VARS; i++)
    {
        file->varlist[i].record = -1;
        file->varlist[i].ndims = -1;
    }

    /* Set to true if this task should participate in IO (only true for
     * one task with netcdf serial files. */
    if (file->iotype == PIO_IOTYPE_NETCDF4P || file->iotype == PIO_IOTYPE_PNETCDF ||
        ios->io_rank == 0)
        file->do_io = 1;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        int msg = PIO_MSG_OPEN_FILE;
        size_t len = strlen(filename);

        if (!ios->ioproc)
        {
            /* Send the message to the message handler. */
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            /* Send the parameters of the function call. */
            if (!mpierr)
                mpierr = MPI_Bcast(&len, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast((void *)filename, len + 1, MPI_CHAR, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&file->iotype, 1, MPI_INT, ios->compmaster, ios->intercomm);
            if (!mpierr)
                mpierr = MPI_Bcast(&file->mode, 1, MPI_INT, ios->compmaster, ios->intercomm);
        }

        /* Handle MPI errors. */
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            return check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    if (ios->ioproc)
    {
        switch (file->iotype)
        {
#ifdef _NETCDF
#ifdef _NETCDF4

        case PIO_IOTYPE_NETCDF4P:
#ifdef _MPISERIAL
            ierr = nc_open(filename, file->mode, &file->fh);
#else
            file->mode = file->mode |  NC_MPIIO;
            ierr = nc_open_par(filename, file->mode, ios->io_comm, ios->info, &file->fh);
#endif
            break;

        case PIO_IOTYPE_NETCDF4C:
            file->mode = file->mode | NC_NETCDF4;
            // *** Note the INTENTIONAL FALLTHROUGH ***
#endif

        case PIO_IOTYPE_NETCDF:
            if (ios->io_rank == 0)
                ierr = nc_open(filename, file->mode, &file->fh);
            break;
#endif

#ifdef _PNETCDF
        case PIO_IOTYPE_PNETCDF:
            ierr = ncmpi_open(ios->io_comm, filename, file->mode, ios->info, &file->fh);

            // This should only be done with a file opened to append
            if (ierr == PIO_NOERR && (file->mode & PIO_WRITE))
            {
                if (ios->iomaster == MPI_ROOT)
                    LOG((2, "%d Setting IO buffer %ld", __LINE__, pio_buffer_size_limit));
                ierr = ncmpi_buffer_attach(file->fh, pio_buffer_size_limit);
            }
            LOG((2, "ncmpi_open(%s) : fd = %d", filename, file->fh));
            break;
#endif

        default:
            return pio_err(ios, file, PIO_EBADIOTYPE, __FILE__, __LINE__);
        }

        /* If the caller requested a retry, and we failed to open a
           file due to an incompatible type of NetCDF, try it once
           with just plain old basic NetCDF. */
        if (retry)
        {
#ifdef _NETCDF
            if ((ierr == NC_ENOTNC || ierr == NC_EINVAL) && (file->iotype != PIO_IOTYPE_NETCDF))
            {
                if (ios->iomaster == MPI_ROOT)
                    printf("PIO2 pio_file.c retry NETCDF\n");

                /* reset ierr on all tasks */
                ierr = PIO_NOERR;

                /* reset file markers for NETCDF on all tasks */
                file->iotype = PIO_IOTYPE_NETCDF;

                /* open netcdf file serially on main task */
                if (ios->io_rank == 0)
                    ierr = nc_open(filename, file->mode, &file->fh);
            }
#endif
        }
    }

    /* Broadcast and check the return code. */
    LOG((2, "Bcasting error code ierr = %d ios->ioroot = %d ios->my_comm = %d", ierr, ios->ioroot,
         ios->my_comm));
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    LOG((2, "Bcast error code ierr = %d", ierr));

    /* If there was an error, free allocated memory and deal with the error. */
    if (ierr)
    {
        free(file);
        return check_netcdf2(ios, NULL, ierr, __FILE__, __LINE__);
    }
    LOG((2, "error code Bcast complete ierr = %d ios->my_comm = %d", ierr, ios->my_comm));

    /* Broadcast results to all tasks. Ignore NULL parameters. */
    if ((mpierr = MPI_Bcast(&file->mode, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);

    /* Create the ncid that the user will see. This is necessary
     * because otherwise ncids will be reused if files are opened
     * on multiple iosystems. */
    file->pio_ncid = pio_next_ncid++;

    /* Return the PIO ncid to the user. */
    *ncidp = file->pio_ncid;

    /* Add this file to the list of currently open files. */
    pio_add_to_file_list(file);

    LOG((2, "Opened file %s file->pio_ncid = %d file->fh = %d ierr = %d",
         filename, file->pio_ncid, file->fh, ierr));

    return ierr;
}

/**
 * Internal function to provide inq_type function for pnetcdf.
 *
 * @param ncid ignored because pnetcdf does not have user-defined
 * types.
 * @param xtype type to learn about.
 * @param name pointer that gets name of type. Ignored if NULL.
 * @param sizep pointer that gets size of type. Ignored if NULL.
 * @returns 0 on success, error code otherwise.
 */
int pioc_pnetcdf_inq_type(int ncid, nc_type xtype, char *name,
                          PIO_Offset *sizep)
{
    int typelen;

    switch (xtype)
    {
    case NC_UBYTE:
    case NC_BYTE:
    case NC_CHAR:
        typelen = 1;
        break;
    case NC_SHORT:
    case NC_USHORT:
        typelen = 2;
        break;
    case NC_UINT:
    case NC_INT:
    case NC_FLOAT:
        typelen = 4;
        break;
    case NC_UINT64:
    case NC_INT64:
    case NC_DOUBLE:
        typelen = 8;
        break;
    default:
        return PIO_EBADTYPE;
    }

    /* If pointers were supplied, copy results. */
    if (sizep)
        *sizep = typelen;
    if (name)
        strcpy(name, "some type");

    return PIO_NOERR;
}

/**
 * This is an internal function that handles both PIOc_enddef and
 * PIOc_redef.
 *
 * @param ncid the ncid of the file to enddef or redef
 * @param is_enddef set to non-zero for enddef, 0 for redef.
 * @returns PIO_NOERR on success, error code on failure. */
int pioc_change_def(int ncid, int is_enddef)
{
    iosystem_desc_t *ios;  /* Pointer to io system information. */
    file_desc_t *file;     /* Pointer to file information. */
    int ierr = PIO_NOERR;  /* Return code from function calls. */
    int mpierr = MPI_SUCCESS, mpierr2;  /* Return code from MPI functions. */

    LOG((2, "pioc_change_def ncid = %d is_enddef = %d", ncid, is_enddef));

    /* Find the info about this file. When I check the return code
     * here, some tests fail. ???*/
    if ((ierr = pio_get_file(ncid, &file)))
        return ierr;
    /*return pio_err(NULL, NULL, ierr, __FILE__, __LINE__);*/
    ios = file->iosystem;

    /* If async is in use, and this is not an IO task, bcast the parameters. */
    if (ios->async_interface)
    {
        if (!ios->ioproc)
        {
            int msg = is_enddef ? PIO_MSG_ENDDEF : PIO_MSG_REDEF;
            if (ios->compmaster == MPI_ROOT)
                mpierr = MPI_Send(&msg, 1, MPI_INT, ios->ioroot, 1, ios->union_comm);

            if (!mpierr)
                mpierr = MPI_Bcast(&ncid, 1, MPI_INT, ios->compmaster, ios->intercomm);
            LOG((3, "pioc_change_def ncid = %d mpierr = %d", ncid, mpierr));
        }

        /* Handle MPI errors. */
        LOG((3, "pioc_change_def handling MPI errors"));
        if ((mpierr2 = MPI_Bcast(&mpierr, 1, MPI_INT, ios->comproot, ios->my_comm)))
            check_mpi(file, mpierr2, __FILE__, __LINE__);
        if (mpierr)
            return check_mpi(file, mpierr, __FILE__, __LINE__);
    }

    /* If this is an IO task, then call the netCDF function. */
    LOG((3, "pioc_change_def ios->ioproc = %d", ios->ioproc));
    if (ios->ioproc)
    {
        LOG((3, "pioc_change_def calling netcdf function file->fh = %d file->do_io = %d",
             file->fh, file->do_io));
#ifdef _PNETCDF
        if (file->iotype == PIO_IOTYPE_PNETCDF)
        {
            if (is_enddef)
                ierr = ncmpi_enddef(file->fh);
            else
                ierr = ncmpi_redef(file->fh);
        }
#endif /* _PNETCDF */
#ifdef _NETCDF
        if (file->iotype != PIO_IOTYPE_PNETCDF && file->do_io)
        {
            if (is_enddef)
            {
                LOG((3, "pioc_change_def calling nc_enddef file->fh = %d", file->fh));
                ierr = nc_enddef(file->fh);
            }
            else
                ierr = nc_redef(file->fh);
        }
#endif /* _NETCDF */
    }

    /* Broadcast and check the return code. */
    LOG((3, "pioc_change_def bcasting return code ierr = %d", ierr));
    if ((mpierr = MPI_Bcast(&ierr, 1, MPI_INT, ios->ioroot, ios->my_comm)))
        return check_mpi(file, mpierr, __FILE__, __LINE__);
    if (ierr)
        return check_netcdf(file, ierr, __FILE__, __LINE__);
    LOG((3, "pioc_change_def succeeded"));

    return ierr;
}

/**
 * Check whether an IO type is valid for the build.
 *
 * @param iotype the IO type to check
 * @returns 0 if valid, non-zero otherwise.
 */
int iotype_is_valid(int iotype)
{
    /* Assume it's not valid. */
    int ret = 0;

    /* All builds include netCDF. */
    if (iotype == PIO_IOTYPE_NETCDF)
        ret++;

    /* Some builds include netCDF-4. */
#ifdef _NETCDF4
    if (iotype == PIO_IOTYPE_NETCDF4C || iotype == PIO_IOTYPE_NETCDF4P)
        ret++;
#endif /* _NETCDF4 */

    /* Some builds include pnetcdf. */
    if (iotype == PIO_IOTYPE_PNETCDF)
        ret++;
#ifdef _PNETCDF
#endif /* _PNETCDF */

    return ret;
}
