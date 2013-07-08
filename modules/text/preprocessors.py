import re

def no_preprocessor(text):
	return text

def pronounciation(text):
    subs = (
        (r'mit\.edu', " mit dot edju "),
        (r'<3', " wub "),
        (r'zbanks', " z banks "),
        (r'(\d{1,2})-(\d{1,2})00',r'\1 \2 hundred'),
        (r'(\d{1,2})-(\d{1,2})(\d\d)',r'\1 \2 \3'),
    )
    text = remove_urls(text)
    for reg, repl in subs:
        text = re.sub(reg, repl, text, flags=re.IGNORECASE)
    return text

def remove_urls(text):
	text=re.sub(r'[A-Za-z]+://[^ ]+',r'link',text)
	text=re.sub(r'[^ ]+\.[^ ]+/[^ ]*',r'link',text)
	return text


if __name__=='__main__':
	print pronounciation('Reuse in 1-290 and 13-1800 google.com www.google.com www.google.com/ http://google.com')
