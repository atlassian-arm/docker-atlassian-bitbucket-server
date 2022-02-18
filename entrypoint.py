#!/usr/bin/python3 -B

from entrypoint_helpers import env, str2bool, exec_app
import logging

RUN_USER = env['run_user']
RUN_GROUP = env['run_group']
BITBUCKET_INSTALL_DIR = env['bitbucket_install_dir']
BITBUCKET_HOME = env['bitbucket_home']
SEARCH_ENABLED = env.get('search_enabled') or env.get('elasticsearch_enabled')
APPLICATION_MODE = env.get('application_mode')

if str2bool(SEARCH_ENABLED) is False or APPLICATION_MODE == 'mirror':
    # When running standalone use a stripped version of the startup
    # scripts to ensure shutdown works correctly. See the script for
    # details.
    start_cmd = [f"{BITBUCKET_INSTALL_DIR}/bin/exec-bitbucket-node.sh"]
else:
    logging.warning("######################################################################")
    logging.warning("Starting Bitbucket with embedded Elasticsearch. Note that this is\n" \
                    "not a recommended configuration and is known to have issues with\n" \
                    "clean shutdown. Ideally Elasticsearch should be started in a separate\n" \
                    "container/pod.")
    logging.warning("######################################################################")

    start_cmd = [f"{BITBUCKET_INSTALL_DIR}/bin/start-bitbucket.sh", "-fg"]

exec_app(start_cmd, BITBUCKET_HOME, name='Bitbucket')
