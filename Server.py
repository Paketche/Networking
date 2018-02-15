import socket
import ast


class Server:
    socket = None

    def __init__(self):
        print("creating an IPv4 stream socket")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("binding the socket to the local host with http service (80)")
        self.socket.bind(("127.8.8.8", 8000))
        print("listening to one socket")
        self.socket.listen(1)

        while True:
            print "listening on port" + str(self.socket.proto)
            # accept connections from outside
            print("waiting for a socket to be accepted")
            (clientsocket, address) = self.socket.accept()
            print("socket at address" + str(clientsocket.getpeername()))
            # now do something with the clientsocket
            # in this case, we'll pretend this is a threaded server
            print "receiving message from it"
            message = self.receive(clientsocket, 1024)
            print

            # self.send(clientsocket, message)

    def send(self, clientSocket, msg):
        totalSent = 0
        while totalSent < len(msg):
            sent = clientSocket.send(msg[totalSent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalSent += sent

    def receive(self, clientSocket, length):
        chunks = []
        bytes_rec = 0
        clientSocket.settimeout(5)
        while bytes_rec < length:
            print "waiting on chunk"
            try:
                chunk = clientSocket.recv(min(length - bytes_rec, 2048))
                print "got chunk"
            except socket.timeout:
                break
            if chunk == b'':
                break
            chunks.append(chunk)
            bytes_rec = bytes_rec + len(chunk)
        return b''.join(chunks)


server = Server()
