# module_list.py
# Zach Banks <zbanks@mit.edu>
# Class to load/reload/call musicazoo modules
# TODO: better error handling, better logging

import os
import sys
import imp

MODULES_DIR = "/etc/musicazoo/modules/"

class ModuleList(object):
    def __init__(self, modules_dir=MODULES_DIR):
        self.modules_dir = modules_dir
        self.modules = {}
        self.reload()

    def exists(self, name):
        return self.modules.has_key(name.lower())

    def get(self, name):
        return self.modules[name.lower()]

    def available(self, name):
        return self.modules.keys()

    def reload(self):
        for filename in os.listdir(self.modules_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                filepath = os.path.join(self.modules_dir, filename)
                name = filename[:-3] # Name of module, minus .py
                try:
                    module = imp.load_source(name, filepath)
                    if "modules" in dir(module):
                        for mname in module.modules:
                            if mname in dir(module):
                                self.modules[mname.lower()] = module.__dict__[mname]
                                print >> sys.stderr, "Imported module %s from %s" % (mname.lower(), filename)
                            else:
                                print >> sys.stderr, "No class named %s in module %s.py" % (mname, mname)
                    else:
                        if name in dir(module):
                            self.modules[name.lower()] = module.__dict__[name]
                            print >> sys.stderr, "Imported module %s from %s" % (name.lower(), filename)
                        else:
                            print >> sys.stderr, "No class named %s in module %s.py" % (name, name)
                except Exception, e:
                    print >> sys.stderr, "Error loading module %s: %s" % (name, e)
                    print >> sys.stderr, e#.message()

