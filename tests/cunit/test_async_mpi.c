/*
 * This program tests some MPI functionality that is used in PIO. This
 * runs on three processors, and does the same MPI commands that are
 * done when async mode is used, with 1 IO task, and two computation
 * compoments, each of one task.
 *
 * Note that this test does not contain includes to pio headers, it is
 * pure MPI code.
 *
 * @author Ed Hartnett
 * @date 8/28/16
 */
#include <config.h>
#include <stdio.h>
#include <mpi.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 3

/* The name of this test. */
#define TEST_NAME "test_async_mpi"

/* Number of processors that will do IO. */
#define NUM_IO_PROCS 1

/* Number of computational components to create. */
#define COMPONENT_COUNT 2

#define ERR_AWFUL 1111
#define ERR_WRONG 1112

/* Handle MPI errors. This should only be used with MPI library
 * function calls. */
#define MPIERR(e) do {                                                  \
        MPI_Error_string(e, err_buffer, &resultlen);                    \
        fprintf(stderr, "MPI error, line %d, file %s: %s\n", __LINE__, __FILE__, err_buffer); \
        MPI_Finalize();                                                 \
        return ERR_AWFUL;                                               \
    } while (0)

/* Handle non-MPI errors by finalizing the MPI library and exiting
 * with an exit code. */
#define ERR(e) do {                                                     \
        fprintf(stderr, "%d Error %d in %s, line %d\n", my_rank, e, __FILE__, __LINE__); \
        MPI_Finalize();                                                 \
        return e;                                                       \
    } while (0)

/* Global err buffer for MPI. When there is an MPI error, this buffer
 * is used to store the error message that is associated with the MPI
 * error. */
char err_buffer[MPI_MAX_ERROR_STRING];

/* This is the length of the most recent MPI error message, stored
 * int the global error string. */
int resultlen;

/* Put together a communicator with the correct number of tasks for
 * this test (3).
 */
int get_test_comm(int my_rank, int ntasks, int min_ntasks, int max_ntasks, MPI_Comm *comm)
{
    int ret;
    
    /* Check that a valid number of processors was specified. */
    if (ntasks < min_ntasks)
    {
        fprintf(stderr, "ERROR: Number of processors must be at least %d for this test!\n",
                min_ntasks);
        return ERR_AWFUL;
    }
    else if (ntasks > max_ntasks)
    {
        /* If more tasks are available than we need for this test,
         * create a communicator with exactly the number of tasks we
         * need. */
        int color, key;
        if (my_rank < max_ntasks)
        {
            color = 0;
            key = my_rank;
        }
        else
        {
            color = 1;
            key = my_rank - max_ntasks;
        }
        if ((ret = MPI_Comm_split(MPI_COMM_WORLD, color, key, comm)))
            MPIERR(ret);
    }
    else
    {
        if ((ret = MPI_Comm_dup(MPI_COMM_WORLD, comm)))
            MPIERR(ret);
    }
    return 0;
}

