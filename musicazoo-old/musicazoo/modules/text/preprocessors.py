import re

def no_preprocessor(text):
	return text

def pronounce_email(text):

	# Sender: say canonical name if available
	sender=text['sender']
	m=re.match(r'(.+) <(.+)>',sender)
	if m:
		sender=m.groups()[0]

	subject=text['subject']
	subject=re.sub(r'^re:',r'reply to ',subject,flags=re.IGNORECASE)
	subject=re.sub(r' re:',r' reply to ',subject,flags=re.IGNORECASE)
	subject=re.sub(r'^fwd:',r'forward, ',subject,flags=re.IGNORECASE)
	subject=re.sub(r' fwd:',r' forward, ',subject,flags=re.IGNORECASE)

	body=text['body']
	body=clean_email(body)

	speech=u"Email from {0} . Subject: {1} . {2}".format(sender,subject,body)
	speech = pronunciation(speech)
	return speech

def clean_email(text):
	text=re.sub(r'--+ Forwarded message --+\n[\s\S]+?\n\n',r'',text,flags=re.IGNORECASE)
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
        (r'mit\.edu', " mit dot edju ",re.IGNORECASE),
        (r'<3', " wub ",None),
        (r'zbanks', " z banks ",re.IGNORECASE),
        (r'#([A-Za-z])',r'hash tag \1',re.IGNORECASE),
        (r'MIT',r' M I T ',None),
        (r'[\*\~\^\<\>\[\]]',r'',None),
        (r'__*', r'_', None),
        (r'--*', r'-', None),
    )
    text = remove_urls(text)
    text = parse_mit_numbers(text)
    for reg, repl, flags in subs:
        if flags:
                text = re.sub(reg, repl, text, flags=flags)
        else:
                text = re.sub(reg, repl, text)
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

def display_email(text):
	sender=text['sender']
	subject=text['subject']
	body=text['body']
	body=clean_email(body)
	# Optionally modify the text that is shown here
	return {'sender':sender,'subject':subject,'body':body}

if __name__=='__main__':
	print pronunciation('MIT is a universty')
