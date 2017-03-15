/*
 * This program tests some internal functions in the library related
 * to the box and subset rearranger, and the transfer of data betweeen
 * IO and computation tasks.
 *
 * Ed Hartnett, 3/9/17
 */
#include <pio.h>
#include <pio_tests.h>
#include <pio_internal.h>

/* The number of tasks this test should run on. */
#define TARGET_NTASKS 4

/* The minimum number of tasks this test should run on. */
#define MIN_NTASKS 1

/* The name of this test. */
#define TEST_NAME "test_rearr"

/* Test some of the rearranger utility functions. */
int test_rearranger_opts1()
{
    rearr_comm_fc_opt_t *ro1;
    rearr_comm_fc_opt_t *ro2;
    rearr_comm_fc_opt_t *ro3;

    if (!(ro1 = calloc(1, sizeof(rearr_comm_fc_opt_t))))
        return ERR_AWFUL;
    if (!(ro2 = calloc(1, sizeof(rearr_comm_fc_opt_t))))
        return ERR_AWFUL;
    if (!(ro3 = calloc(1, sizeof(rearr_comm_fc_opt_t))))
        return ERR_AWFUL;

    /* This should not work. */
    if (PIOc_set_rearr_opts(42, 1, 1, 0, 0, 0, 0, 0, 0) != PIO_EBADID)
        return ERR_WRONG;

    /* ro1 and ro2 are the same. */
    if (!cmp_rearr_comm_fc_opts(ro1, ro2))
        return ERR_WRONG;

    /* Make ro3 different. */
    ro3->enable_hs = 1;
    if (cmp_rearr_comm_fc_opts(ro1, ro3))
        return ERR_WRONG;
    ro3->enable_hs = 0;
    ro3->enable_isend = 1;
    if (cmp_rearr_comm_fc_opts(ro1, ro3))
        return ERR_WRONG;
    ro3->enable_isend = 0;
    ro3->max_pend_req = 1;
    if (cmp_rearr_comm_fc_opts(ro1, ro3))
        return ERR_WRONG;

    /* Free resourses. */
    free(ro1);
    free(ro2);
    free(ro3);
    
    return 0;
}

/* Test some of the rearranger utility functions. */
int test_cmp_rearr_opts()
{
    rearr_opt_t ro1;
    rearr_opt_t ro2;

    ro1.comm_type = PIO_REARR_COMM_P2P;
    ro2.comm_type = PIO_REARR_COMM_P2P;

    ro1.fcd = PIO_REARR_COMM_FC_2D_ENABLE;
    ro2.fcd = PIO_REARR_COMM_FC_2D_ENABLE;

    ro1.comm_fc_opts_comp2io.enable_hs = 0;
    ro1.comm_fc_opts_comp2io.enable_isend = 0;
    ro1.comm_fc_opts_comp2io.max_pend_req = 0;

    ro1.comm_fc_opts_io2comp.enable_hs = 0;
    ro1.comm_fc_opts_io2comp.enable_isend = 0;
    ro1.comm_fc_opts_io2comp.max_pend_req = 0;
    
    ro2.comm_fc_opts_comp2io.enable_hs = 0;
    ro2.comm_fc_opts_comp2io.enable_isend = 0;
    ro2.comm_fc_opts_comp2io.max_pend_req = 0;

    ro2.comm_fc_opts_io2comp.enable_hs = 0;
    ro2.comm_fc_opts_io2comp.enable_isend = 0;
    ro2.comm_fc_opts_io2comp.max_pend_req = 0;

    /* They are equal. */
    if (!cmp_rearr_opts(&ro1, &ro2))
        return ERR_WRONG;

    /* Change something. */
    ro1.comm_type = PIO_REARR_COMM_COLL;

    /* They are not equal. */
    if (cmp_rearr_opts(&ro1, &ro2))
        return ERR_WRONG;

    /* Change something. */
    ro2.comm_type = PIO_REARR_COMM_COLL;
    ro1.fcd = PIO_REARR_COMM_FC_2D_DISABLE;
    
    /* They are not equal. */
    if (cmp_rearr_opts(&ro1, &ro2))
        return ERR_WRONG;

    ro2.fcd = PIO_REARR_COMM_FC_2D_DISABLE;

    /* They are equal again. */
    if (!cmp_rearr_opts(&ro1, &ro2))
        return ERR_WRONG;
    
    return 0;
}

