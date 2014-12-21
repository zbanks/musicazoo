#!/bin/bash

#export PYTHONPATH=`pwd`

#SCONF="supervisord.conf"
SCONF=$(python -c "import pkg_resources; print pkg_resources.resource_filename('musicazoo', '../supervisord.conf')")
SETTINGS=$(python -c "import pkg_resources; print pkg_resources.resource_filename('musicazoo', '../settings.json')")

echo "Supervisor configuration: $SCONF";
echo "Musicazoo settings.json:  $SETTINGS";

supervisord -n -c $SCONF;
