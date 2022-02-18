#!/bin/bash

set -e


# no-op on BbS >= 7.21
supportsOpenSearch() {
    local OPENSEARCH_VERSION_START="7.21.0"
    local LOWEST_VERSION=$(echo "$1 ${OPENSEARCH_VERSION_START}" | tr " " "\n" | sort -V | head -n 1)
    if [[ "${LOWEST_VERSION}" == "${OPENSEARCH_VERSION_START}" ]]; then
        return 0
    fi
    return 1
}

if supportsOpenSearch "${BITBUCKET_VERSION}"; then
    echo "Bitbucket version ${BITBUCKET_VERSION} is >= 7.21.0, skipping"
    exit 0
fi


# Mitigation for the Log4j security vulnerabilities (CVE-2021-44228 & CVE-2021-45046)
echo "Bitbucket version ${BITBUCKET_VERSION} is < 7.21.0, updating log4j Elasticsearch libraries"

ELASTICSEARCH_DIR=${BITBUCKET_INSTALL_DIR}/elasticsearch
MAVEN_LOG4J_URL=https://repo1.maven.org/maven2/org/apache/logging/log4j

rm -f ${ELASTICSEARCH_DIR}/lib/log4j-api-2.*.jar ${ELASTICSEARCH_DIR}/lib/log4j-core-2.*.jar ${BITBUCKET_INSTALL_DIR}/app/WEB-INF/lib/log4j-core-2.*.jar
curl -L --silent ${MAVEN_LOG4J_URL}/log4j-api/2.17.1/log4j-api-2.17.1.jar -o ${ELASTICSEARCH_DIR}/lib/log4j-api-2.17.1.jar
curl -L --silent ${MAVEN_LOG4J_URL}/log4j-core/2.17.1/log4j-core-2.17.1.jar -o ${ELASTICSEARCH_DIR}/lib/log4j-core-2.17.1.jar