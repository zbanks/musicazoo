from musicazooTemplates import MusicazooShellCommandModule

def trimToLength(s,n):
    if len(s) <= n:
        return s
    if n < 3:
        return "."*n
    else:
        return "%s..." % s[:n-3]

class Say(MusicazooShellCommandModule):
    resources = ("audio",)
    presistent = False
    keywords = ("say",)
    command = ("say",)
    title = "Say"
    queue_html = "Say"
    playing_html = "Say"

    def __init__(self,json):
        super(Say,self).__init__(json)
        self.title = 'Say "%s"' % trimToLength(self.arg, 20)
        self.queue_html = self.title
        self.playing_html = self.title
