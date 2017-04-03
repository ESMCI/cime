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

/* For 1-D use. */
#define NDIM1 1

/* For maplens of 2. */
#define MAPLEN2 2

/* Test some of the rearranger utility functions. */
int test_rearranger_opts1(int iosysid)
{
    iosystem_desc_t *ios;
    int ret;
    
    /* This should not work. */
    if (PIOc_set_rearr_opts(TEST_VAL_42, 0, 0, false, false, 0, false,
                            false, 0) != PIO_EBADID)
        return ERR_WRONG;
    if (PIOc_set_rearr_opts(iosysid, TEST_VAL_42, 0, false, false, 0, false,
                            false, 0) != PIO_EINVAL)
        return ERR_WRONG;
    if (PIOc_set_rearr_opts(iosysid, 0, TEST_VAL_42, false, false, 0, false,
                            false, 0) != PIO_EINVAL)
        return ERR_WRONG;
    if (PIOc_set_rearr_opts(iosysid, 0, 0, false, false,
                            PIO_REARR_COMM_UNLIMITED_PEND_REQ - 1, false,
                            false, 0) != PIO_EINVAL)
        return ERR_WRONG;
    if (PIOc_set_rearr_opts(iosysid, 0, 0, false, false, 0, false,
                            false, PIO_REARR_COMM_UNLIMITED_PEND_REQ - 1) !=
        PIO_EINVAL)
        return ERR_WRONG;

    /* This should work. */
    if ((ret = PIOc_set_rearr_opts(iosysid, PIO_REARR_COMM_P2P,
                                   PIO_REARR_COMM_FC_1D_COMP2IO, true,
                                   true, TEST_VAL_42, true, true, TEST_VAL_42 + 1)))
        return ret;

    /* Get the IO system info from the id. */
    if (!(ios = pio_get_iosystem_from_id(iosysid)))
        return pio_err(NULL, NULL, PIO_EBADID, __FILE__, __LINE__);

    /* Check the rearranger settings. */
    if (ios->rearr_opts.comm_type != PIO_REARR_COMM_P2P ||
        ios->rearr_opts.fcd != PIO_REARR_COMM_FC_1D_COMP2IO ||
        !ios->rearr_opts.comp2io.hs || !ios->rearr_opts.comp2io.isend ||
        !ios->rearr_opts.io2comp.hs || !ios->rearr_opts.io2comp.isend ||
        ios->rearr_opts.comp2io.max_pend_req != TEST_VAL_42 ||
        ios->rearr_opts.io2comp.max_pend_req != TEST_VAL_42 + 1)
        return ERR_WRONG;

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

/* Test the create_mpi_datatypes() function. 
 * @returns 0 for success, error code otherwise.*/
int test_create_mpi_datatypes()
{
    MPI_Datatype basetype = MPI_INT;
    int *mfrom = NULL;
    int mpierr;
    int ret;
    
    {
        int msgcnt = 1;
        PIO_Offset mindex[1] = {0};
        int mcount[1] = {1};
        MPI_Datatype mtype;
        
        /* Create an MPI data type. */
        if ((ret = create_mpi_datatypes(basetype, msgcnt, mindex, mcount, mfrom, &mtype)))
            return ret;
        
        /* Free the type. */
        if ((mpierr = MPI_Type_free(&mtype)))
            MPIERR(mpierr);
    }

    {
        int msgcnt = 4;
        PIO_Offset mindex[4] = {0, 0, 0, 0};
        int mcount[4] = {1, 1, 1, 1};
        MPI_Datatype mtype2[4];

        /* Create 4 MPI data types. */
        if ((ret = create_mpi_datatypes(basetype, msgcnt, mindex, mcount, mfrom, mtype2)))
            return ret;

        /* Check the size of the data types. It should be 4. */
        MPI_Aint lb, extent;
        for (int t = 0; t < 4; t++)
        {
            if ((mpierr = MPI_Type_get_extent(mtype2[t], &lb, &extent)))
                MPIERR(mpierr);
            printf("t = %d lb = %ld extent = %ld\n", t, lb, extent);
            if (lb != 0 || extent != 4)
                return ERR_WRONG;
        }
            
        /* Free them. */
        for (int t = 0; t < 4; t++)
            if ((mpierr = MPI_Type_free(&mtype2[t])))
                return ERR_WRONG;
    }
    
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

    /* According to function docs, we should get 2,0 */
    idx_to_dim_list(ndims2, gdims2, idx2, dim_list2);
    printf("dim_list2[0] = %lld\n", dim_list2[0]);
    printf("dim_list2[1] = %lld\n", dim_list2[1]);

    /* This is the correct result! */
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
        /* This is a simple test with one region containing 1 data
         * element. */
        io_desc_t iodesc;
        io_region *ior1;
        int ndims = 1;

        /* This is how we allocate a region. */
        if ((ret = alloc_region2(NULL, ndims, &ior1)))
            return ret;
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
        free(ior1->start);
        free(ior1->count);
        free(ior1);

    }

    {
        /* This also has a single region, but with 2 dims and count
         * values > 1. */
        io_desc_t iodesc;
        io_region *ior2;
        int ndims = 2;

        /* This is how we allocate a region. */
        if ((ret = alloc_region2(NULL, ndims, &ior2)))
            return ret;

        /* These should be 0. */
        for (int i = 0; i < ndims; i++)
            if (ior2->start[i] != 0 || ior2->count[i] != 0)
                return ERR_WRONG;
        
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
        free(ior2->start);
        free(ior2->count);
        free(ior2);
    }

    {
        /* This test has two regions of different sizes. */
        io_desc_t iodesc;
        io_region *ior3;
        io_region *ior4;
        int ndims = 2;

        /* This is how we allocate a region. */
        if ((ret = alloc_region2(NULL, ndims, &ior4)))
            return ret;
        ior4->next = NULL;
        ior4->count[0] = 10;
        ior4->count[1] = 2;

        if ((ret = alloc_region2(NULL, ndims, &ior3)))
            return ret;
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
        free(ior4->start);
        free(ior4->count);
        free(ior4);
        free(ior3->start);
        free(ior3->count);
        free(ior3);
    }

    return 0;
}

