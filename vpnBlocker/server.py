import cherrypy,time,dns.resolver
from expiringdict import ExpiringDict
from ip_store import *
from struct import *
import multiprocessing
from multiprocessing import Manager
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

cacheManager = Manager()
#cacheManager.start()
dnsCache = cacheManager.dict()

def sniffer(ipStore,dnsCache):
    def on_sniff(pkt):
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
        
                for domain in domain_names:
                    dnsCache[domain.strip('.')] =  addresses
                print domain_names, addresses


        elif pkt.haslayer('IP'):
            ip = pkt['IP']
            ipStore.insert(str(ip.src),pkt.time*1000.0)

    sniff(iface='eth0',prn=on_sniff,store=0)
        

def checkIfSeen(domain_tuple,rec_time):
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
            #    return True
            #else:
            #    return False
            #seen = [(start_time-2 <= latest_seen and latest_seen <= rec_time+2) for 
        return status

    return [False]

class VPNBlocker(object):
    @cherrypy.expose
    def query(self,request_id,rec_time):
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
        print "New POST"
        #answers = lan_dns_resolver.query(domain,'A')
        #url_cache[request_id] = []
        #for rdata in answers:
        url_cache[request_id] = (str(domain),int(send_time))
            #print domain,rdata
        return ''

    @cherrypy.expose
    def block(self):
        return BLOCK_HTML

if __name__ == '__main__':
    #ip_tuple = ('192.168.0.1',time.time())
    p = multiprocessing.Process(target = sniffer, args=(ipStore,dnsCache))
    p.daemon = True
    p.start()
    #time.sleep(1)
    #print checkIfSeen(ip_tuple,time.time())
    cherrypy.quickstart(VPNBlocker())
