#!/usr/bin/python
# -*- coding: UTF-8 -*-

from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages


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
        answer = htons(answer) & 0xffff
    else:
        answer = htons(answer)

    return answer


def receiveOnePing(icmpSocket, destinationAddress, ID, timeout):
    # 1. Wait for the socket to receive a reply
    icmpSocket.setblocking(0)

    ready = select.select([icmpSocket], [], [], timeout)
    if ready[0] != []:
        data = icmpSocket.recv(20 + struct.calcsize("bbHHh"))
    else:
        print "response timed out"
        return -1
    # 2. Once received, record time of receipt, otherwise, handle a timeout
    recv_time = time.time()
    # 3. Compare the time of receipt to time of sending, producing the total network delay

    # 4. Unpack the packet header for useful information, including the ID
    msg_type, msg_code, check_sum, recv_id, seq_num = struct.unpack("bbHHh", data[20:28])
    # 5. Check that the ID matches between the request and reply
    if ID != recv_id:
        print "ids are different"
    # 6. Return total network delay
    return recv_time
    pass  # Remove/replace when function is complete


def sendOnePing(icmpSocket, destinationAddress, ID):
    # 1. Build ICMP header
    packet = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, ID, 0)
    # 2. Checksum ICMP packet using given function
    checked = checksum(packet)
    # 3. Insert checksum into packet
    packet = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, checked, ID, 0)
    # connect
    if icmpSocket.connect_ex((destinationAddress, getprotobyname('icmp'))):
        raise RuntimeError("Connection was not established")
    # 4. Send packet using socket
    if icmpSocket.sendall(packet):
        raise RuntimeError("That bitch didn't send")
    #  5. Record time of sending
    return time.time()


def doOnePing(destinationAddress, timeout):
    # 1. Create ICMP socket
    icmp_socket = socket(AF_INET, SOCK_RAW, getprotobyname('icmp'))
    # icmp_socket.settimeout(timeout)
    # 2. Call sendOnePing function
    timesent = sendOnePing(icmp_socket, destinationAddress, 0)
    # 3. Call receiveOnePing function
    timerecv = receiveOnePing(icmp_socket, destinationAddress, 0, timeout)
    # 4. Close ICMP socket
    icmp_socket.close()
    # 5. Return total network delay
    return (timerecv - timesent) * 1000


def ping(host, pingtime=3, timeout=1):
    delays = []
    # 1. Look up hostname, resolving it to an IP address
    ip_address = gethostbyname(host)

    for i in range(pingtime):
        # 2. Call doOnePing function, approximately every second
        delay = doOnePing(ip_address, timeout)
        # 3. Print out the returned delay
        print delay
        delays.append(delay)
        # 4. Continue this process until stopped
    avgd= average(delays)
    mind = min(delays)
    maxd = max(delays)

    print

    # pass  # Remove/replace when function is complete


def average(listofints):
    avg_sum = 0
    for i in listofints:
        avg_sum += i

    return (avg_sum / len(listofints))


ping("lancaster.ac.uk")
