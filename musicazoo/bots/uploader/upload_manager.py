import threading
import magic
import mzbot
import time
import os

class UploadManager:
	def __init__(self,my_url,mz_url):
		self.uid=0
		self.served_media={}
		self.magic=magic.Magic(flags=magic.MAGIC_MIME)
		self.my_url=my_url
		self.mz_url=mz_url

	def getUID(self):
		u=self.uid
		self.uid+=1
		return u

	def add(self,tempfilename,nicefilename=None):
		uid=self.getUID()
		mime=self.magic.from_file(tempfilename)
		uf=UploadedFile(self,uid,tempfilename,nicefilename,finished_hook=lambda:self.rm(uid),mime_type=mime)
		self.served_media[uid]=uf

	def get(self,uid):
		if uid not in self.served_media:
			return None
		return self.served_media[uid]

	def rm(self,uid):
		if uid not in self.served_media:
			return
		uf=self.served_media[uid]
		os.unlink(uf.tempfilename)
		del self.served_media[uid]

class UploadedFile(threading.Thread,mzbot.MZBot):
	def __init__(self,manager,uid,tempfilename,nicefilename=None,finished_hook=None,mime_type=None):
		self.manager=manager
		self.uid=uid
		self.tempfilename=tempfilename
		self.nicefilename=nicefilename
		self.finished_hook=finished_hook
		self.mime_type=mime_type

		mzbot.MZBot.__init__(self,manager.mz_url)
		threading.Thread.__init__(self)

		self.daemon=True
		self.start()

	def run(self):
		url=self.getURL()
		arglist={'url':url,'short_description':'Upload'}
		if self.nicefilename:
			arglist['long_description']=self.nicefilename+' (Upload)'
		print arglist
		result=self.doCommands([{'cmd':'add','args':{'type':'netvid','args':arglist}}])[0]
		self.assert_success(result)
		added_uid=result['result']['uid']
		while True:
			result=self.doCommands([{'cmd':'cur'},{'cmd':'queue'}])
			self.assert_success(result)

			open_things=result[1]['result']
			if 'result' in result[0]:
				open_things.append(result[0]['result'])

			still_playing=False
			for thing in open_things:
				if thing['uid']==added_uid:
					still_playing=True
			if not still_playing:
				break
			time.sleep(10)
		print "Video over"

		#time.sleep(3600) # sleep for an hour before deleting video
		self.finished_hook()

	def getURL(self):
		return self.manager.my_url+"/media/"+str(self.uid)

