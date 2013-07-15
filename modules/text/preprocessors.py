import re

def no_preprocessor(text):
	return text

def pronounce_email(text):
    text = pronunciation(text)
    text = "Email {}".format(text) #Email From:...
    return text

def pronounce_fortune(text):
    text = pronunciation(text)
    subs = (
        (r'^Q:', 'Question: '),
        (r'^A:', 'Answer: '),
    )
    for reg, repl in subs:
        text = re.sub(reg, repl, text, flags=re.IGNORECASE)
    return text

def pronunciation(text):
    subs = (
        (r'mit\.edu', " mit dot edju "),
        (r'<3', " wub "),
        (r'zbanks', " z banks "),
        (r'#([A-Za-z])',r'hash tag \1'),
    )
    text = remove_urls(text)
    text = parse_mit_numbers(text)
    for reg, repl in subs:
        text = re.sub(reg, repl, text, flags=re.IGNORECASE)
    return text

def remove_urls(text):
	text=re.sub(r'[A-Za-z]+://[^ ]+',r'link',text)
	text=re.sub(r'[^ ]+\.[^ ]+/[^ ]*',r'link',text)
	return text

def parse_mit_numbers(text):
	subs=(
		(r'(\d{1,2})[-.]00([^ ]+)',r'\1 double oh \2'), # 16-0010 2.00gokart
		(r'(\d{1,2})-0(\d\d)',r'\1 oh \2'), # 1-010
		(r'(\d{1,2})\.0(\d)(\d)',r'\1 oh \2 \3'), # 3.091
		(r'(\d{1,2})\.00',r'\1 hundred'), # 6.00
		(r'(\d{1,2})\.0(\d)',r'\1 oh \2'), # 6.01
		(r'(\d{1,2})[-.](\d00)',r'\1 \2'), # 54-100, 1.100
		(r'(\d{1,2})-(\d\d)00',r'\1 \2 hundred'), # 54-1800
		(r'(\d{1,2})[-.](\d{1,2})(\d\d)',r'\1 \2 \3'), # 6-120 6.131
		(r'(\d{1,2})-(\d)',r'\1 \2'), # 10-4
	)
	for reg, repl in subs:
		text = re.sub(reg, repl, text, flags=re.IGNORECASE)
	return text

if __name__=='__main__':
	print pronunciation('16-0010 2.007 1-010 3.091 6.01 54-100 1.100 54-1800 6-120 6.131 6.00 10-4')
