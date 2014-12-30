#!/usr/bin/env python

import fnmatch
import glob
import os
import sys

from setuptools import setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name='musicazoo',
    version='5.1.2',
    description='Modular media player',
    author='Zach Banks',
    author_email='zbanks@mit.edu',
    url='https://github.com/zbanks/musicazoo',
    packages=[
        'musicazoo', 
        'musicazoo.wsgi', 
        'musicazoo.queue', 
        'musicazoo.queue.modules', 
        'musicazoo.volume', 
        'musicazoo.lib', 
        'musicazoo.nlp', 
        'musicazoo.top',
        'musicazoo.lux',
    ],
    download_url="https://github.com/zbanks/musicazoo/tarball/5.1.2",
    zip_safe=False,
    install_requires=required,
    scripts=[
        "bin/musicazoo", 
        "bin/mz", 
        "bin/mz_push_email",
        "bin/mz_push_fortune",
    ],
    package_dir = {
        'musicazoo.wsgi': 'musicazoo/wsgi',
    },
    package_data={
        'musicazoo': [
            "../supervisord.conf", 
            "../settings.json"
        ],
        'musicazoo.wsgi': [
            '../../static/*.html', 
            '../../static/settings.json', 
            '../../static/assets/*.js', 
            '../../static/assets/*.otf', 
            '../../static/assets/*.css', 
            '../../static/assets/images/*'
        ],
    },
)