/* Run simple async test. */
int main(int argc, char **argv)
{
    int my_rank = 0;    /* Zero-based rank of processor. */
    int ntasks;         /* Number of processors involved in current execution. */
    MPI_Comm test_comm; /* Communicator for tasks running tests. */
    int ret;            /* Return code from function calls. */

    /* Initialize MPI. */
    if ((ret = MPI_Init(&argc, &argv)))
        MPIERR(ret);

    /* Learn my rank and the total number of processors. */
    if ((ret = MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)))
        MPIERR(ret);
    if ((ret = MPI_Comm_size(MPI_COMM_WORLD, &ntasks)))
        MPIERR(ret);

    /* Get test_comm. */
    if ((ret = get_test_comm(my_rank, ntasks, TARGET_NTASKS, TARGET_NTASKS, &test_comm)))
        ERR(ret);

    /* Ignore all but 3 tasks. */
    if (my_rank < TARGET_NTASKS)
    {
        /* Create group for world. */
        MPI_Group world_group;
        if ((ret = MPI_Comm_group(test_comm, &world_group)))
            MPIERR(ret);

        MPI_Group io_group;
        int my_io_proc_list[1] = {0}; /* List of processors in IO component. */        
        int num_io_procs = 1;
        int num_procs_per_comp[COMPONENT_COUNT] = {1, 1};
        
        if ((ret = MPI_Group_incl(world_group, num_io_procs, my_io_proc_list, &io_group)))
            MPIERR(ret);
        /* printf("my_rank %d created io_group = %d\n", my_rank, io_group); */

        /* There is one shared IO comm. Create it. */
        MPI_Comm io_comm;
        if ((ret = MPI_Comm_create(test_comm, io_group, &io_comm)))
            MPIERR(ret);
        /* printf("my_rank %d created io comm io_comm = %d\n", my_rank, io_comm); */

        /* Set in_io true for rank 0 of test_comm/world. */
        int in_io = my_rank ? 0 : 1;

        /* Rank of current process in IO communicator. */
        int io_rank = -1;

        /* Set to MPI_ROOT on master process, MPI_PROC_NULL on other
         * processes. */
        /* int iomaster; */
        
        /* For processes in the IO component, get their rank within the IO
         * communicator. */
        if (in_io)
        {
            if ((ret = MPI_Comm_rank(io_comm, &io_rank)))
                MPIERR(ret);
            /* iomaster = !io_rank ? MPI_ROOT : MPI_PROC_NULL; */
            /* printf("my_rank %d intracomm created for io_comm = %d io_rank = %d IO %s\n", */
            /*        my_rank, io_comm, io_rank, iomaster == MPI_ROOT ? "MASTER" : "SERVANT"); */
        }

        /* We will create a group for each computational component. */
        MPI_Group group[COMPONENT_COUNT];

        /* We will also create a group for each component and the IO
         * component processes (i.e. a union of computation and IO
         * processes. */
        MPI_Group union_group[COMPONENT_COUNT];

        int my_proc_list[COMPONENT_COUNT][1] = {{1}, {2}};   /* Array of arrays of procs for comp components. */
        
        /* For each computation component. */
        for (int cmp = 0; cmp < COMPONENT_COUNT; cmp++)
        {
            /* printf("my_rank %d processing component %d\n", my_rank, cmp); */

            /* Create a group for this component. */
            if ((ret = MPI_Group_incl(world_group, 1, my_proc_list[cmp], &group[cmp])))
                MPIERR(ret);
            /* printf("my_rank %d created component MPI group - group[%d] = %d\n", my_rank, cmp, group[cmp]); */

            /* How many processors in the union comm? */
            int nprocs_union = num_io_procs + num_procs_per_comp[cmp];

            /* This will hold proc numbers from both computation and IO
             * components. */
            int proc_list_union[nprocs_union];

            /* Add proc numbers from IO. */
            proc_list_union[0] = 0;

            /* Add proc numbers from computation component. */
            for (int p = 0; p < num_procs_per_comp[cmp]; p++)
                proc_list_union[p + num_io_procs] = my_proc_list[cmp][p];

            /* Is this process in this computation component? */
            int in_cmp = 0;
            int pidx;
            for (pidx = 0; pidx < num_procs_per_comp[cmp]; pidx++)
                if (my_rank == my_proc_list[cmp][pidx])
                    break;
            in_cmp = (pidx == num_procs_per_comp[cmp]) ? 0 : 1;
            /* printf("my_rank %d pidx = %d num_procs_per_comp[%d] = %d in_cmp = %d\n", */

            /* Create the union group. */
            if ((ret = MPI_Group_incl(world_group, nprocs_union, proc_list_union, &union_group[cmp])))
                MPIERR(ret);
            /* printf("my_rank %d created union MPI_group - union_group[%d] = %d with %d procs\n", */
            /*        my_rank, cmp, union_group[cmp], nprocs_union); */

            /* Create an intracomm for this component. Only processes in
             * the component need to participate in the intracomm create
             * call. */
            MPI_Comm comp_comm;
            if ((ret = MPI_Comm_create(test_comm, group[cmp], &comp_comm)))
                MPIERR(ret);
            
            if (in_cmp)
            {
                /* Get the rank in this comp comm. */
                int comp_rank;
                if ((ret = MPI_Comm_rank(comp_comm, &comp_rank)))
                    MPIERR(ret);
                /* printf("my_rank %d intracomm created for cmp = %d comp_comm = %d comp_rank = %d\n", */
                /*        my_rank, cmp, comp_comm, comp_rank); */
            }

            /* If this is the IO component, make a copy of the IO comm for
             * each computational component. */
            MPI_Comm io_comm2;
            if (in_io)
            {
                if ((ret = MPI_Comm_dup(io_comm, &io_comm2)))
                    MPIERR(ret);
                /* printf("my_rank %d dup of io_comm = %d io_rank = %d\n", my_rank, io_comm, io_rank); */
            }

            /* All the processes in this component, and the IO component,
             * are part of the union_comm. */
            MPI_Comm union_comm;
            int union_rank;
            MPI_Comm intercomm;
            
            /* Create a group for the union of the IO component
             * and one of the computation components. */
            if ((ret = MPI_Comm_create(test_comm, union_group[cmp], &union_comm)))
                MPIERR(ret);
            /* printf("my_rank %d created union comm for cmp %d union_comm %d\n", */
            /*        my_rank, cmp, union_comm); */

            if (in_io || in_cmp)
            {
                if ((ret = MPI_Comm_rank(union_comm, &union_rank)))
                    MPIERR(ret);
                /* printf("my_rank %d union_rank %d", my_rank, union_rank); */
                
                if (in_io)
                {
                    /* Create the intercomm from IO to computation component. */
                    /* printf("my_rank %d about to create intercomm for IO component to cmp = %d " */
                    /*        "io_comm = %d\n", my_rank, cmp, io_comm); */
                    if ((ret = MPI_Intercomm_create(io_comm, 0, union_comm,
                                                    1, cmp, &intercomm)))
                        MPIERR(ret);
                }
                else if (in_cmp)
                {
                    /* Create the intercomm from computation component to IO component. */
                    /* printf("my_rank %d about to create intercomm for cmp = %d comp_comm = %d", */
                    /*        my_rank, cmp, comp_comm); */
                    if ((ret = MPI_Intercomm_create(comp_comm, 0, union_comm,
                                                    0, cmp, &intercomm)))
                        MPIERR(ret);
                }
                /* printf("my_rank %d intercomm created for cmp = %d\n", my_rank, cmp); */
            } /* in_io || in_cmp */
        } /* next computation component. */
    }    

    /* Finalize MPI. */
    MPI_Finalize();

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
