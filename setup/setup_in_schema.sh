#!/bin/bash

if [[ -z ${SCHEMA} ]]; then
    echo "SCHEMA undefined"
    exit 1
fi

echo "Creating tables in schema '${SCHEMA}'"

psql $1 << EOF
create schema ${SCHEMA};
set schema '${SCHEMA}';
\i setup.sql
EOF

