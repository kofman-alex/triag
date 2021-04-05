#!/bin/bash

CONN_URL=$1

if [[ -z ${SCHEMA} ]]; then
    echo "SCHEMA undefined"
    exit 1
fi

echo "Creating rules in schema '${SCHEMA}'"

psql ${CONN_URL} << EOF
set schema '${SCHEMA}';
\i create_rules.sql
EOF