/* Test some of the rearranger utility functions. */
int test_rearranger_opts3()
{
    rearr_opt_t ro;

    /* I'm not sure what the point of this function is... */
    check_and_reset_rearr_opts(&ro);
    
    return 0;
}

/* Test the compare_offsets() function. */
int test_compare_offsets()
{
    mapsort m1, m2, m3;

    m1.rfrom = 0;
    m1.soffset = 0;
    m1.iomap = 0;
    m2.rfrom = 0;
    m2.soffset = 0;
    m2.iomap = 0;
    m3.rfrom = 0;
    m3.soffset = 0;
    m3.iomap = 1;

    /* Return 0 if either or both parameters are null. */
    if (compare_offsets(NULL, &m2))
        return ERR_WRONG;
    if (compare_offsets(&m1, NULL))
        return ERR_WRONG;
    if (compare_offsets(NULL, NULL))
        return ERR_WRONG;

    /* m1 and m2 are the same. */
    if (compare_offsets(&m1, &m2))
        return ERR_WRONG;

    /* m1 and m3 are different. */
    if (compare_offsets(&m1, &m3) != -1)
        return ERR_WRONG;
    return 0;
}

/* Test the ceil2() and pair() functions. */
int test_ceil2_pair()
{
    /* Test the ceil2() function. */
    if (ceil2(1) != 1)
        return ERR_WRONG;
    if (ceil2(-100) != 1)
        return ERR_WRONG;
    if (ceil2(2) != 2)
        return ERR_WRONG;
    if (ceil2(3) != 4)
        return ERR_WRONG;
    if (ceil2(16) != 16)
        return ERR_WRONG;
    if (ceil2(17) != 32)
        return ERR_WRONG;

    /* Test the pair() function. */
    if (pair(4, 0, 0) != 1)
        return ERR_WRONG;
    if (pair(4, 2, 2) != 1)
        return ERR_WRONG;
    
    return 0;
}

/* Test init_rearr_opts(). */
int test_init_rearr_opts()
{
    iosystem_desc_t ios;

    init_rearr_opts(&ios);

    if (ios.rearr_opts.comm_type != PIO_REARR_COMM_COLL || ios.rearr_opts.fcd != PIO_REARR_COMM_FC_2D_DISABLE ||
        ios.rearr_opts.comm_fc_opts_comp2io.enable_hs || ios.rearr_opts.comm_fc_opts_comp2io.enable_isend ||
        ios.rearr_opts.comm_fc_opts_comp2io.max_pend_req ||
        ios.rearr_opts.comm_fc_opts_io2comp.enable_hs || ios.rearr_opts.comm_fc_opts_io2comp.enable_isend ||
        ios.rearr_opts.comm_fc_opts_io2comp.max_pend_req)
        return ERR_WRONG;
    
    return 0;
}

/* Tests that didn't fit in anywhere else. */
int test_misc()
{
    /* This should not work. */
    if (PIOc_set_rearr_opts(TEST_VAL_42, 0, 0, false, false, 0, false,
                            false, 0) != PIO_EBADID)
        return ERR_WRONG;
    
    return 0;
}

/* Test the create_mpi_datatypes() function. 
 * @returns 0 for success, error code otherwise.*/
int test_create_mpi_datatypes()
{
    MPI_Datatype basetype = MPI_INT;
    int msgcnt = 1;
    PIO_Offset mindex[4] = {0, 0, 0, 0};
    int mcount[4] = {1, 1, 1, 1};
    int *mfrom = NULL;
    MPI_Datatype mtype;
    int mpierr;
    int ret;

    /* Create an MPI data type. */
    if ((ret = create_mpi_datatypes(basetype, msgcnt, mindex, mcount, mfrom, &mtype)))
        return ret;

    /* Free the type. */
    if ((mpierr = MPI_Type_free(&mtype)))
        return ERR_WRONG;

    /* Change our parameters. */
    msgcnt = 4;
    MPI_Datatype mtype2[4];
    
    /* Create 4 MPI data types. */
    if ((ret = create_mpi_datatypes(basetype, msgcnt, mindex, mcount, mfrom, mtype2)))
        return ret;

    /* Free them. */
    for (int t = 0; t < 4; t++)
        if ((mpierr = MPI_Type_free(&mtype2[t])))
            return ERR_WRONG;
    
    return 0;
}

