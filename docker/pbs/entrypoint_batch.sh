#!/bin/bash

/opt/pbs/libexec/pbs_postinstall

service pbs start

. /etc/profile.d/pbs.sh

qmgr -c "set server flatuid=true"
qmgr -c "set server acl_roots+=root@*"
qmgr -c "set server operators+=root@*"
qmgr -c "set server job_history_enable=true"
