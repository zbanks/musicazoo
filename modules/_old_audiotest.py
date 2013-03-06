modules = ("AudioTest",)

class AudioTest:
    def __init__(self, json):
        self.json = json
        self.id = self.json["id"]
        self.resources = ("audio", )

    def run(self, cb):
        print "Running audio test"
        cb()

    def pause(self, cb):
        print "Pausing audio test"
        cb()

    def unpause(self, cb):
        print "Unpausing audio test"
        cb()

    def kill(self):
        print "Killing audio test"

    def status(self):
        output = {}
        output["id"] = self.id
        output["resources"] = self.resources
        output["persistent"] = False
        output["title"] = "Audio Test"
        return output
