import cherrypy,time,dns.resolver
from expiringdict import ExpiringDict
from ip_store import *
from struct import *
import multiprocessing
from multiprocessing import Manager
from scapy.all import *

"""url_cache used to keep temporary data for recent requests"""
url_cache = ExpiringDict(max_len = 1000,max_age_seconds=600)

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

"""Managers used to control access to shared objects, like the dnsCache and the IpStore"""

manager = IpStoreManager()
manager.start()
ipStore = manager.IpStore()

cacheManager = Manager()
dnsCache = cacheManager.dict()


def sniffer(ipStore,dnsCache):
    """
        Sniffs network layer packets. 
        Looks for DNS responses, adds the responses to the dnsCache. 
        This ensures the dns entries of the browser cache as well as our application are consistent.
        For any other packet, stores the source IP in the ipStore.
        Running this as a separate process as cannot afford its thread being blocked
    """

    def on_sniff(pkt):
        if pkt.haslayer(DNS):
            domain_names = []
            addresses = []
            if pkt.ancount > 0 and isinstance(pkt.an,DNSRR):
                domain_names.append(pkt.qd.qname)
                for i in range(pkt.ancount):
                    dnsrr = pkt.an[i]
                    if dnsrr.type == 1:
                        addresses.append(dnsrr.rdata)
                    else:
                        domain_names.append(dnsrr.rdata)
                                
                for domain in domain_names:
                    dnsCache[domain.strip('.')] =  addresses
                print domain_names, addresses


        elif pkt.haslayer('IP'):
            ip = pkt['IP']
            ipStore.insert(str(ip.src),pkt.time*1000.0)

    sniff(iface='ppp0',prn=on_sniff,store=0)
        

def checkIfSeen(domain_tuple,rec_time):
    """
        Given a domain,request start time(start_time) and response start time(rec_time),check if any
        of the IP addresses corresponding to the domain were seen within that time period in the
        IpStore
    """

    domain,start_time = domain_tuple
    addresses = dnsCache.get(domain)
    if addresses:
        status = []
        for ip in addresses:
            latest_seen = ipStore.query(ip)
            print "IP",ip,"Timings",start_time,latest_seen,rec_time
            print start_time - latest_seen 
            print latest_seen - rec_time
            status.append(start_time-2 <= latest_seen and latest_seen <= rec_time+2)
        return status

    return [False]

class VPNBlocker(object):
    @cherrypy.expose
    def query(self,request_id,rec_time):
        """
            Given a request_id and the response start time, 
            return whether the request should be blocked(1) or not(0).
        """
        print request_id,rec_time
        domain_tuple = url_cache.get(request_id)
        rec_time = time.time()*1000.0
        if domain_tuple:
            results = checkIfSeen(domain_tuple,rec_time)
            print results
            seen = any(results)
            #seen = results
            print 'ProxyUsed',not(seen)
            if(seen):
                return '0'
            return '1'
        else:
            return '0'
    
    @cherrypy.expose
    def record(self,domain,request_id,send_time):
        """
            Given a a domain,request_id and the request start time(send_time), 
            store the domain and send_time for each request_id in the url cache(url_cache)
        """
        print "New POST"
        url_cache[request_id] = (str(domain),int(send_time))
        return ''

    @cherrypy.expose
    def block(self):
        """
            Return the block page
        """
        return BLOCK_HTML

if __name__ == '__main__':
    p = multiprocessing.Process(target = sniffer, args=(ipStore,dnsCache))
    p.daemon = True
    p.start()
    cherrypy.quickstart(VPNBlocker())
