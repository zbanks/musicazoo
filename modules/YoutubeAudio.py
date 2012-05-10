from Youtube import Youtube
import re

# This class plays /only/ the audio from a youtube video
# Note -- Not currently sure if this works yet
class YoutubeAudio(Youtube):
    keywords = ("ytaudio",)
    resources = ("audio",)
    command = ("/usr/local/bin/playyoutube","-vo","null")
    
    def match(input_str):
        return False
