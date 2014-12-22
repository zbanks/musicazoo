import json
import os
import pkg_resources

json_path = pkg_resources.resource_filename("musicazoo", '../settings.json')

settings_file=open(json_path)

settings = json.load(settings_file)

if 'log_database' in settings:
    settings['log_database'] = os.path.expandvars(settings['log_database'])

globals().update(settings)
