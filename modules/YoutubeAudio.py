from Youtube import Youtube
import re

cookie_file="/var/tmp/youtube-dl-cookies.txt"

# This class plays /only/ the audio from a youtube video
# Note -- Not currently sure if this works yet
class YoutubeAudio(Youtube):
    keywords = ("ytaudio",)
    resources = ("audio",)
    command = ("mplayer","-slave","-framedrop","-cache","8192","-vo","null",
               "-fs","-cookies","-cookies-file",cookie_file)
   
    def match(input_str):
        return False
