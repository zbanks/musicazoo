from musicazooTemplates import MusicazooShellCommandModule

class Fortune(MusicazooShellCommandModule):
    resources = ("audio")
    persistent = True
    keywords = ("popo", "police")
    command = ("police",)
    title = "Police Radio (via Crime Club)"
