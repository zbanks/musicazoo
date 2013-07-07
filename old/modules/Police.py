from musicazooTemplates import MusicazooShellCommandModule

class Police(MusicazooShellCommandModule):
    resources = ("audio")
    persistent = True
    keywords = ("popo", "police")
    command = ("police",)
    title = "Police Radio (via Crime Club)"