/* Test the idx_to_dim_list() function. */
int test_idx_to_dim_list()
{
    int ndims = 1;
    int gdims[1] = {1};
    PIO_Offset idx = 0;
    PIO_Offset dim_list[1];

    /* This simplest case. */
    idx_to_dim_list(ndims, gdims, idx, dim_list);

    if (dim_list[0] != 0)
        return ERR_WRONG;

    /* The case given in the function docs. */
    int ndims2 = 2;
    int gdims2[2] = {3, 2};
    PIO_Offset idx2 = 4;
    PIO_Offset dim_list2[2];

    /* According to function docs, we should get 1,1 */
    idx_to_dim_list(ndims2, gdims2, idx2, dim_list2);
    printf("dim_list2[0] = %lld\n", dim_list2[0]);
    printf("dim_list2[1] = %lld\n", dim_list2[1]);

    /* This is not the result that the documentation promised! */
    if (dim_list2[0] != 2 || dim_list2[1] != 0)
        return ERR_WRONG;
    
    return 0;
}

/* Test the coord_to_lindex() function. */
int test_coord_to_lindex()
{
    int ndims = 1;
    PIO_Offset lcoord[1] = {0};
    PIO_Offset count[1] = {1};
    PIO_Offset lindex;

    /* Not sure what this function is really doing. */
    lindex = coord_to_lindex(ndims, lcoord, count);
    if (lindex != 0)
        return ERR_WRONG;
    
    int ndims2 = 2;
    PIO_Offset lcoord2[2] = {0, 0};
    PIO_Offset count2[2] = {1, 1};
    PIO_Offset lindex2;

    lindex2 = coord_to_lindex(ndims2, lcoord2, count2);
    if (lindex2 != 0)
        return ERR_WRONG;
    
    int ndims3 = 2;
    PIO_Offset lcoord3[2] = {1, 2};
    PIO_Offset count3[2] = {1, 1};
    PIO_Offset lindex3;

    lindex3 = coord_to_lindex(ndims3, lcoord3, count3);
    printf("lindex = %lld\n", lindex3);
    if (lindex3 != 3)
        return ERR_WRONG;
    
    return 0;
}

/* Test compute_maxIObuffersize() function. */
int test_compute_maxIObuffersize(MPI_Comm test_comm, int my_rank)
{
    int ret;

    {
        /* This will not work. */
        io_desc_t iodesc;
        iodesc.firstregion = NULL;
        if (compute_maxIObuffersize(test_comm, &iodesc) != PIO_EINVAL)
            return ERR_WRONG;
    }

    {
        /* This is a simple test with one region containing 1 data
         * element. */
        io_desc_t iodesc;
        io_region *ior1;
        int ndims = 1;

        /* This is how we allocate a region. */
        ior1 = alloc_region(ndims);
        ior1->next = NULL;
        ior1->count[0] = 1;
        
        iodesc.firstregion = ior1;
        iodesc.ndims = 1;
        
        /* Run the function. Simplest possible case. */
        if ((ret = compute_maxIObuffersize(test_comm, &iodesc)))
            return ret;
        if (iodesc.maxiobuflen != 1)
            return ERR_WRONG;
        
        /* Free resources for the region. */
        brel(ior1->start);
        brel(ior1->count);
        brel(ior1);

    }

    {
        /* This also has a single region, but with 2 dims and count
         * values > 1. */
        io_desc_t iodesc;
        io_region *ior2;
        int ndims = 2;

        /* This is how we allocate a region. */
        ior2 = alloc_region(ndims);
        ior2->next = NULL;
        ior2->count[0] = 10;
        ior2->count[1] = 2;
        
        iodesc.firstregion = ior2;
        iodesc.ndims = 2;
        
        /* Run the function. */
        if ((ret = compute_maxIObuffersize(test_comm, &iodesc)))
            return ret;
        if (iodesc.maxiobuflen != 20)
            return ERR_WRONG;
        
        /* Free resources for the region. */
        brel(ior2->start);
        brel(ior2->count);
        brel(ior2);

    }

    {
        /* This test has two regions of different sizes. */
        io_desc_t iodesc;
        io_region *ior3;
        io_region *ior4;
        int ndims = 2;

        /* This is how we allocate a region. */
        ior4 = alloc_region(ndims);
        ior4->next = NULL;
        ior4->count[0] = 10;
        ior4->count[1] = 2;

        ior3 = alloc_region(ndims);
        ior3->next = ior4;
        ior3->count[0] = 100;
        ior3->count[1] = 5;
        
        iodesc.firstregion = ior3;
        iodesc.ndims = 2;
        
        /* Run the function. */
        if ((ret = compute_maxIObuffersize(test_comm, &iodesc)))
            return ret;
        printf("iodesc.maxiobuflen = %d\n", iodesc.maxiobuflen);
        if (iodesc.maxiobuflen != 520)
            return ERR_WRONG;
        
        /* Free resources for the region. */
        brel(ior4->start);
        brel(ior4->count);
        brel(ior4);
        brel(ior3->start);
        brel(ior3->count);
        brel(ior3);
    }

    return 0;
}

