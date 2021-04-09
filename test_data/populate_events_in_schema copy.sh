#!/bin/bash

CONN_URL=$1

if [[ -z ${SCHEMA} ]]; then
    echo "SCHEMA undefined"
    exit 1
fi

echo "Populate events in schema '${SCHEMA}'"

psql ${CONN_URL} << EOF
set schema '${SCHEMA}';
\i populate_events.sql
EOF

