from musicazooTemplates import MusicazooShellCommandModule

class Email(MusicazooShellCommandModule):
    resources = ("screen", "audio")
    persistent = False
    keywords = ()
    command = ("/usr/local/bin/received_email.sh",)
    title = "Email"
    playing_html = "Email"
    queue_html = "Email"

    def __init__(self, json):
        self.command = self.command + (json["file"].encode("ascii", "ignore"), json["address"].encode("ascii", "ignore"))
        self.from_address = json["address"]
        self.title = "Email from %s" % json["address"]

        self.playing_html = self.title[:]
        self.queue_html = self.title[:]

        print self.title
        print self.command
        self._initialize(json)
