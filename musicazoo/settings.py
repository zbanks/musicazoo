import json
import os

json_path = os.path.join(os.path.dirname(__file__),"../settings.json")

settings_file=open(json_path)

settings = json.load(settings_file)

globals().update(settings)