/* Tests for determine_fill() function. */
int test_determine_fill(MPI_Comm test_comm)
{
    iosystem_desc_t ios;
    io_desc_t iodesc;
    int gsize[1] = {4};
    PIO_Offset *compmap = NULL;
    int ret;

    /* Set up simple test. */
    ios.union_comm = test_comm;
    iodesc.ndims = 1;
    iodesc.rearranger = PIO_REARR_SUBSET;
    iodesc.llen = 1;

    if ((ret = determine_fill(&ios, &iodesc, gsize, compmap)))
        return ret;
    if (iodesc.needsfill)
        return ERR_WRONG;

    iodesc.llen = 0;
    if ((ret = determine_fill(&ios, &iodesc, gsize, compmap)))
        return ret;
    if (!iodesc.needsfill)
        return ERR_WRONG;
    printf("iodesc.needsfill = %d\n", iodesc.needsfill);

    return 0;
}

/* Run tests for get_start_and_count_regions() funciton. */
int test_get_start_and_count_regions()
{
    return 0;
}

/* Run tests for find_region() function. */
int test_find_region()
{
    int ndims = 1;
    int gdims[1] = {1};
    int maplen = 1;
    PIO_Offset map[1] = {1};
    PIO_Offset start[1];
    PIO_Offset count[1];
    PIO_Offset regionlen;

    regionlen = find_region(ndims, gdims, maplen, map, start, count);
    printf("regionlen = %lld\n", regionlen);
    if (regionlen != 1)
        return ERR_WRONG;
    
    return 0;
}

/* Run tests for expand_region() function. */
int test_expand_region()
{
    int dim = 0;
    int gdims[1] = {1};
    int maplen = 1;
    PIO_Offset map[1] = {5};
    int region_size = 1;
    int region_stride = 1;
    int max_size[1] = {10};
    PIO_Offset count[1];

    expand_region(dim, gdims, maplen, map, region_size, region_stride, max_size, count);
    if (count[0] != 1)
        return ERR_WRONG;
    printf("max_size[0] = %d count[0] = %lld\n", max_size[0], count[0]);
    
    return 0;
}

