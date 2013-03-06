from musicazooTemplates import MusicazooShellCommandModule

class STFU(MusicazooShellCommandModule):
    resources = ()
    presistent = False
    keywords = ("stfu",)
    command = ("killall","mplayer")
    title = "STFU!"
    queue_html = "STFU!"
    playing_html = "STFU!"
