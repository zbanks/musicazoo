from mzbot import MZBot
import requests
import subprocess

class FortuneBot(MZBot):
    def send_fortune(self):
        try:
            fortune_text = subprocess.check_output(['fortune', '-s'])
            data = {'cmd': 'add',
                    'args': {
                        'type': 'text',
                        'args': {
                            'text': fortune_text,
                            'text_preprocessor': 'none',
                            'speech_preprocessor': 'pronounciation',
                            'text2speech': 'google',
                            'renderer': 'splash', #FIXME
                            'duration': 5,
                            'short_description': "Fortune",
                            'long_description': fortune_text
                        }
                    }
                }
            return self.doCommands([data])
        except CalledProcessError:
            pass

if __name__ == "__main__":
    fb = FortuneBot("http://localhost/cmd")
    print fb.send_fortune()
