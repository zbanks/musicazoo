import json
import os
import pkg_resources

json_path = pkg_resources.resource_filename("musicazoo", '../settings.json')

settings_file=open(json_path)

settings = json.load(settings_file)

globals().update(settings)
