#!/usr/bin/python3 -B

from entrypoint_helpers import env, str2bool, start_app
import logging


RUN_USER = env['run_user']
RUN_GROUP = env['run_group']
BITBUCKET_INSTALL_DIR = env['bitbucket_install_dir']
BITBUCKET_HOME = env['bitbucket_home']


def start_full():
    logging.warning("Starting container with local ElasticSearch. "
                 "This is not recommended, and may cause issues with clean shutdown. "
                 "It is recommended to run a separate ElasticSearch container, and set 'elasticsearch_enabled' to false.")
    start_cmd = f"{BITBUCKET_INSTALL_DIR}/bin/start-bitbucket.sh -fg"
    start_app(start_cmd, BITBUCKET_HOME, name='Bitbucket Server')


def start_bb_only():
    # Interim
    start_cmd = f"{BITBUCKET_INSTALL_DIR}/bin/start-bitbucket.sh -fg --no-search"
    start_app(start_cmd, BITBUCKET_HOME, name='Bitbucket Server')


if str2bool(env['elasticsearch_enabled']) is False or env['application_mode'] == 'mirror':
    start_full()
else:
    start_bb_only()
