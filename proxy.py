import http_server
import socket
import os
import datetime
import time
import select
import http_header

root_dir = "./cache/"
cc_file_name = " cache-control.txt"
content_type = "Content-Type: text/html\r\n"
CRLF = "\r\n"
timeout = 2


def handle_request(tcp_socket):
    """
    :type socket.socket tcp_socket
    :param tcp_socket:
    :return:
    """
    # get request and unpack it
    request = tcp_socket.recv(1024)
    unpacked_req = http_header.unpack_http_request(request)

    try:
        # load the cache control file. this also checks if the file is present( each file has a cache control file, if it cannot be opened the file is not in the cache)
        cache_loc = root_dir + unpacked_req.get("Host") + unpacked_req.get("URL")
        cc = load_cache_control_file(cache_loc + cc_file_name)
        recv_time, methods = cc

        # check if the file must be revalidated
        if must_reval(unpacked_req, cc):
            print "has to revalidate"
            # if this returns false that means that the revalidated function has already sent a request to the client
            if not revalidate(tcp_socket, unpacked_req.get("Host"), request, float(recv_time)):
                return

        # read file and send it with its cache-control directives
        file = open(cache_loc).read()

        message = http_header.http_codes[200] + content_type
        # set directives
        for key in methods.keys():
            message += key + ": " + ", ".join(methods.get(key)) + CRLF

        print(message)
        tcp_socket.sendall(message + CRLF + file)
    except IOError:
        # get a relay the request to the origin server and send the response back to the client while caching it
        origin_resp, recv_time = send_and_receive(unpacked_req.get("Host"), request, tcp_socket)
        print(origin_resp)
        tcp_socket.send(origin_resp)
        cache(recv_time, request, origin_resp)

    finally:

        tcp_socket.close()


def load_cache_control_file(path):
    """
    :type path: str

    Reads the cache control file and returns its information
    :param path: string of the cache-control file path

    :return: a tuple of (
        received time,
        method describing the cache-control directives
        value(s) of of the directive
    :raises IOError if the file does not exist or its not properly formatted
    """
    try:
        cc = open(path).read()
        recv_time, cc = cc.split("\n", 1)

        methods = dict()
        lines = cc.split("\n")
        for line in lines:
            method, values = line.split(": ", 1)
            values = values.split(", ")
            methods.update({method: values})

        return recv_time, methods
    except:
        print "could not open cc: " + path
        raise IOError


def is_stale(recv_time, methods):
    """
    Calculates whether or not he file is stale.
    :param recv_time: time of receiving in seconds
    :param method: string one of ("Cache-Control","Expires")
    :param values: cache control values
    :return: tuple (
        seconds by which the file has expired (if the value is negative, it mean that that many second are left to expiration),
        age of the file)
    """
    # calculating age
    age = time.time() - float(recv_time)
    exp_by = None

    # if there isn't a max-age in the cache control directive will need to look at the Expires directive to see if it's stale
    exp_needed = True

    if methods.get("Cache-Control"):
        for val in methods.get("Cache-Control"):
            if "max-age" in val:
                max = int(val.split("=")[1])
                exp_by = age - max
                exp_needed = False
                break

    if exp_needed and methods.get("Expires"):
        exp_date = datetime.datetime.strptime(methods.get("Expires")[0], "%a, %d %b %Y %H:%M:%S %Z")
        exp_by = (datetime.datetime.now() - exp_date).total_seconds()

    return (exp_by, age)


