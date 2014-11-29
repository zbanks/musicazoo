if __name__ != '__main__':
    # If name is not main then this was imported for use in the queue process

    import musicazoo.queue.module as module

    class Youtube(module.Module):
        TYPE_STRING='youtube'
        process = ['python',__file__] # The sub-process to execute is itself
        # tell me that isn't cute
else:
    # If name is main then this is the sub-process
    # admittedly, it does feel very fork-esque
    import musicazoo.lib.packet as packet
    import musicazoo.queue.pymodule as pymodule

    conn=pymodule.ParentConnection()

    def poller():
        while True:
            print "MOD RECV",conn.recv_cmd()
            conn.send_resp(packet.good())

    import sys
    import threading

    t=threading.Thread(target=poller)
    t.daemon=True
    t.start()

    import time
    while True:
        time.sleep(1)
    
    print "QUITTING"
    conn.close()
