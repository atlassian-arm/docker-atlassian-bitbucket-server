#!/usr/bin/env bash

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


# The following 2 settings control the minimum and maximum memory allocated to the Java virtual machine.
# For larger instances, the maximum amount will need to be increased.
#
if [ -z "${JVM_MINIMUM_MEMORY}" ]; then
    JVM_MINIMUM_MEMORY=512m
fi
if [ -z "${JVM_MAXIMUM_MEMORY}" ]; then
    JVM_MAXIMUM_MEMORY=1g
fi

# Uncommenting the following will set the umask for the webapp. It can be used to override the default
# settings for the service user if they are not sufficiently secure.
#
umask 0027

MAX_OPEN_FILES=6192
if [ $(ulimit -n) -lt ${MAX_OPEN_FILES} ]; then
    echo -e "\nThe current open files limit is set to less than $MAX_OPEN_FILES\nAttempting to increase limit..."
    if ulimit -n $MAX_OPEN_FILES; then
        echo -e "\tLimit increased to $MAX_OPEN_FILES open files"
    else
        echo -e "\n Couldn't increase file limit to $MAX_OPEN_FILES\nTrying a lower number..."
        MAX_OPEN_FILES=4096
        if ulimit -n $MAX_OPEN_FILES; then
          echo -e "\tLimit increased to $MAX_OPEN_FILES open files"
        else
          echo -e "Warning: Open file limit could not be increased. You may experience problems under heavy load"
        fi
    fi
fi

if [ ! -d "$BITBUCKET_HOME/log" ]; then
    mkdir -p "$BITBUCKET_HOME/log"
    if [ $? -ne 0 ]; then
        echo "$BITBUCKET_HOME/log could not be created. Permissions issue?"
        echo "The Bitbucket webapp was not started"
        exit 1
    fi
fi

source $BIN_DIR/set-jmx-opts.sh
if [ $? -ne 0 ]; then
    exit 1
fi

# Java 11 no longer supports setting sun.jnu.encoding via the command line. With nothing set in the environment
# to influence sun.jnu.encoding it will typically default to ANSI_X3.4-1968 on Linux.
if [ -z "$LANG" ] ; then
    export LANG="en_US.UTF-8"
fi

JVM_LIBRARY_PATH="$INST_DIR/lib/native;$BITBUCKET_HOME/lib/native"

BITBUCKET_ARGS="-Datlassian.standalone=BITBUCKET -Dbitbucket.home=$BITBUCKET_HOME -Dbitbucket.install=$INST_DIR"
JVM_FILE_ENCODING_ARGS="-Dfile.encoding=UTF-8 -Dsun.jnu.encoding=UTF-8"
JVM_JAVA_ARGS="-Djava.io.tmpdir=$BITBUCKET_HOME/tmp -Djava.library.path=$JVM_LIBRARY_PATH"
JVM_MEMORY_ARGS="-Xms$JVM_MINIMUM_MEMORY -Xmx$JVM_MAXIMUM_MEMORY -XX:+UseG1GC"
JVM_REQUIRED_ARGS="$JVM_MEMORY_ARGS $JVM_FILE_ENCODING_ARGS $JVM_JAVA_ARGS"

JAVA_OPTS="-classpath $INST_DIR/app $JAVA_OPTS $BITBUCKET_ARGS $JMX_OPTS $JVM_REQUIRED_ARGS $JVM_SUPPORT_RECOMMENDED_ARGS"
LAUNCHER="com.atlassian.bitbucket.internal.launcher.BitbucketServerLauncher"

echo -e "\nStarting Bitbucket webapp at http://localhost:${bitbucket.http.port}${bitbucket.context}"

exec $JAVA_BINARY $JAVA_OPTS $LAUNCHER start --logging.console=true
