#!/bin/bash

. src/.env_mach_specific.sh
./runoff_map < runoff_map_gl4_tnx1v4.nml
./run_merge_mapping_files.sh \
--map_in_oo map_gland4km_epsg3413_to_tnx1v4_nn.nc \
--map_in_ms map_gland4km_to_tnx1v4_nnsm_e1000r300_181030.nc \
#--region_mask /cluster/shared/noresm/inputdata/ocn/pop/gx1v6/grid/region_mask_20090205.ieeei4
--map_out map_gland4km_to_tnx1v4_nn_open_ocean_nnsm_e1000r300_marginal_sea_181030.nc
