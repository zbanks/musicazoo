import re

def no_preprocessor(text):
	return text

def pronounciation(text):
    subs = (
        (r'mit\.edu', " mit dot edju "),
        (r'<3', " wub "),
        (r'zbanks', " z banks ")
    )
    text = remove_urls(text)
    for reg, repl in subs:
        text = re.sub(reg, repl, text, re.IGNORECASE)
	return text

def remove_urls(text):
	text=re.sub(r'[A-Za-z]+://[^ ]+',r'link',text)
	text=re.sub(r'www\.[^ ]+\.[^ ]+',r'link',text)
	return text


if __name__=='__main__':
	print remove_urls('This is a link: www.google.com')
