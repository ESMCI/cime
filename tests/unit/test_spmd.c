/*
 * This program tests MPI_Alltoallw by having processor i send different
 * amounts of data to each processor.
 * The first test sends i items to processor i from all processors.
 *
 * Jim Edwards
 * Ed Hartnett, 11/23/16
 */
#include <pio.h>
#include <pio_tests.h>
#include <pio_internal.h>
#include <sys/time.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The name of this test. */
#define TEST_NAME "test_spmd"

#define min(a,b)                                \
    ({ __typeof__ (a) _a = (a);                 \
        __typeof__ (b) _b = (b);                \
        _a < _b ? _a : _b; })

#define TEST_MAX_GATHER_BLOCK_SIZE 32

int old_main(int argc, char **argv)
{
    MPI_Comm comm;
    int *sbuf, *rbuf;
    int rank, size;
    int *sendcounts, *recvcounts, *rdispls, *sdispls;
    int i, j, *p, err;
    MPI_Datatype *sendtypes, *recvtypes;
    struct timeval t1, t2;
    int msg_cnt;

/*     MPI_Init( &argc, &argv ); */
/*     err = 0; */
/*     comm = MPI_COMM_WORLD; */
/*     /\* Create the buffer *\/ */
/*     MPI_Comm_size( comm, &size ); */
/*     MPI_Comm_rank( comm, &rank ); */
/*     sbuf = (int *)malloc( size * size * sizeof(int) ); */
/*     rbuf = (int *)malloc( size * size * sizeof(int) ); */
/*     if (!sbuf || !rbuf) { */
/*         fprintf( stderr, "Could not allocated buffers!\n" ); */
/*         fflush(stderr); */
/*         MPI_Abort( comm, 1 ); */
/*     } */
/*     /\* Test pio_fc_gather *\/ */

/*     msg_cnt = 0; */
/*     while(msg_cnt <= TEST_MAX_GATHER_BLOCK_SIZE) */
/*     { */
/*         /\* Load up the buffers *\/ */
/*         for (i = 0; i<size*size; i++) { */
/*             sbuf[i] = i + 100*rank; */
/*             rbuf[i] = -i; */
/*         } */

/*         MPI_Barrier(comm); */
/*         if (rank==0) printf("Start gather test %d\n",msg_cnt); */
/*         if (rank == 0) gettimeofday(&t1, NULL); */

/*         err = pio_fc_gather( sbuf, size, MPI_INT, rbuf, size, MPI_INT, 0, comm, msg_cnt); */


/*         if (rank == 0){ */
/*             gettimeofday(&t2, NULL); */
/*             printf("time = %f\n",t2.tv_sec - t1.tv_sec + 1.e-6*( t2.tv_usec - t1.tv_usec)); */
/*         } */
/*         if (rank==0){ */
/*             for (j=0;j<size;j++){ */
/*                 for (i = 0;i<size;i++){ */
/*                     if (rbuf[i + j*size] != i + 100*j){ */
/*                         printf("got %d expected %d\n",rbuf[i+j*size] , i+100*j); */
/*                     } */
/*                 } */
/*             } */
/*         } */

/*         MPI_Barrier(comm); */


/*         if (msg_cnt==0) */
/*             msg_cnt=1; */
/*         else */
/*             msg_cnt*=2; */
/*     } */

/*     /\* Test pio_swapm Create and load the arguments to alltoallv *\/ */
/*     sendcounts = (int *)malloc( size * sizeof(int) ); */
/*     recvcounts = (int *)malloc( size * sizeof(int) ); */
/*     rdispls = (int *)malloc( size * sizeof(int) ); */
/*     sdispls = (int *)malloc( size * sizeof(int) ); */
/*     sendtypes = (MPI_Datatype *)malloc( size * sizeof(MPI_Datatype) ); */
/*     recvtypes = (MPI_Datatype *)malloc( size * sizeof(MPI_Datatype) ); */
/*     if (!sendcounts || !recvcounts || !rdispls || !sdispls || !sendtypes || !recvtypes) { */
/*         fprintf( stderr, "Could not allocate arg items!\n" ); */
/*         fflush(stderr); */
/*         MPI_Abort( comm, 1 ); */
/*     } */

/*     for (i = 0; i<size; i++) { */
/*         sendcounts[i] = i + 1; */
/*         recvcounts[i] = rank +1; */
/*         rdispls[i] = i * (rank+1) * sizeof(int) ; */
/*         sdispls[i] = (((i+1) * (i))/2) * sizeof(int) ; */
/*         sendtypes[i] = recvtypes[i] = MPI_INT; */
/*     } */

/*     //    for (int msg_cnt=4; msg_cnt<size; msg_cnt*=2){ */
/*     //   if (rank==0) printf("message count %d\n",msg_cnt); */
/*     msg_cnt = 0; */
/*     for (int itest=0;itest<5; itest++){ */
/*         bool hs=false; */
/*         bool isend=false; */
/*         /\* Load up the buffers *\/ */
/*         for (i = 0; i<size*size; i++) { */
/*             sbuf[i] = i + 100*rank; */
/*             rbuf[i] = -i; */
/*         } */
/*         MPI_Barrier(comm); */

/*         if (rank==0) printf("Start itest %d\n",itest); */
/*         if (rank == 0) gettimeofday(&t1, NULL); */

/*         if (itest==0){ */
/*             err = pio_swapm( size, rank, sbuf,  sendcounts, sdispls, sendtypes, */
/*                              rbuf,  recvcounts, rdispls, recvtypes, comm, hs, isend, 0); */
/*         }else if (itest==1){ */
/*             hs = true; */
/*             isend = true; */
/*             err = pio_swapm( size, rank, sbuf,  sendcounts, sdispls, sendtypes, */
/*                              rbuf,  recvcounts, rdispls, recvtypes, comm, hs, isend, msg_cnt); */
/*         }else if (itest==2){ */
/*             hs = false; */
/*             isend = true; */
/*             err = pio_swapm( size, rank, sbuf, sendcounts, sdispls, sendtypes, */
/*                              rbuf, recvcounts, rdispls, recvtypes, comm, hs, isend, msg_cnt); */

/*         }else if (itest==3){ */
/*             hs = false; */
/*             isend = false; */
/*             err = pio_swapm( size, rank, sbuf, sendcounts, sdispls, sendtypes, */
/*                              rbuf, recvcounts, rdispls, recvtypes, comm, hs, isend, msg_cnt); */

/*         }else if (itest==4){ */
/*             hs = true; */
/*             isend = false; */
/*             err = pio_swapm( size, rank, sbuf,  sendcounts, sdispls, sendtypes, */
/*                              rbuf,  recvcounts, rdispls, recvtypes, comm, hs, isend, msg_cnt); */

/*         } */

/*         if (rank == 0){ */
/*             gettimeofday(&t2, NULL); */
/*             printf("itest = %d time = %f\n",itest,t2.tv_sec - t1.tv_sec + 1.e-6*( t2.tv_usec - t1.tv_usec)); */
/*         } */
/*         /\* */
/*           printf("scnt: %d %d %d %d\n",sendcounts[0],sendcounts[1],sendcounts[2],sendcounts[3]); */
/*           printf("sdispls: %d %d %d %d\n",sdispls[0],sdispls[1],sdispls[2],sdispls[3]); */
/*           printf("rcnt: %d %d %d %d\n",recvcounts[0],recvcounts[1],recvcounts[2],recvcounts[3]); */
/*           printf("rdispls: %d %d %d %d\n",rdispls[0],rdispls[1],rdispls[2],rdispls[3]); */

/*           printf("send: "); */
/*           for (i = 0;i<size*size;i++) */
/*           printf("%d ",sbuf[i]); */
/*           printf("\n"); */
/*           printf("recv: "); */
/*           for (i = 0;i<size*size;i++) */
/*           printf("%d ",rbuf[i]); */
/*           printf("\n"); */
/*         *\/ */
/*         MPI_Barrier(comm); */
/*         /\* Check rbuf *\/ */
/*         for (i = 0; i < size; i++) */
/* 	{ */
/*             p = rbuf + rdispls[i] / sizeof(int); */
/*             for (j=0; j < rank + 1; j++) */
/* 	    { */
/*                 if (p[j] != i * 100 + (rank* (rank + 1)) / 2 + j) */
/* 		{ */
/*                     fprintf( stderr, "[%d] got %d expected %d for %d %dth in itest=%d\n", */
/*                              rank, p[j],(i*100 + (rank*(rank+1))/2+j), i, j, itest); */
/*                     fflush(stderr); */
/*                     err++; */
/*                 } */
/*             } */
/*         } */
/*     } */

/*     //    } */

/*     /\* Free memory. *\/ */
/*     free(sendtypes); */
/*     free(recvtypes); */
/*     free(sdispls); */
/*     free(rdispls); */
/*     free(recvcounts); */
/*     free(sendcounts); */
/*     free(rbuf); */
/*     free(sbuf); */
/*     MPI_Finalize(); */

/* #if PIO_ENABLE_LOGGING */
/*     fclose(LOG_FILE); */
/* #endif /\* PIO_ENABLE_LOGGING *\/ */
    return 0;
}

