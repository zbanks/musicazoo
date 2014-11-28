available_ports = set(range(5600,5700))

def get_free_port():
    return available_ports.pop()

def release_port(p):
    global available_ports
    available_ports.add(p)
