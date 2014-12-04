#!/bin/bash

export PYTHONPATH=`pwd`
supervisord -c supervisord.conf
