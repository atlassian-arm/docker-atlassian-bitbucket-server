#!/bin/bash

##############################################################################
#
# This script will initiate a clean shutdown of the application, and
# then wait for the process to finish before returning. This is
# primarily intended for use in environments that provide an orderly
# shutdown mechanism, in particular the Kubernetes `preStop` hook.
#
# This script will wait for the process to exit indefinitely; however
# most run-time tools (including Docker and Kubernetes) have their own
# shutdown timeouts that will send a SIGKILL if the grace period is
# exceeded.
#
##############################################################################

# Bitbucket handles SIGTERM correctly, so use the supplied signal helper
echo "Shutdown: Sending TERM signal to the application and waiting..."
/opt/atlassian/support/send-sig.sh TERM wait
