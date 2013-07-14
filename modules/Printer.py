from musicazooTemplates import MusicazooShellCommandModule

class Printer(MusicazooShellCommandModule):
    resources = ()
    persistent = False
    keywords = ("printer", "enis")
    command = ("echo_enis.sh",)
    title = "Enis"