/* Tests for determine_fill() function. */
int test_determine_fill(MPI_Comm test_comm)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    int gsize[1] = {4};
    PIO_Offset compmap[1] = {1};
    int ret;

    /* Initialize ios. */
    if (!(ios = calloc(1, sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;
    ios->union_comm = test_comm;

    /* Set up iodesc for test. */
    if (!(iodesc = calloc(1, sizeof(io_desc_t))))
        return PIO_ENOMEM;
    iodesc->ndims = 1;
    iodesc->rearranger = PIO_REARR_SUBSET;
    iodesc->llen = 1;

    /* We don't need fill. */
    if ((ret = determine_fill(ios, iodesc, gsize, compmap)))
        return ret;
    if (iodesc->needsfill)
        return ERR_WRONG;

    /* Change settings, so now we do need fill. */
    iodesc->llen = 0;
    if ((ret = determine_fill(ios, iodesc, gsize, compmap)))
        return ret;
    if (!iodesc->needsfill)
        return ERR_WRONG;

    /* Free test resources. */
    free(ios);
    free(iodesc);
    
    return 0;
}

/* Run tests for get_start_and_count_regions() funciton. */
int test_get_regions(int my_rank)
{
#define MAPLEN 2
    int ndims = NDIM1;
    const int gdimlen[NDIM1] = {8};
    /* Don't forget map is 1-based!! */
    PIO_Offset map[MAPLEN] = {(my_rank * 2) + 1, ((my_rank + 1) * 2) + 1};
    int maxregions;
    io_region *ior1;
    int ret;

    /* This is how we allocate a region. */
    if ((ret = alloc_region2(NULL, NDIM1, &ior1)))
        return ret;
    ior1->next = NULL;
    ior1->count[0] = 1;
    
    /* Call the function we are testing. */
    if ((ret = get_regions(ndims, gdimlen, MAPLEN, map, &maxregions, ior1)))
        return ret;
    if (maxregions != 2)
        return ERR_WRONG;

    /* Free resources for the region. */
    free(ior1->next->start);
    free(ior1->next->count);
    free(ior1->next);
    free(ior1->start);
    free(ior1->count);
    free(ior1);
    
    return 0;
}

/* Run tests for find_region() function. */
int test_find_region()
{
    int ndims = NDIM1;
    int gdimlen[NDIM1] = {4};
    int maplen = 1;
    PIO_Offset map[1] = {1};
    PIO_Offset start[NDIM1];
    PIO_Offset count[NDIM1];
    PIO_Offset regionlen;

    /* Call the function we are testing. */
    regionlen = find_region(ndims, gdimlen, maplen, map, start, count);

    /* Check results. */
    printf("regionlen = %lld start[0] = %lld count[0] = %lld\n", regionlen, start[0], count[0]);
    if (regionlen != 1 || start[0] != 0 || count[0] != 1)
        return ERR_WRONG;
    
    return 0;
}

/* Run tests for expand_region() function. */
int test_expand_region()
{
    int dim = 0;
    int gdims[NDIM1] = {1};
    int maplen = 1;
    PIO_Offset map[1] = {5};
    int region_size = 1;
    int region_stride = 1;
    int max_size[NDIM1] = {10};
    PIO_Offset count[NDIM1];

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

/* Test the compute_counts() function with the box rearranger. */
int test_compute_counts(MPI_Comm test_comm, int my_rank)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    int dest_ioproc[TARGET_NTASKS] = {0, 1, 2, 3};
    PIO_Offset dest_ioindex[TARGET_NTASKS] = {0, 1, 2, 3};
    int ret;

    /* Initialize ios. */
    if (!(ios = calloc(1, sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;
    
    ios->num_iotasks = TARGET_NTASKS;
    ios->num_comptasks = TARGET_NTASKS;
    ios->ioproc = 1;
    ios->union_comm = test_comm;
    if (!(ios->ioranks = malloc(TARGET_NTASKS * sizeof(int))))
        return PIO_ENOMEM;
    for (int t = 0; t < TARGET_NTASKS; t++)
        ios->ioranks[t] = t;
    
    /* Initialize iodesc. */
    if (!(iodesc = calloc(1, sizeof(io_desc_t))))
        return PIO_ENOMEM;
    iodesc->rearranger = PIO_REARR_BOX;
    iodesc->ndof = TARGET_NTASKS;
    iodesc->llen = TARGET_NTASKS;
    iodesc->rearr_opts.comm_type = PIO_REARR_COMM_COLL;
    iodesc->rearr_opts.fcd = PIO_REARR_COMM_FC_2D_DISABLE;

    /* Test the function. */
    if ((ret = compute_counts(ios, iodesc, dest_ioproc, dest_ioindex)))
        return ret;

    /* Check results. */
    for (int i = 0; i < ios->num_iotasks; i++)
        if (iodesc->scount[i] != 1 || iodesc->sindex[i] != i)
            return ERR_WRONG;

    for (int i = 0; i < iodesc->ndof; i++)
        if (iodesc->rcount[i] != 1 || iodesc->rfrom[i] != i ||
            iodesc->rindex[i] != my_rank)
            return ERR_WRONG;

    /* Free resources allocated in compute_counts(). */
    free(iodesc->scount);
    free(iodesc->sindex);
    free(iodesc->rcount);
    free(iodesc->rfrom);
    free(iodesc->rindex);

    /* Free test resources. */
    free(ios->ioranks);
    free(iodesc);
    free(ios);

    return 0;
}

/* Call PIOc_InitDecomp() with parameters such that it calls
 * box_rearrange_create() just like test_box_rearrange_create() will
 * (see below). */
int test_init_decomp(int iosysid, MPI_Comm test_comm, int my_rank)
{
    int ioid;
    PIO_Offset compmap[MAPLEN2] = {my_rank * 2, (my_rank + 1) * 2};
    const int gdimlen[NDIM1] = {8};
    int ret;

    /* Initialize a decomposition. */
    if ((ret = PIOc_init_decomp(iosysid, PIO_INT, NDIM1, gdimlen, MAPLEN2,
                                compmap, &ioid, PIO_REARR_BOX, NULL, NULL)))
        return ret;

    /* Free it. */
    if ((ret = PIOc_freedecomp(iosysid, ioid)))
        return ret;
            
    return 0;
}

/* Test for the box_rearrange_create() function. */
int test_box_rearrange_create(MPI_Comm test_comm, int my_rank)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    io_region *ior1;    
    int maplen = MAPLEN2;
    PIO_Offset compmap[MAPLEN2] = {(my_rank * 2) + 1, ((my_rank + 1) * 2) + 1};
    const int gdimlen[NDIM1] = {8};
    int ndims = NDIM1;
    int ret;

    /* Allocate IO system info struct for this test. */
    if (!(ios = calloc(1, sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;

    /* Allocate IO desc struct for this test. */
    if (!(iodesc = calloc(1, sizeof(io_desc_t))))
        return PIO_ENOMEM;

    /* Default rearranger options. */
    iodesc->rearr_opts.comm_type = PIO_REARR_COMM_COLL;
    iodesc->rearr_opts.fcd = PIO_REARR_COMM_FC_2D_DISABLE;

    /* Set up for determine_fill(). */
    ios->union_comm = test_comm;
    ios->io_comm = test_comm;
    iodesc->ndims = NDIM1;
    iodesc->rearranger = PIO_REARR_BOX;

    /* Set up the IO task info for the test. */
    ios->ioproc = 1;
    ios->union_rank = my_rank;
    ios->num_iotasks = 4;
    ios->num_comptasks = 4;
    if (!(ios->ioranks = calloc(ios->num_iotasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
    for (int i = 0; i < TARGET_NTASKS; i++)
        ios->ioranks[i] = i;

    /* This is how we allocate a region. */
    if ((ret = alloc_region2(NULL, NDIM1, &ior1)))
        return ret;
    if (my_rank == 0)
        ior1->count[0] = 8;
    
    iodesc->firstregion = ior1;

    /* We are finally ready to run the code under test. */
    if ((ret = box_rearrange_create(ios, maplen, compmap, gdimlen, ndims, iodesc)))
        return ret;

    /* Check some results. */
    if (iodesc->rearranger != PIO_REARR_BOX || iodesc->ndof != maplen ||
        iodesc->llen != my_rank ? 0 : 8 || !iodesc->needsfill)
        return ERR_WRONG;

    /* for (int i = 0; i < ios->num_iotasks; i++) */
    /* { */
    /*     /\* sindex is only allocated if scount[i] > 0. *\/ */
    /*     if (iodesc->scount[i] != i ? 0 : 1 || */
    /*         (iodesc->scount[i] && iodesc->sindex[i] != 0)) */
    /*         return ERR_WRONG; */
    /* } */

    /* for (int i = 0; i < iodesc->ndof; i++) */
    /* { */
    /*     /\* rcount is 1 for rank 0, 0 on other tasks. *\/ */
    /*     if (iodesc->rcount[i] != my_rank ? 0 : 1) */
    /*         return ERR_WRONG; */
        
    /*     /\* rfrom is 0 everywhere, except task 0, array elemnt 1. *\/ */
    /*     if (my_rank == 0 && i == 1) */
    /*     { */
    /*         if (iodesc->rfrom[i] != 1) */
    /*             return ERR_WRONG; */
    /*     } */
    /*     else */
    /*     { */
    /*         if (iodesc->rfrom[i] != 0) */
    /*             return ERR_WRONG; */
    /*     } */
        
    /*     /\* rindex is only allocated where there is a non-zero count. *\/ */
    /*     if (iodesc->rcount[i]) */
    /*         if (iodesc->rindex[i] != 0) */
    /*             return ERR_WRONG; */
    /* } */

    /* Free resources allocated in compute_counts(). */
    free(iodesc->scount);
    free(iodesc->sindex);
    free(iodesc->rcount);
    free(iodesc->rfrom);
    free(iodesc->rindex);

    /* Free resources from test. */
    free(ior1->start);
    free(ior1->count);
    free(ior1);
    free(ios->ioranks);
    free(iodesc);
    free(ios);
    
    return 0;
}

/* Test for the box_rearrange_create() function. */
int test_box_rearrange_create_2(MPI_Comm test_comm, int my_rank)
{
#define MAPLEN2 2
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    io_region *ior1;    
    int maplen = MAPLEN2;
    PIO_Offset compmap[MAPLEN2] = {1, 0};
    const int gdimlen[NDIM1] = {8};
    int ndims = NDIM1;
    int ret;

    /* Allocate IO system info struct for this test. */
    if (!(ios = calloc(1, sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;

    /* Allocate IO desc struct for this test. */
    if (!(iodesc = calloc(1, sizeof(io_desc_t))))
        return PIO_ENOMEM;

    /* Default rearranger options. */
    iodesc->rearr_opts.comm_type = PIO_REARR_COMM_COLL;
    iodesc->rearr_opts.fcd = PIO_REARR_COMM_FC_2D_DISABLE;

    /* Set up for determine_fill(). */
    ios->union_comm = test_comm;
    ios->io_comm = test_comm;
    iodesc->ndims = NDIM1;
    iodesc->rearranger = PIO_REARR_BOX;

    /* This is the size of the map in computation tasks. */
    iodesc->ndof = 2;

    /* Set up the IO task info for the test. */
    ios->ioproc = 1;
    ios->union_rank = my_rank;
    ios->num_iotasks = 4;
    ios->num_comptasks = 4;
    if (!(ios->ioranks = calloc(ios->num_iotasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
    for (int i = 0; i < TARGET_NTASKS; i++)
        ios->ioranks[i] = i;

    /* This is how we allocate a region. */
    if ((ret = alloc_region2(NULL, NDIM1, &ior1)))
        return ret;
    ior1->next = NULL;
    if (my_rank == 0)
        ior1->count[0] = 8;
    
    iodesc->firstregion = ior1;

    /* We are finally ready to run the code under test. */
    if ((ret = box_rearrange_create(ios, maplen, compmap, gdimlen, ndims, iodesc)))
        return ret;

    /* Check some results. */
    if (iodesc->rearranger != PIO_REARR_BOX || iodesc->ndof != maplen ||
        iodesc->llen != my_rank ? 0 : 8 || !iodesc->needsfill)
        return ERR_WRONG;

    for (int i = 0; i < ios->num_iotasks; i++)
    {
        /* sindex is only allocated if scount[i] > 0. */
        if (iodesc->scount[i] != i ? 0 : 1 ||
            (iodesc->scount[i] && iodesc->sindex[i] != 0))
            return ERR_WRONG;
    }

    for (int i = 0; i < iodesc->ndof; i++)
    {
        /* rcount is 1 for rank 0, 0 on other tasks. */
        if (my_rank == 0 && iodesc->rcount[i] != 1)
            return ERR_WRONG;
        
        /* rfrom only matters if there is a non-zero count. */
        if (iodesc->rcount[i])
            if (iodesc->rfrom[i] != i ? 1 : 0)
                return ERR_WRONG;
        
        /* rindex is only allocated where there is a non-zero count. */
        if (iodesc->rcount[i])
            if (iodesc->rindex[i] != 0)
                return ERR_WRONG;
    }

    /* Free resources allocated in compute_counts(). */
    free(iodesc->scount);
    free(iodesc->sindex);
    free(iodesc->rcount);
    free(iodesc->rfrom);
    free(iodesc->rindex);

    /* Free resources from test. */
    free(ior1->start);
    free(ior1->count);
    free(ior1);
    free(ios->ioranks);
    free(iodesc);
    free(ios);
    
    return 0;
}

/* Test function default_subset_partition. */
int test_default_subset_partition(MPI_Comm test_comm, int my_rank)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    int mpierr;
    int ret;

    /* Allocate IO system info struct for this test. */
    if (!(ios = calloc(1, sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;

    /* Allocate IO desc struct for this test. */
    if (!(iodesc = calloc(1, sizeof(io_desc_t))))
        return PIO_ENOMEM;

    ios->ioproc = 1;
    ios->io_rank = my_rank;
    ios->comp_comm = test_comm;

    /* Run the function to test. */
    if ((ret = default_subset_partition(ios, iodesc)))
        return ret;

    /* Free the created communicator. */
    if ((mpierr = MPI_Comm_free(&iodesc->subset_comm)))
        MPIERR(mpierr);

    /* Free resources from test. */
    free(iodesc);
    free(ios);

    return 0;
}

/* Test function rearrange_comp2io. */
int test_rearrange_comp2io(MPI_Comm test_comm, int my_rank)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    void *sbuf = NULL;
    void *rbuf = NULL;
    int nvars = 1;
    io_region *ior1;
    int maplen = 2;
    PIO_Offset compmap[2] = {1, 0};
    const int gdimlen[NDIM1] = {8};
    int ndims = NDIM1;
    int mpierr;
    int ret;

    /* Allocate some space for data. */
    if (!(sbuf = calloc(4, sizeof(int))))
        return PIO_ENOMEM;
    if (!(rbuf = calloc(4, sizeof(int))))
        return PIO_ENOMEM;
        
    /* Allocate IO system info struct for this test. */
    if (!(ios = calloc(1, sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;

    /* Allocate IO desc struct for this test. */
    if (!(iodesc = calloc(1, sizeof(io_desc_t))))
        return PIO_ENOMEM;

    ios->ioproc = 1;
    ios->io_rank = my_rank;
    ios->union_comm = test_comm;
    ios->num_iotasks = TARGET_NTASKS;
    iodesc->rearranger = PIO_REARR_BOX;
    iodesc->basetype = MPI_INT;

    /* Set up test for IO task with BOX rearranger to create one type. */
    ios->ioproc = 1; /* this is IO proc. */
    ios->num_iotasks = 4; /* The number of IO tasks. */
    iodesc->rtype = NULL; /* Array of MPI types will be created here. */
    iodesc->nrecvs = 1; /* Number of types created. */
    iodesc->basetype = MPI_INT;
    iodesc->stype = NULL; /* Array of MPI types will be created here. */

    /* The two rearrangers create a different number of send types. */
    int num_send_types = iodesc->rearranger == PIO_REARR_BOX ? ios->num_iotasks : 1;

    /* Default rearranger options. */
    iodesc->rearr_opts.comm_type = PIO_REARR_COMM_COLL;
    iodesc->rearr_opts.fcd = PIO_REARR_COMM_FC_2D_DISABLE;

    /* Set up for determine_fill(). */
    ios->union_comm = test_comm;
    ios->io_comm = test_comm;
    iodesc->ndims = NDIM1;
    iodesc->rearranger = PIO_REARR_BOX;

    iodesc->ndof = 4;

    /* Set up the IO task info for the test. */
    ios->ioproc = 1;
    ios->union_rank = my_rank;
    ios->num_iotasks = 4;
    ios->num_comptasks = 4;
    if (!(ios->ioranks = calloc(ios->num_iotasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
    for (int i = 0; i < TARGET_NTASKS; i++)
        ios->ioranks[i] = i;

    /* This is how we allocate a region. */
    if ((ret = alloc_region2(NULL, NDIM1, &ior1)))
        return ret;
    ior1->next = NULL;
    if (my_rank == 0)
        ior1->count[0] = 8;
    
    iodesc->firstregion = ior1;

    /* Create the box rearranger. */
    if ((ret = box_rearrange_create(ios, maplen, compmap, gdimlen, ndims, iodesc)))
        return ret;

    /* Run the function to test. */
    if ((ret = rearrange_comp2io(ios, iodesc, sbuf, rbuf, nvars)))
        return ret;
    printf("returned from rearrange_comp2io\n");

    /* We created send types, so free them. */
    for (int st = 0; st < num_send_types; st++)
        if (iodesc->stype[st] != PIO_DATATYPE_NULL)        
            if ((mpierr = MPI_Type_free(&iodesc->stype[st])))
                MPIERR(mpierr);

    /* We created one receive type, so free it. */
    if (iodesc->rtype)
        for (int r = 0; r < iodesc->nrecvs; r++)
            if (iodesc->rtype[r] != PIO_DATATYPE_NULL)
                if ((mpierr = MPI_Type_free(&iodesc->rtype[r])))
                    MPIERR(mpierr);

    /* Free resources allocated in library code. */
    free(iodesc->rtype);
    free(iodesc->sindex);
    free(iodesc->scount);
    free(iodesc->stype);
    free(iodesc->rcount);
    free(iodesc->rfrom);
    free(iodesc->rindex);

    /* Free resources from test. */
    free(ior1->start);
    free(ior1->count);
    free(ior1);
    free(ios->ioranks);
    free(iodesc);
    free(ios);
    free(sbuf);
    free(rbuf);

    return 0;
}

/* Test function rearrange_io2comp. */
int test_rearrange_io2comp(MPI_Comm test_comm, int my_rank)
{
    iosystem_desc_t *ios;
    io_desc_t *iodesc;
    void *sbuf = NULL;
    void *rbuf = NULL;
    io_region *ior1;
    int maplen = 2;
    PIO_Offset compmap[2] = {1, 0};
    const int gdimlen[NDIM1] = {8};
    int ndims = NDIM1;
    int mpierr;
    int ret;

    /* Allocate some space for data. */
    if (!(sbuf = calloc(4, sizeof(int))))
        return PIO_ENOMEM;
    if (!(rbuf = calloc(4, sizeof(int))))
        return PIO_ENOMEM;
        
    /* Allocate IO system info struct for this test. */
    if (!(ios = calloc(1, sizeof(iosystem_desc_t))))
        return PIO_ENOMEM;

    /* Allocate IO desc struct for this test. */
    if (!(iodesc = calloc(1, sizeof(io_desc_t))))
        return PIO_ENOMEM;

    ios->ioproc = 1;
    ios->io_rank = my_rank;
    ios->union_comm = test_comm;
    ios->num_iotasks = TARGET_NTASKS;
    iodesc->rearranger = PIO_REARR_BOX;
    iodesc->basetype = MPI_INT;

    /* Set up test for IO task with BOX rearranger to create one type. */
    ios->ioproc = 1; /* this is IO proc. */
    ios->num_iotasks = 4; /* The number of IO tasks. */
    iodesc->rtype = NULL; /* Array of MPI types will be created here. */
    iodesc->nrecvs = 1; /* Number of types created. */
    iodesc->basetype = MPI_INT;
    iodesc->stype = NULL; /* Array of MPI types will be created here. */

    /* The two rearrangers create a different number of send types. */
    int num_send_types = iodesc->rearranger == PIO_REARR_BOX ? ios->num_iotasks : 1;

    /* Default rearranger options. */
    iodesc->rearr_opts.comm_type = PIO_REARR_COMM_COLL;
    iodesc->rearr_opts.fcd = PIO_REARR_COMM_FC_2D_DISABLE;

    /* Set up for determine_fill(). */
    ios->union_comm = test_comm;
    ios->io_comm = test_comm;
    iodesc->ndims = NDIM1;
    iodesc->rearranger = PIO_REARR_BOX;

    iodesc->ndof = 4;

    /* Set up the IO task info for the test. */
    ios->ioproc = 1;
    ios->union_rank = my_rank;
    ios->num_iotasks = 4;
    ios->num_comptasks = 4;
    if (!(ios->ioranks = calloc(ios->num_iotasks, sizeof(int))))
        return pio_err(ios, NULL, PIO_ENOMEM, __FILE__, __LINE__);
    for (int i = 0; i < TARGET_NTASKS; i++)
        ios->ioranks[i] = i;

    /* This is how we allocate a region. */
    if ((ret = alloc_region2(NULL, NDIM1, &ior1)))
        return ret;
    ior1->next = NULL;
    if (my_rank == 0)
        ior1->count[0] = 8;
    
    iodesc->firstregion = ior1;

    /* Create the box rearranger. */
    if ((ret = box_rearrange_create(ios, maplen, compmap, gdimlen, ndims, iodesc)))
        return ret;

    /* Run the function to test. */
    if ((ret = rearrange_io2comp(ios, iodesc, sbuf, rbuf)))
        return ret;
    printf("returned from rearrange_comp2io\n");

    /* We created send types, so free them. */
    for (int st = 0; st < num_send_types; st++)
        if (iodesc->stype[st] != PIO_DATATYPE_NULL)        
            if ((mpierr = MPI_Type_free(&iodesc->stype[st])))
                MPIERR(mpierr);

    /* We created one receive type, so free it. */
    if (iodesc->rtype)
        for (int r = 0; r < iodesc->nrecvs; r++)
            if (iodesc->rtype[r] != PIO_DATATYPE_NULL)
                if ((mpierr = MPI_Type_free(&iodesc->rtype[r])))
                    MPIERR(mpierr);

    /* Free resources allocated in library code. */
    free(iodesc->rtype);
    free(iodesc->sindex);
    free(iodesc->scount);
    free(iodesc->stype);
    free(iodesc->rcount);
    free(iodesc->rfrom);
    free(iodesc->rindex);

    /* Free resources from test. */
    free(ior1->start);
    free(ior1->count);
    free(ior1);
    free(ios->ioranks);
    free(iodesc);
    free(ios);
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

        printf("%d running tests for get_regions()\n", my_rank);
        if ((ret = test_get_regions(my_rank)))
            return ret;

        printf("%d running create_mpi_datatypes tests\n", my_rank);
        if ((ret = test_create_mpi_datatypes()))
            return ret;

        printf("%d running define_iodesc_datatypes tests\n", my_rank);
        if ((ret = test_define_iodesc_datatypes()))
            return ret;

        printf("%d running rearranger opts tests 1\n", my_rank);
        if ((ret = test_rearranger_opts1(iosysid)))
            return ret;

        printf("%d running compare_offsets tests\n", my_rank);
        if ((ret = test_compare_offsets()))
            return ret;

        printf("%d running compute_counts tests for box rearranger\n", my_rank);
        if ((ret = test_compute_counts(test_comm, my_rank)))
            return ret;

        printf("%d running test for init_decomp\n", my_rank);
        if ((ret = test_init_decomp(iosysid, test_comm, my_rank)))
            return ret;

        printf("%d running tests for box_rearrange_create\n", my_rank);
        if ((ret = test_box_rearrange_create(test_comm, my_rank)))
            return ret;

        printf("%d running more tests for box_rearrange_create\n", my_rank);
        if ((ret = test_box_rearrange_create_2(test_comm, my_rank)))
            return ret;

        printf("%d running tests for default_subset_partition\n", my_rank);
        if ((ret = test_default_subset_partition(test_comm, my_rank)))
            return ret;

        printf("%d running tests for rearrange_comp2io\n", my_rank);
        if ((ret = test_rearrange_comp2io(test_comm, my_rank)))
            return ret;

        printf("%d running tests for rearrange_io2comp\n", my_rank);
        if ((ret = test_rearrange_io2comp(test_comm, my_rank)))
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
