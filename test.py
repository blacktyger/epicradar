import errno
import socket
import time


def ping_address(host, timeout=2):
    if ':' in host:
        old_host = host.split(':')
        host = old_host[0]
        port = int(old_host[1])
        print(host, port)
    else:
        port = 3415

    s = socket.socket()
    s.settimeout(timeout)
    result = False
    start = time.time()
    try:
        s.connect((host, port))
        s.close()
        result = True
        end = time.time()
        ms = 1000 * (end - start)
        return result, int(ms)
    except (socket.gaierror, socket.timeout) as e:
        print(e)

    return result


print(ping_address('51pool.online:4616'))