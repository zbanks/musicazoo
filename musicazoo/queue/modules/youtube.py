import musicazoo.queue.module

class Youtube(musicazoo.queue.module.Module):
    TYPE_STRING='youtube'
    process = ['python',__file__]

if __name__ == '__main__':
    import socket
    import sys
    import time

    host = sys.argv[1]
    cmd_port = int(sys.argv[2])
    update_port = int(sys.argv[3])
    cs=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    us=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    print "connecting to",host,cmd_port,update_port
    cs.connect((host,cmd_port))
    us.connect((host,update_port))
    print "connected!"
    time.sleep(10)
    print "closing..."
    cs.close()
    us.close()
    print "done. exiting..."
