#!/bin/bash
CONN_URL=$1

if [[ -z ${SCHEMA} ]]; then
    echo "SCHEMA undefined"
    exit 1
fi

echo "Creating tables in schema '${SCHEMA}'"

psql ${CONN_URL} << EOF
drop schema if exists ${SCHEMA} cascade;
create schema ${SCHEMA};
set schema '${SCHEMA}';
\i setup.sql
EOF

