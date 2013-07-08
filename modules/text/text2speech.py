import urllib,urllib2

def google(obj):
	request=urllib2.Request('http://translate.google.com/translate_tts',urllib.urlencode({'q':obj.textToSpeak,'tl':'en'}))
	request.add_header('User-Agent','Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11')
	opener = urllib2.build_opener()
	mp3 = opener.open(request).read()
	obj.sndfile.write(mp3)
	obj.sndfile.flush()
	return True

def no_text2speech(obj):
	return False
