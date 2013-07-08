import re

def no_preprocessor(text):
	return text

def casual(text):
    text = re.sub(r'(?:\w*://)?(?:.*?\.)?(?:([a-zA-Z-1-9]*)\.)?([a-zA-Z-1-9]*\.[a-zA-Z]{1,})', " link ", text)
    subs = (
        (r'(\w+://)?(.*?\.)?(([a-zA-Z-1-9]*)\.)?([a-zA-Z-1-9]*\.[a-zA-Z]{1,})', " link "),
        (r'<3', " wub "),
        (r'zbanks', " z banks "),
        (r'mit[.]edu', " mit dot edju ")
    )
    for reg, repl in subs:
        text = re.sub(reg, repl, text, re.IGNORECASE)
	return text
