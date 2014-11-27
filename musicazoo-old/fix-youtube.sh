#!/bin/bash

pip install --upgrade youtube-dl
supervisorctl restart musicazoo:mzserver
