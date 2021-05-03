#!/usr/bin/env bash

##############################################################################
#
# This, along with `_exec-webapp.sh`, is a stripped-down version of
# the startup scripts shipped with Bitbucket DC for use in the Docker
# images when starting standalone. The key changes are:
#
# * All ElasticSearch startup has been removed.
#
# * Any subshells or application startup is called with `exec` rather
#   than starting a child process. This is necessary to ensure that
#   signals are propogated to the applcation.
#
##############################################################################

# BIN_DIR & INST_DIR will be fully qualified, not relative
pushd `dirname $0` > /dev/null
export BIN_DIR=`pwd`
popd > /dev/null
export INST_DIR=$(dirname "$BIN_DIR")

source $BIN_DIR/set-jre-home.sh &&
    source $BIN_DIR/set-bitbucket-home.sh &&
    source $BIN_DIR/set-bitbucket-user.sh
if [ $? -ne 0 ]; then
    # One of the setup scripts failed. Don't try to start any processes
    echo -e "\nStartup has been aborted"
    exit 1
fi

if [ -z "$BITBUCKET_USER" ] || [ $(id -un) == "$BITBUCKET_USER" ]; then
    echo "Starting Atlassian Bitbucket as the current user"
elif [ $UID -ne 0 ]; then
    echo Atlassian Bitbucket has been installed to run as $BITBUCKET_USER. Use "sudo -u $BITBUCKET_USER $0"
    echo to start as that user.
    exit 1
else
    echo "Starting Atlassian Bitbucket as dedicated user $BITBUCKET_USER"
fi


if [ -z "$BITBUCKET_USER" ] || [ $(id -un) == "$BITBUCKET_USER" ]; then
    echo "Starting Atlassian Bitbucket as the current user"
    exec $BIN_DIR/_exec-webapp.sh

elif [ $UID -ne 0 ]; then
    echo Atlassian Bitbucket has been installed to run as $BITBUCKET_USER. Use "sudo -u $BITBUCKET_USER $0"
    echo to start as that user.
    exit 1
else
    echo "Starting Atlassian Bitbucket as dedicated user $BITBUCKET_USER"

    exec $SU -l $BITBUCKET_USER <<EOS
        # Copy over the environment, the poor man's way
        export BIN_DIR="$BIN_DIR"
        export BITBUCKET_HOME="$BITBUCKET_HOME"
        export INST_DIR="$INST_DIR"
        export JAVA_BINARY="$JAVA_BINARY"
        export JAVA_KEYSTORE="$JAVA_KEYSTORE"
        export JAVA_KEYSTORE_PASSWORD="$JAVA_KEYSTORE_PASSWORD"
        export JAVA_TRUSTSTORE="$JAVA_TRUSTSTORE"
        export JMX_PASSWORD_FILE="$JMX_PASSWORD_FILE"
        export JMX_REMOTE_AUTH="$JMX_REMOTE_AUTH"
        export JMX_REMOTE_PORT="$JMX_REMOTE_PORT"
        export JRE_HOME="$JRE_HOME"
        export JVM_MAXIMUM_MEMORY="$JVM_MAXIMUM_MEMORY"
        export JVM_MINIMUM_MEMORY="$JVM_MINIMUM_MEMORY"
        export JVM_SUPPORT_RECOMMENDED_ARGS="$JVM_SUPPORT_RECOMMENDED_ARGS"
        export RMI_SERVER_HOSTNAME="$RMI_SERVER_HOSTNAME"
        export JMX_REMOTE_RMI_PORT="$JMX_REMOTE_RMI_PORT"
        export LANG="$LANG"

        # Change working directory
        cd $PWD
        exec $BIN_DIR/_exec-webapp.sh
EOS
fi
