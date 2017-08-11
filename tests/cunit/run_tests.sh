#set -e
printf 'running PIO tests...'
echo
printf 'running test_spmd...\n'
mpiexec -n 4 ./test_spmd
# echo
# printf 'running test_rearr...'
# mpiexec -n 4 ./test_rearr
# mpiexec -n 4 ./test_intercomm2
# mpiexec -n 4 ./test_async_simple
# mpiexec -n 4 ./test_async_3proc
# mpiexec -n 4 ./test_async_4proc
# mpiexec -n 4 ./test_iosystem2_simple
# mpiexec -n 4 ./test_iosystem2_simple2
# mpiexec -n 4 ./test_iosystem2
# mpiexec -n 4 ./test_iosystem3_simple
# mpiexec -n 4 ./test_iosystem3_simple2
# mpiexec -n 4 ./test_iosystem3
# mpiexec -n 4 ./test_pioc
# mpiexec -n 4 ./test_pioc_unlim
# mpiexec -n 4 ./test_pioc_putget
# mpiexec -n 4 ./test_pioc_fill
# mpiexec -n 4 ./test_darray
# mpiexec -n 4 ./test_darray_multi
# mpiexec -n 4 ./test_darray_multivar
# mpiexec -n 4 ./test_darray_multivar2
# mpiexec -n 4 ./test_darray_multivar3
# mpiexec -n 4 ./test_darray_1d
# mpiexec -n 4 ./test_darray_3d
# mpiexec -n 4 ./test_decomp_uneven
# mpiexec -n 4 ./test_decomps
# mpiexec -n 4 ./test_darray_async_simple
# mpiexec -n 4 ./test_darray_async
# mpiexec -n 4 ./test_darray_async_many
