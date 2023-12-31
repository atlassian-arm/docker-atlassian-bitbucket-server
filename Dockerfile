ARG BASE_IMAGE=eclipse-temurin:11
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
ENV SEARCH_ENABLED                                  true
ENV APPLICATION_MODE                                default
ENV JRE_HOME                                        /opt/java/openjdk
ENV JAVA_BINARY                                     ${JRE_HOME}/bin/java

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

COPY bin/make-git.sh \
     bin/post-unpack-cleanup.sh \
     bin/log4shell-vulnerability-fix.sh \
     /
RUN /make-git.sh

ARG DOWNLOAD_URL=https://product-downloads.atlassian.com/software/stash/downloads/atlassian-bitbucket-${BITBUCKET_VERSION}.tar.gz

RUN groupadd --gid ${RUN_GID} ${RUN_GROUP} \
    && useradd --uid ${RUN_UID} --gid ${RUN_GID} --home-dir ${BITBUCKET_HOME} --shell /bin/bash ${RUN_USER} \
    && echo PATH=$PATH > /etc/environment \
    \
    && mkdir -p                                     ${BITBUCKET_INSTALL_DIR} \
    && curl -L --silent                             ${DOWNLOAD_URL} | tar -xz --strip-components=1 -C "${BITBUCKET_INSTALL_DIR}" \
    && /post-unpack-cleanup.sh                      ${BITBUCKET_INSTALL_DIR} \
    && /log4shell-vulnerability-fix.sh \
    && chmod -R "u=rwX,g=rX,o=rX"                   ${BITBUCKET_INSTALL_DIR}/ \
    && chown -R root.                               ${BITBUCKET_INSTALL_DIR}/ \
    && chown -R ${RUN_USER}:${RUN_GROUP}            ${BITBUCKET_INSTALL_DIR}/*search/logs \
    && chown -R ${RUN_USER}:${RUN_GROUP}            ${BITBUCKET_HOME}

VOLUME ["${BITBUCKET_HOME}"]

COPY exec-bitbucket-node.sh _exec-webapp.sh ${BITBUCKET_INSTALL_DIR}/bin/

COPY entrypoint.py \
     shared-components/image/entrypoint_helpers.py \
     shutdown-wait.sh                               /
COPY shared-components/support                      /opt/atlassian/support
