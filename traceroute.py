import icmp_ping
import sys
import socket
from os import linesep


def traceroute(host, port, probes=3, timeout=1, max_hops=30):
    try:
        ip_address = socket.gethostbyname(str(host))
    except:
        print "Ping request could not find host ", host, " Please check the name and try again."
        sys.exit(0)

    ttl = 1
    while ttl <= max_hops:
        print str(ttl) + "\t",

        response = None
        for i in range(probes):
            try:
                response = icmp_ping.doOnePing(ip_address, port, timeout, ttl)
                print response['delay'] + " ms\t",
            except icmp_ping.Timeout:
                print "*\t",

        if response:
            if socket.inet_ntoa(response['src']) == response['src']:
                print  response['src']
            else:
                print socket.inet_ntoa(response['src']) + " [" + response['src'] + "] "

            if response['src'] == ip_address:
                print linesep + "Trace complete."
                break
        ttl += 1
