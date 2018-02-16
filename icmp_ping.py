#!/usr/bin/python
# -*- coding: UTF-8 -*-

import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages

m_format = "bbHHh"
ip_header_size = 20

error_messages = {"30": "Destination network unreachable", "31": "Destination host unreachable",
                  "110": "TTL expired in transit"}


class Timeout(Exception):
    def __init__(self, message="Request timed out"):
        self.message = message


# class IdMismatch(Exception):
#     def __init__(self, message="ID's do not match"):
#         self.message = message


class ConnectionNotEstablished(Exception):
    def __init__(self, message="Connection could not be established"):
        self.message = message


class MessageNotSent(Exception):
    def __init__(self, message="Message could not be sent"):
        self.message = message


# class DestinationUnreachable(Exception):
#     def __init__(self, message="Destination is unreachable"):
#         self.message = message


# class TTL_expired(Exception):
#     def __init__(self, message="TTL has expired"):
#         self.message = message


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = ord(string[count + 1]) * 256 + ord(string[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    if sys.platform == 'darwin':
        answer = socket.htons(answer) & 0xffff
    else:
        answer = socket.htons(answer)

    return answer


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    err_mess = ""

    try:

        ready = select.select([icmpSocket], [], [], timeout)[0]
        if ready:
            data, addr = icmpSocket.recvfrom(1024)
            recv_time = time.time()
        else:
            raise socket.timeout

        ip_header = data[:ip_header_size]
        ip_header = unpack_ip_header(ip_header)

        icmp_mess = data[ip_header_size:]
        icmp_mess = unpack_icmp_header(icmp_mess, m_format)

        if ip_header['src'] != destinationAddress:
            err_mess = error_messages.get(icmp_mess["type"] + icmp_mess["code"])

        elif icmp_mess['identifier'] != ID:
            err_mess = "reply id mismatch"

        return {"src": ip_header["src"], "length": int(ip_header["length"]), "recv_time": recv_time,
                "TTL": int(ip_header['TTL']), "type": int(icmp_mess['type']), "err_mess": err_mess}
    except socket.timeout:
        raise Timeout()


def sendOnePing(icmpSocket, destinationAddress, port, ID):
    # Build ICMP header
    packet = construct_icmp_header(m_format, ID)

    # # Connect to the other side
    # if icmpSocket.connect_ex((destinationAddress, port)):
    #     raise ConnectionNotEstablished()

    # Send packet using socket
    if not icmpSocket.sendto(packet, (destinationAddress, port)):
        raise MessageNotSent()

    # Record time of sending
    recv_time = time.time()
    return recv_time


def doOnePing(destinationAddress, port, timeout, TTL=None):
    ID = 1
    # 1. Create ICMP socket
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
    if TTL: icmp_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)

    try:
        # 2. Call sendOnePing function
        send_time = sendOnePing(icmp_socket, destinationAddress, port, ID)
        # 3. Call receiveOnePing function
        response = receiveOnePing(icmp_socket, destinationAddress, ID, timeout)

        # 5. Return total network delay
        delay = round((response['recv_time'] - send_time) * 1000, 3)
        response.update({"delay": delay})

        return response
    except(MessageNotSent, Timeout) as e:
        raise e
    finally:
        icmp_socket.close()


def ping(host, port=80, timeout=1, ping_count=4):
    delays = []
    packets_lost = 0
    # it is expected that all messages would be sent and if not the this would be decremented in the loop
    msg_sent = ping_count

    # 1. Look up hostname, resolving it to an IP address
    try:
        ip_address = socket.gethostbyname(str(host))
    except:
        print "Ping request could not find host ", host, " Please check the name and try again."
        sys.exit(0)

    print"Pinging", host, "[", ip_address, "] just for fun"
    try:
        for i in range(ping_count):
            try:
                response = doOnePing(ip_address, port, timeout)

                if response['type'] == 3:
                    msg_sent -= 1

                print "Reply from " + response['src'] + ": ",
                if not response['type']:
                    print "bytes=" + str(response['length']), "time=" + str(response['delay']) + "ms", "TTL=" + str(
                        response['TTL']),

                print response['err_mess']

                # print "Reply from " + response['src'] + ": " + (
                #     "bytes=" + response['length'] + "time=" + response['delay'] + "ms TTL=" + response['TTL'] if
                #     not response['type'] else "") + response['err_mess']

                delays.append(response['delay'])
                time.sleep(0.1)
            except MessageNotSent as e:
                print e.message + os.linesep
                msg_sent -= 1
            except Timeout as e:
                print e.message + os.linesep
                packets_lost += 1
                pass

            time.sleep(1)
    except KeyboardInterrupt:
        pass

        # ping results
    print "\nPing statistics for " + ip_address + ":\n\tPackets: Sent = " + str(
        msg_sent) + ", Received = " + str(
        msg_sent - packets_lost) + ", Lost = " + str(packets_lost)

    if not delays:
        print "Approximate round trip times in milli-seconds:\n\tMinimum = " + str(
            min(delays)) + "ms, Average = " + str(
            average(delays)) + "ms, Maximum = " + str(max(delays)) + "ms\n"

    pass  # Remove/replace when function is complete


def construct_icmp_header(m_format, ID):
    packet = struct.pack(m_format, ICMP_ECHO_REQUEST, 0, 0, ID, 0)
    checked = checksum(packet)
    packet = struct.pack(m_format, ICMP_ECHO_REQUEST, 0, checked, ID, 0)
    return packet


def unpack_ip_header(header):
    ip_dict = dict()

    if header != '':
        ip_keys = ["version", "length", "id", "flags", "fragment offset", "TTL", "protocol", "checksum", "src", "dest"]
        ip_packet = struct.unpack('!BBHHHBBH4s4s', header)

        # put the attributes of the ip packet into a dictionary and transform the source and the destination into proper
        # adressess
        for i in range(len(ip_keys)):
            if ip_keys[i] == "src" or ip_keys[i] == "dest":
                ip_dict.update({ip_keys[i]: socket.inet_ntoa(ip_packet[i])})
            else:
                ip_dict.update({ip_keys[i]: ip_packet[i]})

    return ip_dict


def unpack_icmp_header(header, Format):
    icmp_dict = dict()

    if header:
        icmp_keys = ["type", "code", "checksum", "identifier", "seq_num"]
        icmp_mess = struct.unpack(Format, header[:struct.calcsize(Format)])

        for i in range(len(icmp_mess)):
            icmp_dict.update({icmp_keys[i]: icmp_mess[i]})

    return icmp_dict


def average(intlist):
    sum = 0
    for i in intlist:
        sum += i
    return round(sum / len(intlist), 3)


if __name__ == "__main__":
    ping("lancaster.ac.uk")
