try:
    import alsaaudio
except:
    alsaaudio = None

try:
    import osax
except:
    osax = None


class Volume(object):
    def __init__(self):
        if alsaaudio:
            self.mixer=alsaaudio.Mixer()
        elif osax:
            self.mixer = osax.OSAX()
        else:
            print "Unable to control volume"

    def get_vol(self):
        if alsaaudio:
            return int(self.mixer.getvolume()[0])
        elif osax:
            return self.mixer.get_volume_settings()[osax.k.output_volume]
        else:
            return 0

    def set_vol(self,vol):
        if alsaaudio:
            self.mixer.setvolume(vol)
        elif osax:
            self.mixer.set_volume(output_volume=vol)
        else:
            pass

    commands={
        'set_vol':set_vol
    }

    parameters={
        'vol':get_vol
    }

    constants={
        'class':'volume'
    }
