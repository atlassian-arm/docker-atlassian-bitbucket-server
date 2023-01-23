#!/bin/bash

# Script to perform any adjustments to the unpacked app

set -e

BITBUCKET_INSTALL_DIR=$1

# Different versions of BB ship with either Elasticsearch or
# Opensearch, and some versions of Opensearch have missing runtime
# directories.
# NOTE: Permissions are set in the Dockerfile for consistency
for searchapp in ${BITBUCKET_INSTALL_DIR}/*search; do
    mkdir ${searchapp}/logs
done
