#import time
import threading
import struct

FMT='llHHI'

EV_KEY=0x01
EV_LED=0x11
BTN_TRIGGER = 0x120
LED_MISC=0x08

class USButton(threading.Thread):
	def __init__(self,fd,callback=None):
		threading.Thread.__init__(self)
		self.evw=open(fd,'wb')
		self.evr=open(fd,'rb')
		self.daemon=True
		self.btnstate=False
		self.callback=callback
		self.start()

	def run(self):
		while True:
			l=struct.unpack(FMT,self.evr.read(24))
			if l[2]==EV_KEY and l[3]==BTN_TRIGGER:
				self.btnstate=l[4]
				if self.callback is not None:
					self.callback(self.btnstate)

	def set_led(self,state):
		#tv_sec,tv_usec=divmod(time.time(), 1.0)
		(tv_sec,tv_usec)=(0,0)
		packet=[long(tv_sec),long(tv_usec*1000000),EV_LED,LED_MISC,int(state)]
		self.evw.write(struct.pack(FMT,*packet))
		self.evw.flush()

	def get_button(self):
		return self.btnstate

	button=property(fget=get_button)
	led=property(fset=set_led)

