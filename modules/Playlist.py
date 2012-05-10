from musicazooTemplates import MusicazooShellCommandModule
import re

# This class is for playing music or video playlists on mplayer
class Playlist(MusicazooShellCommandModule):
    resources = ("audio",)
    persistent = True
    keywords = ("pls", "playlist")
    command = ("mplayer", "-vo", "null", "-playlist")

    @staticmethod
    def match(input_str):
        return not not re.search(r"[.](pls|m3u|asx)", input_str.strip())
