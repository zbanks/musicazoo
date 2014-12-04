import math

try:
    import alsaaudio
except:
    alsaaudio = None

try:
    import osax
except:
    osax = None

exp=0.6 # approximate

def human_to_computer(val):
	return int(100*(float(val)/100)**exp)

def computer_to_human(val):
	return int(100*(float(val)/100)**(1.0/exp))


class Volume(object):
    def __init__(self):
        if alsaaudio:
            self.mixer=alsaaudio.Mixer(control='PCM')
        elif osax:
            self.mixer = osax.OSAX()
        else:
            print "Unable to control volume"

    def get_vol(self):
        if alsaaudio:
            v=self.mixer.getvolume()[0]
        elif osax:
            v=self.mixer.get_volume_settings()[osax.k.output_volume]
        else:
            v=0
	return computer_to_human(v)

    def set_vol(self,vol):
	v=human_to_computer(vol)
        if alsaaudio:
            self.mixer.setvolume(v)
        elif osax:
            self.mixer.set_volume(output_volume=v)
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
