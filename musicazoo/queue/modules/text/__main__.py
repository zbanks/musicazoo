from musicazoo.queue import pymodule
import musicazoo.lib.graphics
import musicazoo.lib.vlc
import threading
import socket
import Tkinter
import time

import text2speech
import text2screen
import preprocessing

text2speech_engines = {
    'google':text2speech.google,
}

text2screen_engines = {
    'splash':text2screen.splash,
    'paragraph':text2screen.paragraph,
    'email':text2screen.email,
}

screen_preprocessors = {
}

speech_preprocessors = {
    'pronounce':preprocessing.pronounce,
    'pronounce_email':preprocessing.pronounce_email,
    'pronounce_fortune':preprocessing.pronounce_fortune,
}


class TextModule(pymodule.JSONParentPoller,threading.Thread):
    def __init__(self):
        super(TextModule, self).__init__()
        self.daemon=True
        self.fsg=musicazoo.lib.graphics.FullScreenGraphics()
        self.fsg.sync(self.start)
        self.fsg.run()
        self.shutdown()

    def shutdown(self):
        self.running=False
        self.update_rm()
        self.close()
        self.join()

    def compute_tts(self):
        self.speech = text2speech_engines[self.text2speech](self.speech_text,**self.text2speech_args)
        self.vlc_i = musicazoo.lib.vlc.Instance()
        self.vlc_mp = self.vlc_i.media_player_new()
        self.vlc_media = self.vlc_i.media_new_path(self.speech.name)
        self.vlc_mp.set_media(self.vlc_media)
        self.tts_ready=True

    def cmd_init(self,text,duration=None,text2screen='splash',text2speech='google',screen_preprocessor=None,speech_preprocessor='pronounce',text2screen_args={},text2speech_args={}):
        self.text2speech = text2speech
        self.text2speech_args = text2speech_args
        self.text = text
        self.text2screen = text2screen
        self.speech_preprocessor = speech_preprocessor
        self.screen_preprocessor = screen_preprocessor

        self.connection.send_update({"cmd":"set_parameters","args":{"parameters":{
            "text":text,
            "duration":duration,
            "text2screen":text2screen,
            "text2speech":text2speech,
            "screen_preprocessor":screen_preprocessor,
            "speech_preprocessor":speech_preprocessor,
            "text2screen_args":text2screen_args,
            "text2speech_args":text2speech_args,
        }}})

        if screen_preprocessor:
            self.screen_text = screen_preprocessors[screen_preprocessor](text)
        else:
            self.screen_text = text

        text2screen_engines[text2screen](self.fsg,self.screen_text,**text2screen_args)

        self.speech = None

        if text2speech:
            if speech_preprocessor:
                self.speech_text = speech_preprocessors[speech_preprocessor](text)
            else:
                self.speech_text = text

            self.tts_ready=False
            self.tts_done=False
            self.tts_play=False
            self.tts_wait_ready()

            t=threading.Thread(target=self.compute_tts)
            t.daemon=True
            t.start()

        if duration is None:
            if self.text2speech is None:
                self.duration = 10
            else:
                self.duration = 3
        else:
            self.duration = duration

        self.remaining_time=self.duration

    def cmd_rm(self):
        self.fsg.sync(self.fsg.over)
        self.running=False

    def tts_wait_ready(self):
        if self.tts_ready:
            if self.tts_play:
                self.vlc_mp.play()
            self.tts_wait_over()
        else:
            self.fsg.after(100,self.tts_wait_ready)

    def tts_wait_over(self):
        if self.vlc_mp.get_state() in [musicazoo.lib.vlc.State.Ended,musicazoo.lib.vlc.State.Stopped,musicazoo.lib.vlc.State.Error] and self.tts_play:
            self.speech.close()
            self.tts_done=True
            self.over_handle = self.fsg.after(int(self.remaining_time*1000),self.fsg.over)
            self.start_time=time.time()
        else:
            self.fsg.after(100,self.tts_wait_over)

    def cmd_resume(self):
        if self.text2speech and not self.tts_done:
            if self.tts_ready:
                self.vlc_mp.play()
            self.tts_play=True
        else:
            self.over_handle = self.fsg.after(int(self.remaining_time*1000),self.fsg.over)
            self.start_time=time.time()

    def cmd_play(self):
        self.cmd_resume()
        self.fsg.sync(self.fsg.show)

    def cmd_pause(self):
        if self.text2speech and not self.tts_done:
            if self.tts_ready:
                self.vlc_mp.pause()
            self.tts_play=False
        else:
            self.fsg.after_cancel(self.over_handle)
            self.remaining_time -= time.time()-self.start_time
            if self.remaining_time <= 0:
                self.fsg.sync(self.fsg.over)

    def cmd_suspend(self):
        self.cmd_pause()
        self.fsg.sync(self.fsg.hide)

    def run(self):
        self.running=True
        try:
            while self.running:
                self.handle_one_command()
        except socket.error:
            if self.running:
                self.fsg.sync(self.fsg.over)
                raise

    commands = {
        'init':cmd_init,
        'rm':cmd_rm,
        'play':cmd_play,
        'suspend':cmd_suspend,
        'do_pause':cmd_pause,
        'do_resume':cmd_resume,
    }

mod = TextModule()

