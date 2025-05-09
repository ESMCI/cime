#!/bin/bash

set -e

USER_ID=${USER_ID:-0}
GROUP_ID=${GROUP_ID:-0}

echo "Starting with UID: $USER_ID, GID: $GROUP_ID"

if ! getent group "$GROUP_ID" > /dev/null; then
    groupadd --non-unique -g "$GROUP_ID" cime_user
fi

if ! getent passwd "$USER_ID" > /dev/null; then
    useradd --shell /bin/bash --non-unique -u "$USER_ID" -g "$GROUP_ID" cime_user
fi

[ ! -e "/home/cime_user" ] && mkdir /home/cime_user

mkdir -p /home/cime_user/output/{timings,cases,inputdata,inputdata-clmforc,archive,baselines,tools}

chown -R "${USER_ID}:${GROUP_ID}" /home/cime_user
chown -R "${USER_ID}:${GROUP_ID}" /opt/spack-environment

. /opt/spack-environment/activate.sh
. /helper.sh

exec gosu "${USER_ID}:${GROUP_ID}" "$@"