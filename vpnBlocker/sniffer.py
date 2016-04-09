#Packet sniffer in python
#For Linux - Sniffs all incoming and outgoing packets :)
#Silver Moon (m00n.silv3r@gmail.com)
 
import socket, sys
from struct import *
import time
from scapy.all import *
from scapy.layers.dns import DNSRR,DNS, DNSQR

def sniffer(pkt):
    if pkt.haslayer(DNS):
        domain_names = []
        addresses = []
        if pkt.ancount > 0 and isinstance(pkt.an,DNSRR):
            domain_names.append(pkt.qd.qname)
            #print pkt.ancount, pkt.qd.qname
            for i in range(pkt.ancount):
                dnsrr = pkt.an[i]
                if dnsrr.type == 1:
                    addresses.append(dnsrr.rdata)
                else:
                    domain_names.append(dnsrr.rdata)
                #print dnsrr.rrname, dnsrr.rdata, dnsrr.type
        
            print domain_names , addresses

    elif pkt.haslayer('IP'):
        ip = pkt['IP']
        #print ip.src
    #print pkt.time*1000.0


conf.sniff_promisc=False
sniff(iface='eth0',prn=sniffer,store=0)

