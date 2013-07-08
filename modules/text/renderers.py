import graphics
import Tkinter
import time
import vlc

def splash(obj):
	fsg=graphics.FullScreenGraphics()
	c=Tkinter.Canvas(fsg,width=fsg.width,height=fsg.height,bg='black',highlightthickness=0)
	c.pack()
	(x,y) = fsg.center()
	text=c.create_text((x,y), text=obj.textToShow, fill="white", justify=Tkinter.CENTER, font=("Helvetica",72))
	
	if obj.hasSound:
		vlc_i = vlc.Instance()
		vlc_mp = vlc_i.media_player_new()
		vlc_media=vlc_i.media_new_path(obj.sndfile.name)
		vlc_mp.set_media(vlc_media)
		vlc_mp.play()
		while vlc_mp.get_length()==0:
			time.sleep(0.1)
		obj.duration+=float(vlc_mp.get_length())/1000

	fsg.show()
	start=time.time()
	while True:
		obj.time=time.time()-start
		if obj.time>=obj.duration:
			break
		time.sleep(0.1)

	if obj.hasSound:
		vlc_mp.stop()
	fsg.close()
