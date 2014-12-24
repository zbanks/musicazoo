import json

class FileLogger(object):
    def __init__(self,filename):
        self.filename=filename

    def log(self,msg):
        f=open(self.filename,"a")
        with f:
            json.dump(msg,f)
            f.write('\n')
