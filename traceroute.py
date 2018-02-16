import icmp_ping
import sys
import socket
from time import sleep
from os import linesep


def traceroute(host, port, probes=3, timeout=1, max_hops=30):
    try:
        ip_address = socket.gethostbyname(str(host))
    except:
        print "Ping request could not find host ", host, " Please check the name and try again."
        sys.exit(0)

    for ttl in range(1, max_hops):
        print str(ttl) + "\t",

        response = None
        for i in range(probes):
            try:
                response = icmp_ping.doOnePing(ip_address, port, timeout, ttl)
                print str(response['delay']) + " ms\t",
            except icmp_ping.Timeout:
                print "*\t",
            sleep(1)

        if response:
            try:
                print socket.gethostbyaddr(str(response['src']))[0] + " [" + response['src'] + "] ",
            except:
                print response['src'],

            if response['src'] == ip_address:
                print linesep + "Trace complete."
                break

        print linesep,


if __name__ == "__main__":
    traceroute("google.com", 80)
