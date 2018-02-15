import socket
import select
import time
import webbrowser

client_cache_dir = "./client_cache/"


def split_query(query):
    '''
    :type query str
    :param query:
    :return: dict
    '''

    schema, query = query.split("://", 1)
    port = 0
    if query.find(":") > 0:
        host, query = query.split(":", 1)
        port, query = query.split("/", 1)
    else:
        host, query = query.split("/", 1)

    return {"Schema": schema, "Host": host, "Port": port, "url": query}


def get(URL, proxy=None):
    '''
    :type URL str
    :param URL:
    :return:
    '''
    tcp_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.getprotobyname("tcp"))
    default_port = 80

    URL = split_query(URL)
    http_message = construct_request("GET", URL.get("Host"), URL.get("url"))

    if URL.get("Port"):
        default_port = int(URL.get("Port"))

    if proxy:
        host, port = proxy.split(":")
        tcp_soc.connect((host, int(port)))
    else:
        tcp_soc.connect((URL.get("Host"), default_port))

    tcp_soc.sendall(http_message)

    all_data = []
    timeout = 3
    print "waiting for response"
    ready = select.select([tcp_soc], [], [])[0]
    if ready:
        while True:
            data = tcp_soc.recv(1024)
            if data:
                all_data.append(data)
                continue
            break
    else:
        print "timed out"
        return None

    recv_time = time.time()

    payload = unpack_http_response(''.join(all_data)).get("payload")
    file = open("dummy.html","w+")
    file.write(payload)
    file.close()

    webbrowser.open_new_tab("dummy.html")

    return (''.join(all_data), recv_time)


def construct_request(method, host, URL):
    '''
    :type method: str
    :param method:
    :param data:
    :return:
    '''
    return method + " /" + URL + " HTTP/1.1\r\nHost: " + host + 2 * "\r\n"


def unpack_http_response(response):
    '''
    :type response str
    :param responce:
    :rtype dict
    :return:
    '''
    unpacked = dict()

    header, payload = response.split(2 * "\r\n", 1)
    if "\r\n" in header:
        status, directives = header.split("\r\n", 1)
        version, status = status.split(" ", 1)

        for entry in directives.split("\r\n"):
            key, value = entry.split(": ", 1)
            list_val = value.split(", ")

            unpacked.update({key: list_val})
    else:
        version, status = header.split(" ", 1)

    # status, response = response.split("\r\n", 1)

    unpacked.update({"version": version})
    unpacked.update({"status": status})

    # header, response = response.split(2 * "\r\n")
    unpacked.update({"payload": payload})

    return unpacked


# get("http://google.com/index.html")
# print get("http://127.0.0.1:80/index.html")
if __name__ == "__main__":
    print get("http://127.0.0.1:80/index.html", proxy="127.0.0.3:8085")[0]
