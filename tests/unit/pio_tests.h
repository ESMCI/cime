/**
 * @file
 * Include file for tests for the Parallel IO library.
 * @author Ed Hartnett
 * @date 9/13/2016
 */

#ifndef _PIO_TESTS_H
#define _PIO_TESTS_H

/* Include this for the sleep function. */
#include <unistd.h>

/* Timing header may need to be included. */
#ifdef TIMING
#include <gptl.h>
#endif

/** The number of possible output netCDF output flavors available to
 * the ParallelIO library. */
#define NUM_FLAVORS 4

/* Number of sample files constructed for these tests. */
#define NUM_SAMPLES 3

/** Error code for when things go wrong. */
#define ERR_CHECK 1109
#define ERR_INIT 1110
#define ERR_AWFUL 1111
#define ERR_WRONG 2222

/** Handle MPI errors. This should only be used with MPI library
 * function calls. */
#define MPIERR(e) do {                                                  \
	MPI_Error_string(e, err_buffer, &resultlen);			\
	fprintf(stderr, "MPI error, line %d, file %s: %s\n", __LINE__, __FILE__, err_buffer); \
	MPI_Finalize();							\
	return ERR_AWFUL;							\
    } while (0)

/** Handle non-MPI errors by finalizing the MPI library and exiting
 * with an exit code. */
#define ERR(e) do {				\
        fprintf(stderr, "%d Error %d in %s, line %d\n", my_rank, e, __FILE__, __LINE__); \
	MPI_Finalize();				\
	return e;				\
    } while (0)

/** Global err buffer for MPI. When there is an MPI error, this buffer
 * is used to store the error message that is associated with the MPI
 * error. */
char err_buffer[MPI_MAX_ERROR_STRING];

/** This is the length of the most recent MPI error message, stored
 * int the global error string. */
int resultlen;

/* Function prototypes. */
char *flavor_name(int flavor);
int pio_test_init(int argc, char **argv, int *my_rank, int *ntasks, int target_ntasks);
int create_nc_sample(int sample, int iosysid, int format, char *filename, int my_rank);
int check_nc_sample(int sample, int iosysid, int format, char *filename, int my_rank);
int create_nc_sample_0(int iosysid, int format, char *filename, int my_rank);
int check_nc_sample_0(int iosysid, int format, char *filename, int my_rank);
int create_nc_sample_1(int iosysid, int format, char *filename, int my_rank);
int check_nc_sample_1(int iosysid, int format, char *filename, int my_rank);
int create_nc_sample_2(int iosysid, int format, char *filename, int my_rank);
int check_nc_sample_2(int iosysid, int format, char *filename, int my_rank);
int pio_test_finalize();

#endif /* _PIO_TESTS_H */
