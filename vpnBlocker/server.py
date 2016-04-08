import cherrypy,time,dns.resolver
from expiringdict import ExpiringDict
from ip_store import *
from struct import *
import multiprocessing
from scapy.all import *

url_cache = ExpiringDict(max_len = 1000,max_age_seconds=600)

lan_dns_resolver = dns.resolver.Resolver()
lan_dns_resolver.nameservers = ['8.8.8.8']

BLOCK_HTML = """ 
<!DOCTYPE html>
<html>
    <head>
        <title>Page Blocked</title>
    </head>

    <body>
        Page blocked due to suspected VPN usage
    </body>
</html>

"""

manager = IpStoreManager()
manager.start()
ipStore = manager.IpStore()

def sniffer(ipStore):
    """import socket,sys,time
    
    try:
        s = socket.socket( socket.AF_PACKET , socket.SOCK_RAW , socket.ntohs(0x0003))
    except socket.error , msg:
        print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
 
# receive a packet
    while True:
        packet = s.recvfrom(65565)
     
    #packet string from tuple
        packet = packet[0]
     
    #parse ethernet header
        eth_length = 14
     
        eth_header = packet[:eth_length]
        eth = unpack('!6s6sH' , eth_header)
        eth_protocol = socket.ntohs(eth[2])
    #print 'Destination MAC : ' + eth_addr(packet[0:6]) + ' Source MAC : ' + eth_addr(packet[6:12]) + ' Protocol : ' + str(eth_protocol)
 
    #Parse IP packets, IP Protocol number = 8
        if eth_protocol == 8 :
        #Parse IP header
        #take first 20 characters for the ip header
            ip_header = packet[eth_length:20+eth_length]
         
        #now unpack them :)
            iph = unpack('!BBHHHBBH4s4s' , ip_header)
 
            version_ihl = iph[0]
            version = version_ihl >> 4
            ihl = version_ihl & 0xF
 
            iph_length = ihl * 4
 
            ttl = iph[5]
            protocol = iph[6]
            s_addr = socket.inet_ntoa(iph[8]);
            d_addr = socket.inet_ntoa(iph[9]);
 
        #print 'Version : ' + str(version) + ' IP Header Length : ' + str(ihl) + ' TTL : ' + str(ttl) + ' Protocol : ' + str(protocol) + ' Source Address : ' + str(s_addr) + ' Destination Address : ' + str(d_addr)
            time_stamp = time.time()*1000.00
            ipStore.insert(str(s_addr),time_stamp)
            print str(s_addr), time_stamp"""
    sniff(iface='ppp0',prn=lambda x:ipStore.insert(str(x[IP].src),time.time()*1000.0))
        

def checkIfSeen(ip_tuple,rec_time):
    ip,start_time = ip_tuple
    latest_seen = ipStore.query(ip)
    print "IP",ip,"Timings",start_time,latest_seen,rec_time
    print start_time - latest_seen 
    print latest_seen - rec_time
    if (start_time-2 <= latest_seen and latest_seen <= rec_time+2):
        return True
    else:
        return False

class VPNBlocker(object):
    @cherrypy.expose
    def query(self,request_id,rec_time):
        print request_id,rec_time
        ip_tuples = url_cache.get(request_id)
        rec_time = time.time()*1000.0
        if ip_tuples:
            results = [checkIfSeen(x,rec_time) for x in ip_tuples]
            print results
            seen = any(results)
            print 'ProxyUsed',not(seen)
            if(seen):
                return '0'
            return '1'
        else:
            return '0'
    
    @cherrypy.expose
    def record(self,domain,request_id,send_time):
        print "New POST"
        answers = lan_dns_resolver.query(domain,'A')
        url_cache[request_id] = []
        for rdata in answers:
            url_cache[request_id].append((str(rdata),int(send_time)))
            print domain,rdata
        return ''

    @cherrypy.expose
    def block(self):
        return BLOCK_HTML

if __name__ == '__main__':
    #ip_tuple = ('192.168.0.1',time.time())
    p = multiprocessing.Process(target = sniffer, args=(ipStore,))
    p.daemon = True
    p.start()
    #time.sleep(1)
    #print checkIfSeen(ip_tuple,time.time())
    cherrypy.quickstart(VPNBlocker())
