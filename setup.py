#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Musicazoo',
    version='5.0',
    description='Modular media player',
    author='Zach Banks',
    author_email='zbanks@mit.edu',
    url='https://github.com/zbanks/musicazoo',
    packages=['musicazoo', 'musicazoo.wsgi', 'musicazoo.queue', 'musicazoo.volume', 'musicazoo.lib', 'musicazoo.nlp'],
    scripts=[
        "bin/musicazoo", "bin/mz"
    ],
    package_dir = {
        'musicazoo.wsgi': 'musicazoo/wsgi'
    },
    package_data={
        'musicazoo.wsgi': ['static/*.html', 'static/assets/*.js', 'static/assets/*.otf', 'static/assets/*.css', 'static/assets/images/*']
    }
)
