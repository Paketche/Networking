import socket


class Host:
    socket = None
    msg = "stuff"

    def __init__(self, msg):
        print("creating an IPv4 stream socket")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msg = msg
        print("connecting it to localhost at port 80")
        self.connect(socket.gethostname())
        print ("sending message")
        self.send()
        print(self.receive())

    def connect(self, address):
        self.socket.connect((address, 8085))

    def send(self):
        totalSent = 0
        while totalSent < len(self.msg):
            sent = self.socket.send(self.msg[totalSent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalSent += sent

    def receive(self):
        chunks = []
        bytes_rec = 0
        while bytes_rec < len(self.msg):
            chunk = self.socket.recv(2048)
            if chunk == '':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_rec = bytes_rec + len(chunk)
        return ''.join(chunks)


host = Host("pasti")
