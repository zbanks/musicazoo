#!/bin/bash

#export PYTHONPATH=`pwd`

export SHMOOZE_SETTINGS=$1

#SCONF="supervisord.conf"
SCONF=$(python -c "import pkg_resources; print pkg_resources.resource_filename('musicazoo', '../supervisord.conf')")
#SETTINGS=$(python -c "import pkg_resources; print pkg_resources.resource_filename('musicazoo', '../settings.json')") 

echo "Supervisor configuration: $SCONF";
echo "Musicazoo settings.json:  $SHMOOZE_SETTINGS";

supervisord -n -c $SCONF;
