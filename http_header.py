http_codes = {200: "HTTP/1.1 200 OK\r\n", 404: "HTTP/1.1 404 Not Found\r\n\r\n",
              304: "HTTP/1.1 304 Not Modified\r\n\r\n"}
multivalued = ["Cache-Control"]
CRLF = "\r\n"


def unpack_http_request(packet):
    unpacked = dict()

    request, header = str(packet).split("\r\n", 1)

    request_keys = ["Method", "URL", "Version"]
    request = request.split(" ")

    # the -2 removes the empty strings between and after the last 2 "\r\n" that designate the end of the header
    header = header.split(CRLF)[:-2]

    for i in range(len(request_keys)):
        unpacked.update({request_keys[i]: request[i]})

    for entry in header:
        key, values = entry.split(": ", 1)

        if key in multivalued:
            values = values.split(", ")

        unpacked.update({key: values})

    return unpacked


def unpack_http_response(response):
    '''
    :type response str
    :param responce:
    :rtype dict
    :return:
    '''
    unpacked = dict()

    header, payload = response.split(2 * CRLF, 1)
    if CRLF in header:
        status, directives = header.split(CRLF, 1)
        version, status = status.split(" ", 1)

        for entry in directives.split(CRLF):
            key, value = entry.split(": ", 1)

            if key in multivalued:
                value = value.split(", ")

            unpacked.update({key: value})
    else:
        version, status = header.split(" ", 1)

    unpacked.update({"version": version})
    unpacked.update({"status": status})

    unpacked.update({"payload": payload})

    return unpacked