/* Test define_iodesc_datatypes() function. */
int test_define_iodesc_datatypes()
{
#define NUM_REARRANGERS 2
    int rearranger[NUM_REARRANGERS] = {PIO_REARR_BOX, PIO_REARR_SUBSET};
    int mpierr;
    int ret;

    /* Run the functon. */
    for (int r = 0; r < NUM_REARRANGERS; r++)
    {
        iosystem_desc_t ios;
        io_desc_t iodesc;
        
        /* Set up test for IO task with BOX rearranger to create one type. */
        ios.ioproc = 1; /* this is IO proc. */
        ios.num_iotasks = 4; /* The number of IO tasks. */
        iodesc.rtype = NULL; /* Array of MPI types will be created here. */
        iodesc.nrecvs = 1; /* Number of types created. */
        iodesc.basetype = MPI_INT;
        iodesc.stype = NULL; /* Array of MPI types will be created here. */

        /* Allocate space for arrays in iodesc that will be filled in
         * define_iodesc_datatypes(). */
        if (!(iodesc.rcount = malloc(iodesc.nrecvs * sizeof(int))))
            return PIO_ENOMEM;
        if (!(iodesc.rfrom = malloc(iodesc.nrecvs * sizeof(int))))
            return PIO_ENOMEM;
        if (!(iodesc.rindex = malloc(1 * sizeof(PIO_Offset))))
            return PIO_ENOMEM;
        iodesc.rindex[0] = 0;
        iodesc.rcount[0] = 1;

        iodesc.rearranger = rearranger[r];
        
        /* The two rearrangers create a different number of send types. */
        int num_send_types = iodesc.rearranger == PIO_REARR_BOX ? ios.num_iotasks : 1;

        if (!(iodesc.sindex = malloc(num_send_types * sizeof(PIO_Offset))))
            return PIO_ENOMEM;
        if (!(iodesc.scount = malloc(num_send_types * sizeof(int))))
            return PIO_ENOMEM;
        for (int st = 0; st < num_send_types; st++)
        {
            iodesc.sindex[st] = 0;
            iodesc.scount[st] = 1;
        }

        /* Run the test function. */
        if ((ret = define_iodesc_datatypes(&ios, &iodesc)))
            return ret;
        
        /* We created send types, so free them. */
        for (int st = 0; st < num_send_types; st++)
            if ((mpierr = MPI_Type_free(&iodesc.stype[st])))
                MPIERR(mpierr);

        /* We created one receive type, so free it. */
        if ((mpierr = MPI_Type_free(&iodesc.rtype[0])))
            MPIERR(mpierr);

        /* Free resources. */
        free(iodesc.rtype);
        free(iodesc.sindex);
        free(iodesc.scount);
        free(iodesc.stype);
        free(iodesc.rcount);
        free(iodesc.rfrom);
        free(iodesc.rindex);
    }

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
    if ((ret = pio_test_init2(argc, argv, &my_rank, &ntasks, MIN_NTASKS,
                              TARGET_NTASKS, 3, &test_comm)))
        ERR(ERR_INIT);

    /* Test code runs on TARGET_NTASKS tasks. The left over tasks do
     * nothing. */
    if (my_rank < TARGET_NTASKS)
    {
        int iosysid;
        if ((ret = PIOc_Init_Intracomm(test_comm, TARGET_NTASKS, 1, 0, PIO_REARR_BOX, &iosysid)))
            return ret;
        
        printf("%d running init_rearr_opts tests\n", my_rank);
        if ((ret = test_init_rearr_opts()))
            return ret;

        printf("%d running idx_to_dim_list tests\n", my_rank);
        if ((ret = test_idx_to_dim_list()))
            return ret;

        printf("%d running coord_to_lindex tests\n", my_rank);
        if ((ret = test_coord_to_lindex()))
            return ret;

        printf("%d running compute_maxIObuffersize tests\n", my_rank);
        if ((ret = test_compute_maxIObuffersize(test_comm, my_rank)))
            return ret;

        printf("%d running determine_fill\n", my_rank);
        if ((ret = test_determine_fill(test_comm)))
            return ret;

        printf("%d running tests for expand_region()\n", my_rank);
        if ((ret = test_expand_region()))
            return ret;

        printf("%d running tests for find_region()\n", my_rank);
        if ((ret = test_find_region()))
            return ret;

        printf("%d running tests for get_start_and_count_regions()\n", my_rank);
        if ((ret = test_get_start_and_count_regions()))
            return ret;

        printf("%d running create_mpi_datatypes tests\n", my_rank);
        if ((ret = test_create_mpi_datatypes()))
            return ret;

        printf("%d running define_iodesc_datatypes tests\n", my_rank);
        if ((ret = test_define_iodesc_datatypes()))
            return ret;

        printf("%d running rearranger opts tests 1\n", my_rank);
        if ((ret = test_rearranger_opts1()))
            return ret;

        printf("%d running tests for cmp_rearr_opts()\n", my_rank);
        if ((ret = test_cmp_rearr_opts()))
            return ret;

        printf("%d running compare_offsets tests\n", my_rank);
        if ((ret = test_compare_offsets()))
            return ret;

        printf("%d running rearranger opts tests 3\n", my_rank);
        if ((ret = test_rearranger_opts3()))
            return ret;

        printf("%d running misc tests\n", my_rank);
        if ((ret = test_misc()))
            return ret;

        /* Finalize PIO system. */
        if ((ret = PIOc_finalize(iosysid)))
            return ret;

    } /* endif my_rank < TARGET_NTASKS */

    /* Finalize the MPI library. */
    printf("%d %s Finalizing...\n", my_rank, TEST_NAME);
    if ((ret = pio_test_finalize(&test_comm)))
        return ret;

    printf("%d %s SUCCESS!!\n", my_rank, TEST_NAME);

    return 0;
}
