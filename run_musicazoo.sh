#!/bin/bash

#export PYTHONPATH=`pwd`

#SCONF="supervisord.conf"
SCONF=$(python -c "import pkg_resources; print pkg_resources.resource_filename('musicazoo', '../supervisord.conf')")

supervisord -c $SCONF
