ARG BASE_IMAGE=adoptopenjdk/openjdk11
FROM $BASE_IMAGE

LABEL maintainer="dc-deployments@atlassian.com"
LABEL securitytxt="https://www.atlassian.com/.well-known/security.txt"

ARG BITBUCKET_VERSION

ENV APP_NAME                                        bitbucket
ENV RUN_USER                                        bitbucket
ENV RUN_GROUP                                       bitbucket
ENV RUN_UID                                         2003
ENV RUN_GID                                         2003

# https://confluence.atlassian.com/display/BitbucketServer/Bitbucket+Server+home+directory
ENV BITBUCKET_HOME                                  /var/atlassian/application-data/bitbucket
ENV BITBUCKET_INSTALL_DIR                           /opt/atlassian/bitbucket
ENV BITBUCKET_ELASTICSEARCH_DIR                     ${BITBUCKET_ELASTICSEARCH_DIR}
ENV ELASTICSEARCH_ENABLED                           true
ENV APPLICATION_MODE                                default
ENV JRE_HOME                                        /opt/java/openjdk
ENV JAVA_BINARY                                     ${JRE_HOME}/bin/java
ENV MAVEN_LOG4J_URL                                 https://repo1.maven.org/maven2/org/apache/logging/log4j

WORKDIR $BITBUCKET_HOME

# Expose HTTP and SSH ports
EXPOSE 7990
EXPOSE 7999

CMD ["/entrypoint.py", "--log=INFO"]
ENTRYPOINT ["/usr/bin/tini", "--"]

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends fontconfig openssh-client perl python3 python3-jinja2 tini \
    && apt-get clean autoclean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY bin/make-git.sh                                /
RUN /make-git.sh

ARG DOWNLOAD_URL=https://product-downloads.atlassian.com/software/stash/downloads/atlassian-bitbucket-${BITBUCKET_VERSION}.tar.gz

RUN groupadd --gid ${RUN_GID} ${RUN_GROUP} \
    && useradd --uid ${RUN_UID} --gid ${RUN_GID} --home-dir ${BITBUCKET_HOME} --shell /bin/bash ${RUN_USER} \
    && echo PATH=$PATH > /etc/environment \
    \
    && mkdir -p                                     ${BITBUCKET_INSTALL_DIR} \
    && curl -L --silent                             ${DOWNLOAD_URL} | tar -xz --strip-components=1 -C "${BITBUCKET_INSTALL_DIR}" \
    # Mitigation for the Log4j security vulnerabilities (CVE-2021-44228 & CVE-2021-45046)
    && rm -f ${BITBUCKET_ELASTICSEARCH_DIR}/lib/log4j-api-2.*.jar ${BITBUCKET_ELASTICSEARCH_DIR}/lib/log4j-core-2.*.jar ${BITBUCKET_INSTALL_DIR}/app/WEB-INF/lib/log4j-core-2.*.jar \
    && (curl -L --silent ${MAVEN_LOG4J_URL}/log4j-api/2.17.1/log4j-api-2.17.1.jar -o ${BITBUCKET_ELASTICSEARCH_DIR}/lib/log4j-api-2.17.1.jar || true) \
    && (curl -L --silent ${MAVEN_LOG4J_URL}/log4j-core/2.17.1/log4j-core-2.17.1.jar -o ${BITBUCKET_ELASTICSEARCH_DIR}/lib/log4j-core-2.17.1.jar || true) \
    && chmod -R "u=rwX,g=rX,o=rX"                   ${BITBUCKET_INSTALL_DIR}/ \
    && chown -R root.                               ${BITBUCKET_INSTALL_DIR}/ \
    && (chown -R ${RUN_USER}:${RUN_GROUP}           ${BITBUCKET_ELASTICSEARCH_DIR}/logs || true) \
    && chown -R ${RUN_USER}:${RUN_GROUP}            ${BITBUCKET_HOME}

VOLUME ["${BITBUCKET_HOME}"]

COPY exec-bitbucket-node.sh _exec-webapp.sh ${BITBUCKET_INSTALL_DIR}/bin/

COPY entrypoint.py \
     shared-components/image/entrypoint_helpers.py \
     shutdown-wait.sh /
COPY shared-components/support                      /opt/atlassian/support