def must_reval(unpacked_req, cc):
    """
    Checks if a cached file needs to be revalidated. checks if the server requires it or if the page is fresh enough for the client
    :type unpacked_req dict
    :param unpacked_req:
    :param cc:
    :return:
    """
    # unpack the cache-control tuple(cc)
    recv_time, methods = cc
    # get the saved file's cache-control directives
    cc_values = methods.get("Cache-Control")

    # get a list of cache-control directives from the request
    req_cc_vals = unpacked_req.get("Cache-Control")
    if req_cc_vals: cc_values += req_cc_vals

    # in this case a revalidation is compulsory even if fresh
    if "no-cache" in cc_values:
        return True

    # get the age of the file and by how much it has expired
    exp_by, age = is_stale(recv_time, methods)
    if not exp_by:  # has no expiration date so no need to revalidate
        return False

    # if exp_by > 0 that means that the cache has expired
    if exp_by > 0:
        # revalidation is compulsory in this case
        if "must-revalidate" in cc_values:
            return True

        elif req_cc_vals:
            # check if there is a max-stale directive in the request
            for val in req_cc_vals:
                if "max-stale" in val:
                    # if the directive has an assigned value check if it's satisfied
                    if "=" in val:
                        max_stale = int(val.split("=")[1])
                        return max_stale < exp_by
                    # else the client would take the cache
                    else:
                        return False
    elif req_cc_vals:
        # check if there is a min-fresh or max-age directive in the request
        for val in req_cc_vals:
            if "min-fresh" in val:
                min_fresh = int(val.split("=")[1])
                return min_fresh < (exp_by * -1)

            elif "max-age" in val:
                max = int(val.split("=")[1])
                return age > max
    # if there are no directives that control the freshness of the cache no need to revalidate
    return False


def revalidate(tcp_socket, host, request, recv_time):
    """
    :type tcp_socket socket.socket
    :param tcp_socket:
    :return: true if the copy of the page in the cache is fresh before revalidation
    """

    # stick a "if modified " header in the http request
    header, payload = request.split(2 * CRLF, 1)
    if_head = "If-Modified-Since: " + datetime.datetime.fromtimestamp(recv_time).strftime(
        "%a, %d %b %Y %H:%M:%S %Z") + "GMT" + CRLF
    request = header + CRLF + if_head + CRLF + payload

    # connect to origin and get a validation
    origin_resp, recv_time = send_and_receive(host, request, tcp_socket)
    if "304" not in http_header.unpack_http_response(origin_resp).get("status"):
        tcp_socket.sendall(origin_resp)
        cache(recv_time, request, origin_resp)
        return False  # the copy was not fresh before revalidation

    return True


def cache(recv_time, client_request, origin_response):
    """
    Caches a response from an origin server. Executed only if the directives in the request and response allow it
    :type origin_response str
    :param origin_response:
    :return:
    """
    # unpack the these two
    origin_response = http_header.unpack_http_response(origin_response)
    client_request = http_header.unpack_http_request(client_request)

    # getting them together only so that it can be chacked for "no-store"
    cc = []
    if origin_response.get("Cache-Control"): cc + origin_response.get("Cache-Control")
    if client_request.get("Cache-Control"): cc + client_request.get("Cache-Control")

    # no caching should be performed in one of these cases
    if "no-store" in cc or "private" in cc or origin_response.get("status") == '404':
        return

    else:
        host = client_request.get("Host")
        # make directory is it does not exist
        try:
            os.stat(root_dir + host)
        except:
            os.mkdir(root_dir + host)

        cc_file = open(root_dir + host + client_request.get("URL") + " cache-control.txt", "w+")
        cc_file.write(str(recv_time) + "\n")

        # saves the way that determens the freshness of the file
        if origin_response.get("Cache-Control"):
            cc_file.write("Cache-Control: " + ", ".join(origin_response.get("Cache-Control")))
        if "max-age" not in origin_response.get("Cache-Control") and origin_response.get("Expires"):
            cc_file.write("Expires: " + origin_response.get("Expires"))

        cc_file.close()

        file = open(root_dir + host + client_request.get("URL"), "w+")
        file.write(origin_response.get("payload"))
        file.close()


def send_and_receive(host, request, tcp_socket=None, timeout=2):
    """
    Send a request to the host and return the response
    :param host:
    :param request:
    :param tcp_socket: socket to which the errors of the function are going to be sent
    :param timeout:
    :return:
    """

    origin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostbyname(host)

    # connect to origin
    if not origin_socket.connect_ex((host, 80)) == 0:
        if tcp_socket: tcp_socket.send("HTTP/1.1 400 Bad Request" + 2 * CRLF)
        return None

    # send
    origin_socket.send(request)

    # receive response
    ready = select.select([origin_socket], [], [])
    if not ready:
        if tcp_socket: tcp_socket.send("HTTP/1.1 504 Gateway Timeout" + 2 * CRLF)
        return None
    else:
        origin_resp = origin_socket.recv(1024)
        recv = time.time()
        return origin_resp, recv


if __name__ == "__main__":
    http_server.start_server('127.0.0.3', 8085, handle=handle_request)
