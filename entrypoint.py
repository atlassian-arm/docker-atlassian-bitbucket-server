#!/usr/bin/python3 -B

from entrypoint_helpers import env, str2bool, start_app
import logging
import os
import resource
import sys


RUN_USER = env['run_user']
RUN_GROUP = env['run_group']
BITBUCKET_INSTALL_DIR = env['bitbucket_install_dir']
BITBUCKET_HOME = env['bitbucket_home']


#################### Bitbucket + ES ####################

def start_full():
    logging.warning("Starting container with local ElasticSearch. "
                    "This is not recommended, and may cause issues with clean shutdown. "
                    "It is recommended to run a separate ElasticSearch container, and set 'ELASTICSEARCH_ENABLED' to false.")
    start_cmd = f"{ BITBUCKET_INSTALL_DIR }/bin/start-bitbucket.sh -fg"
    start_app(start_cmd, BITBUCKET_HOME, name='Bitbucket Server')


#################### Bitbucket only ####################

# The following is mostly extracted from the _start-webapp.sh script in the
# distribution. It is replicated here as we can't call that script directly,
# some of it doesn't make sense in a container context, and we need to hand full
# control of the process off to tini so signals are propagated correctly.  See
# DCD-1131 for some background.

JRE_HOME = os.getenv('JRE_HOME')
JAVA_BINARY = os.getenv('JAVA_BINARY')
JVM_MINIMUM_MEMORY = os.getenv('JVM_MINIMUM_MEMORY', '512m')
JVM_MAXIMUM_MEMORY = os.getenv('JVM_MAXIMUM_MEMORY', '1g');
UMASK = 0o27
MIN_FDS = 4096
LOG_DIR = f"{ BITBUCKET_HOME }/log"

LAUNCHER="com.atlassian.bitbucket.internal.launcher.BitbucketServerLauncher"

def create_log_dir():
    if not os.path.isdir(LOG_DIR):
        try:
            os.mkdir(LOG_DIR)
            return True
        except:
            logging.warning(f"{ LOG_DIR } could not be created. Permissions issue?")
            return False

def exists_or_exit(var):
    val = os.getenv(var)
    if val == None:
        logging.critical("JMX is enabled but { var } is not set.")
        sys.exit(1)
    return val

def file_exists_or_exit(var):
    fname = os.getenv(var)
    if fname == None:
        logging.critical("JMX is enabled but { var } is not set. The Bitbucket webapp was not started.")
        sys.exit(1)
    if not os.path.isfile(fname):
        logging.critical("JMX is enabled but { fname } is not present. The Bitbucket webapp was not started.")
        sys.exit(1)
    return fname

def gen_jmx_opts():
    JMX_REMOTE_AUTH = os.getenv('JMX_REMOTE_AUTH')
    if JMX_REMOTE_AUTH == None:
        return []

    JMX_OPTS = [f"-Dcom.sun.management.jmxremote.port={ os.getenv('JMX_REMOTE_PORT', '3333') }",
                f"-Djava.rmi.server.hostname={ os.getenv('RMI_SERVER_HOSTNAME', '') }",
                f"-Dcom.sun.management.jmxremote.rmi.port={ os.getenv('JMX_REMOTE_RMI_PORT', '') }"]

    if JMX_REMOTE_AUTH == 'password':
        logging.info("Using password JMX authentication, configuring ...")
        JMX_OPTS += [f"-Dcom.sun.management.jmxremote.password.file={ file_exists_or_exit('JMX_PASSWORD_FILE') }",
                     f"-Dcom.sun.management.jmxremote.ssl=false"]
        return JMX_OPTS

    elif JMX_REMOTE_AUTH == 'ssl':
        logging.info("Using SSL JMX authentication, configuring ...")
        JMX_OPTS += [f"-Djavax.net.ssl.keyStore={ file_exists_or_exit('JAVA_KEYSTORE') }",
                     f"-Djavax.net.ssl.keyStorePassword={ exists_or_exit('JAVA_KEYSTORE_PASSWORD') }",
                     f"-Djavax.net.ssl.trustStore={ file_exists_or_exit('JAVA_TRUSTSTORE') }",
                     f"-Djavax.net.ssl.trustStorePassword={ exists_or_exit('JAVA_TRUSTSTORE_PASSWORD') }",
                     f"-Dcom.sun.management.jmxremote.authenticate=false",
                     f"-Dcom.sun.management.jmxremote.ssl.need.client.auth=true"]
        return JMX_OPTS

    else:
        logging.critical("JMX authentication method (JMX_REMOTE_AUTH) was unknown.")
        sys.exit(1)

def start_bb_only():
    os.umask(UMASK)

    ulimit = resource.getrlimit(resource.RLIMIT_NOFILE)
    if ulimit[1] < MIN_FDS:
        logging.warning(f"Open file limit is { MIN_FDS }. You may experience problems under heavy load. "
                        "Increase it on the Docker command-line with --ulimit.")

    if not os.getenv('LANG'):
        os.environ['LANG'] = 'en_US.UTF-8'

    if not create_log_dir():
        logging.critical("Could not create log directory. The Bitbucket webapp was not started.")
        sys.exit(1)


    JAVA_OPTS = [f"-classpath", f"{ BITBUCKET_INSTALL_DIR }/app",
                 f"-Datlassian.standalone=BITBUCKET", f"-Dbitbucket.home={ BITBUCKET_HOME }", f"-Dbitbucket.install={ BITBUCKET_INSTALL_DIR }",
                 f"-Dfile.encoding=UTF-8", f"-Dsun.jnu.encoding=UTF-8",
                 f"-Djava.io.tmpdir={ BITBUCKET_HOME }/tmp", f"-Djava.library.path={ BITBUCKET_INSTALL_DIR }/lib/native:{ BITBUCKET_HOME }/lib/native",
                 f"-Xms{ JVM_MINIMUM_MEMORY }", f"-Xmx{ JVM_MAXIMUM_MEMORY }", f"-XX:+UseG1GC"]
    JAVA_OPTS += gen_jmx_opts()

    logging.info("Starting Bitbucket webapp")
    logging.info(str.join(" ", JAVA_OPTS + [LAUNCHER, "start", "--logging.console=true"]))
    os.execv(JAVA_BINARY, [JAVA_BINARY] + JAVA_OPTS + [LAUNCHER, "start", "--logging.console=true"])


#################### Go ####################

if str2bool(env['elasticsearch_enabled']) is False or env['application_mode'] == 'mirror':
    start_bb_only()
else:
    start_full()
