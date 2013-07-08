import re

def no_preprocessor(text):
	return text

def casual(text):
    text = re.sub(r'(?:\w*://)?(?:.*?\.)?(?:([a-zA-Z-1-9]*)\.)?([a-zA-Z-1-9]*\.[a-zA-Z]{1,})', " link ", text)
    subs = (
        (r'mit[.]edu', " mit dot edju "),
        (r'(\w+://)?(.*?\.)?(([a-zA-Z-1-9]*)\.)?([a-zA-Z-1-9]*\.[a-zA-Z]{1,})', " link "),
        (r'<3', " wub "),
        (r'zbanks', " z banks ")
    )
    for reg, repl in subs:
        text = re.sub(reg, repl, text, re.IGNORECASE)
	return text

def remove_urls(text):
	text=re.sub(r'[A-Za-z]+://[^ ]+',r'link',text)
	text=re.sub(r'www\.[^ ]+\.[^ ]+',r'link',text)
	return text


if __name__=='__main__':
	print remove_urls('This is a link: www.google.com')
