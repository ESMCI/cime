/**
 * @file
 * Macros to handle errors in tests or libray code.
 * @author Ed Hartnett
 * @date 2019
 *
 * @see https://github.com/NCAR/ParallelIO
 */

#ifndef __PIO_ERROR__
#define __PIO_ERROR__

#include <config.h>
#include <pio.h>

/** Handle non-MPI errors by finalizing the MPI library and goto
 * exit. Finalize and goto exit. */
#define BAIL(e) do {                                                    \
        fprintf(stderr, "%d Error %d in %s, line %d\n", my_rank, e, __FILE__, __LINE__); \
        goto exit;                                                      \
    } while (0)

/** Handle non-MPI errors by finalizing the MPI library and exiting
 * with an exit code. Finalize and return. */
#define ERR(e) do {                                                     \
        fprintf(stderr, "%d Error %d in %s, line %d\n", my_rank, e, __FILE__, __LINE__); \
        MPI_Finalize();                                                 \
        return e;                                                       \
    } while (0)

#endif /* __PIO_ERROR__ */
