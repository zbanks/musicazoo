import os
import requests
import tempfile

def google(text):
    text=unicode(text)

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

    sndfile=tempfile.NamedTemporaryFile()

    total=len(chunks)
    for idx in range(total):
        text=chunks[idx]
        mp3=requests.get('http://translate.google.com/translate_tts',params={'q':text,'tl':'en','idx':idx,'total':total,'textlen':len(text)},headers={'User-Agent':'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'})
        sndfile.write(mp3.content)
    
    #f=open(os.path.join(os.path.dirname(__file__),'silence.mp3'))
    #silence=f.read()
    #f.close()
    #sndfile.write(silence)

    sndfile.flush()
    os.fsync(sndfile)
    return sndfile