/* The actual tests are here. */
int run_spmd_tests(MPI_Comm test_comm)
{
    int my_rank; /* 0-based rank in test_comm. */
    int ntasks;  /* Number of tasks in test_comm. */
    int num_elem; /* Number of elements in buffers. */
    int *sbuf;    /* The send buffer. */
    int *rbuf;    /* The receive buffer. */
    struct timeval t1, t2; /* For timing. */    
    int mpiret;   /* Return value from MPI calls. */
    int ret;      /* Return value. */

    /* Learn rank and size. */
    if ((mpiret = MPI_Comm_size(test_comm, &ntasks)))
        MPIERR(mpiret);
    if ((mpiret = MPI_Comm_rank(test_comm, &my_rank)))
        MPIERR(mpiret);

    /* Determine size of buffers. */
    num_elem = ntasks * ntasks;
        
    /* Allocatte the buffers. */
    if (!(sbuf = malloc(num_elem * sizeof(int))))
        return PIO_ENOMEM;
    if (!(rbuf = malloc(num_elem * sizeof(int))))
        return PIO_ENOMEM;

    /* Test pio_fc_gather. In fact it does not work for msg_cnt > 0. */
    /* for (int msg_cnt = 0; msg_cnt <= TEST_MAX_GATHER_BLOCK_SIZE; */
    /*      msg_cnt = msg_cnt ? msg_cnt * 2 : 1) */
    int msg_cnt = 0;
    {
        /* Load up the buffers */
        for (int i = 0; i < num_elem; i++)
        {
            sbuf[i] = i + 100 * my_rank;
            rbuf[i] = -i;
        }

        printf("%d Testing pio_fc_gather with msg_cnt = %d\n", my_rank, msg_cnt);

        /* Start timeer. */
        if (!my_rank)
            gettimeofday(&t1, NULL);

        /* Run the gather function. */
        if ((ret = pio_fc_gather(sbuf, ntasks, MPI_INT, rbuf, ntasks, MPI_INT, 0, test_comm,
                                 msg_cnt)))
            return ret;

        /* Only check results on task 0. */
        if (!my_rank)
        {
            /* Stop timer. */
            gettimeofday(&t2, NULL);
            printf("Time in microseconds: %ld microseconds\n",
                   ((t2.tv_sec - t1.tv_sec) * 1000000L + t2.tv_usec) - t1.tv_usec);

            /* Check results. */
            for (int j = 0; j < ntasks; j++)
                for (int i = 0; i < ntasks; i++)
                    if (rbuf[i + j * ntasks] != i + 100 * j)
                        printf("got %d expected %d\n", rbuf[i + j * ntasks], i + 100 * j);
        }
        

        /* Wait for all test tasks. */
        MPI_Barrier(test_comm);
    }

    /* Free resourses. */
    free(sbuf);
    free(rbuf);
    
    return 0;
}

/* Run Tests for pio_spmd.c functions. */
int main(int argc, char **argv)
{
    int my_rank; /* Zero-based rank of processor. */
    int ntasks;  /* Number of processors involved in current execution. */
    int ret;     /* Return code. */
    MPI_Comm test_comm; /* A communicator for this test. */

    /* Initialize test. */
    if ((ret = pio_test_init(argc, argv, &my_rank, &ntasks, TARGET_NTASKS,
			     &test_comm)))
        ERR(ERR_INIT);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
	printf("%d running test code\n", my_rank);
        if ((ret = run_spmd_tests(test_comm)))
            return ret;

    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize()))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}

