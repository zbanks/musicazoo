# commands.py
# Zach Banks <zbanks@mit.edu>
# AMP commands for musicazoo dispatch (server/client)

from twisted.protocols import amp
import amptypes

# Exceptions
class ModuleError(Exception):
    pass

# Server-side commands

class PushModule(amp.Command):
    arguments = [("module", amp.String()), ("args", amp.ListOf(amp.String()))]
    response = [("id", amp.String())]
    errors = {ModuleError: "ModuleError",
              NotImplementedError: "NotImplementedError" }

class MessageModule(amp.Command):
    arguments = [("id", amp.String()), ("message", amp.String()), ("jsondata", amp.String())]
    response = [("response", amp.String())]
    errors = {ModuleError: "ModuleError",
              NotImplementedError: "NotImplementedError" }

class Reload(amp.Command):
    arguments = []
    response = []
    errors = { Exception: "Exception" }

class RemoveActivity(amp.Command):
    arguments = [("id", amp.String())]
    response = []
    errors = { ModuleError: "ModuleError" }

class RemoveAll(amp.Command):
    arguments = [("id", amp.String())]
    response = []
    errors = { ModuleError: "ModuleError" }

class Status(amp.Command):
    arguments = []
    response = [("volume", amp.Integer()),
                ("playing", amp.ListOf(amp.AmpList(
                    [("id", amp.String()),
                     ("module", amp.String()),
                     ("jsondata", amp.String())]
                ))), ("queue", amp.ListOf(amp.AmpList(
                    [("id", amp.String()),
                     ("module", amp.String()),
                     ("jsondata", amp.String())]
                )))]
    errors = { ModuleError: "ModuleError" }
    
