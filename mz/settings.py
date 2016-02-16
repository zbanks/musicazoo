import sys
import json

class SettingsError(Exception):
    pass

def load_from_arg(arg=1):
    if len(sys.argv) <= arg:
        raise SettingsError("Not enough arguments, expected settings file as argument {}".format(arg))

    fn = sys.argv[arg]

    with open(fn, "r") as f:
        settings = json.load(f)

    return settings
