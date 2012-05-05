from musicazooTemplates import MusicazooShellCommandModule

class Fortune(MusicazooShellCommandModule):
    resources = ("screen", "audio")
    persistent = False
    keywords = ("fortune", "joke", "quote")
    command = ("say-fortune",)
    title = "Fortune"
    queue_html = "Fortune"
    playing_html = "Fortune"
