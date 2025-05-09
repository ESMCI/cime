#!/bin/bash

function fix_mct_arflags() {
    local mct_path="${1}"

    # TODO make PR to fix
    if [[ ! -e "${mct_path}/mct/Makefile.bak" ]]
    then
        echo "Fixing AR variable in ${mct_path}/mct/Makefile"

        sed -i".bak" "s/\$(AR)/\$(AR) -cqv/g" "${mct_path}/mct/Makefile"
    fi

    if [[ ! -e "${mct_path}/mpeu/Makefile.bak" ]]
    then
        echo "Fixing AR variable in ${mct_path}/mpeu/Makefile"

        sed -i".bak" "s/\$(AR)/\$(AR) -cqv/g" "${mct_path}/mpeu/Makefile"
    fi
}