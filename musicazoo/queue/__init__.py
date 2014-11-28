import musicazoo.lib.service as service

class Queue(service.JSONCommandService):
    port=5580

    def __init__(self,modules):
        print "Queue started."
        self.modules_available=dict([(m.TYPE_STRING,m) for m in modules])
        self.queue=[]
        self.old_queue=[]
        self.last_uid=-1
        self.queue_lock=service.Lock()
        service.JSONCommandService.__init__(self)

    def get_uid(self):
        self.last_uid += 1
        return self.last_uid

    @service.coroutine
    def ask_module(self,uid,parameters):
        uid=int(uid)
        d=dict(self.queue)
        if uid not in d:
            raise Exception("Module identifier not in queue")
        raise service.Return(d[uid].get_multiple_parameters(parameters))

    @service.coroutine
    def ask_background(self,uid,parameters):
        uid=int(uid)
        if self.bg is None:
            raise Exception("No background")
        (bg_uid,bg_obj)=self.bg
        if bg_uid != uid:
            raise Exception("Background identifier doesn't match current background")
        raise service.Return(bg_obj.get_multiple_parameters(parameters))

    @service.coroutine
    def modules_available(self):
        raise service.Return(self.modules_available.keys())

    @service.coroutine
    def backgrounds_available(self):
        raise service.Return(self.backgrounds_available.keys())

    # queue command
    @service.coroutine
    def get_queue(self,parameters={}):
        l=[]
        for (uid,obj) in self.queue:
            d={'uid':uid,'type':obj.TYPE_STRING}
            if obj.TYPE_STRING in parameters:
                d['parameters']=obj.get_multiple_parameters(parameters[obj.TYPE_STRING])
            l.append(d)
        raise service.Return(l)

    # bg command
    @service.coroutine
    def get_bg(self,parameters={}):
        if self.bg is None:
            return None
        (uid,obj)=self.bg

        d={'uid':uid,'type':obj.TYPE_STRING}
        if obj.TYPE_STRING in parameters:
            d['parameters']=obj.get_multiple_parameters(parameters[obj.TYPE_STRING])
        raise service.Return(d)

    @service.coroutine
    def tell_module(self,uid,cmd,args={}):
        uid=int(uid)
        d=dict(self.queue)
        if uid not in d:
            raise Exception("Module identifier not in queue")
        result = yield d[uid].tell(cmd,args)
        raise service.Return(result)

    @service.coroutine
    def tell_background(self,uid,cmd,args={}):
        uid=int(uid)
        if self.bg is None:
            raise Exception("No background")
        (bg_uid,bg_obj)=self.bg
        if bg_uid != uid:
            raise Exception("Background identifier doesn't match current background")
        result = yield bg_obj.tell(cmd,args)
        raise service.Return(result)

    @service.coroutine
    def add(self,type,args={}):
        uid=self.get_uid()
        if type not in self.modules_available:
            raise Exception("Unrecognized module name")
        mod_inst=self.modules_available[type](lambda:self.rm([uid]))
        yield mod_inst.new(args)
        with (yield self.queue_lock.acquire()):
            self.queue.append((uid,mod_inst))
            yield self.queue_updated()
        raise service.Return({'uid':uid})

    # TODO harden this
    @service.coroutine
    def queue_updated(self):
        cur_uids=[uid for (uid,obj) in self.queue]
        to_remove=[obj.remove() for (uid,obj) in self.old_queue if uid not in cur_uids and obj.alive]
        if len(self.queue) > 0:
            uid,obj=self.queue[0]
            if not obj.is_on_top:
                to_play=[obj.play()]
            else:
                to_play=[]
        to_suspend=[obj.suspend() for (uid,obj) in self.queue[1:] if obj.is_on_top]
        self.old_queue=self.queue

        futures=to_remove+to_suspend+to_play
        yield futures

    @service.coroutine
    def rm(self,uids):
        with (yield self.queue_lock.acquire()):
            self.queue=[(uid,obj) for (uid,obj) in self.queue if uid not in [int(u) for u in uids]]
            yield self.queue_updated()

## EVERYTHING BELOW HERE IS TRASH
    def set_bg(self,type,args={}):
        uid=self.backgrounds.get_uid()
        mod_inst=self.backgrounds.instantiate(type,self,uid,args)
        if self.bg is not None:
            (bg_uid,bg_obj)=self.bg
            bg_obj.close()
        self.bg=(uid,mod_inst)
        self.bg_visible=False
        self.update_bg()
        return {'uid':uid}

    def update_bg(self,parameters={}):
        if self.bg is None:
            return
        
        (bg_uid,bg_obj)=self.bg
        if self.cur is None:
            if not self.bg_visible:
                bg_obj.show()
                self.bg_visible=True
        else:
            if self.bg_visible:
                bg_obj.hide()
                self.bg_visible=False

    def mv(self,uids):
        newqueue=[]
        oldqueue=[uid for (uid,obj) in self.queue]
        d=dict(self.queue)
        for uid in uids:
            uid=int(uid)
            if uid in oldqueue:
                oldqueue.remove(uid)
                newqueue.append(uid)
        newqueue+=oldqueue
        self.queue=[(uid,d[uid]) for uid in newqueue]

    commands = {
#        'rm':rm,
#        'mv':mv,
        'add':add,
        'queue':get_queue,
        'bg':get_bg,
#        'set_bg':set_bg,
        'modules_available':modules_available,
        'backgrounds_available':backgrounds_available,
        'tell_module':tell_module,
        'tell_background':tell_background,
        'ask_module':ask_module,
        'ask_background':ask_background,
    }

