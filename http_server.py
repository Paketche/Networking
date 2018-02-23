import socket
import datetime
import os
import http_header

cache_control = "Cache-Control: max-age=100, must-revalidate\r\n"
content_type = "Content-Type: text/html\r\n"
root_dir = "."
CRLF = "\r\n"


def handle_request(tcp_socket):
    packet = tcp_socket.recv(1024)
    packet = http_header.unpack_http_request(packet)

    response = ""
    try:
        # check for conditional requests
        if_mod = packet.get("If-Modified-Since")
        if if_mod:
            since = datetime.datetime.strptime(if_mod, "%a, %d %b %Y %H:%M:%S %Z")
            if not is_file_modified(root_dir + packet.get("URL"), since):
                response += http_header.http_codes[304]
                return

        # send a 200 response
        file = open("." + packet.get("URL")).read()
        response += http_header.http_codes[200] + content_type + cache_control + CRLF + file
    except IOError:
        # send a 404 response
        response = http_header.http_codes[404]
    finally:
        print response
        tcp_socket.send(response)
        tcp_socket.close()


def start_server(address, port, handle=handle_request):
    """
    Creates a new instance of server
    """
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.getprotobyname("tcp"))

    tcp_socket.bind((address, port))
    tcp_socket.listen(5)

    while True:
        print "listening"

        conn, _ = tcp_socket.accept()
        handle(conn)


def is_file_modified(path, date):
    """
    Checks if the file on path has been modified since date
    :param path:
    :param date:
    :return:
    """
    try:
        stat = os.stat(path)
        mod = datetime.datetime.fromtimestamp(stat.st_mtime)

        return mod > date
    except IOError, e:
        raise IOError


if __name__ == "__main__":
    start_server("127.0.0.1", 80)
