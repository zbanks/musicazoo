import urllib,urllib2
import os

def google(obj):
	text=unicode(obj.textToSpeak)

	limit=99
	whitespace=['.',',',':',';','--','-','\t','\r\n','\n\r','\n','\r',' ']

	chunks=[]
	while True:
		if len(text)<=limit:
			chunks.append(text)
			break
		space=-1
		for char in whitespace:
			space=text.rfind(char,0,limit)
			if space>=0:
				space+=len(char)
				break
		if space<0:
			space=limit
		chunks.append(text[0:space])
		if len(text)==space:
			break
		text=text[space:]

	total=len(chunks)
	for idx in range(total):
		text=chunks[idx]
		request=urllib2.Request('http://translate.google.com/translate_tts',urllib.urlencode({'q':text,'tl':'en','idx':idx,'total':total,'textlen':len(text)}))
		request.add_header('User-Agent','Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11')
		opener = urllib2.build_opener()
		mp3=opener.open(request).read()
		obj.sndfile.write(mp3)
	
	f=open(os.path.join(os.path.dirname(__file__),'silence.mp3'))
	silence=f.read()
	f.close()
	obj.sndfile.write(silence)

	obj.sndfile.flush()
	os.fsync(obj.sndfile)
	return True

def no_text2speech(obj):
	return False
