import cherrypy
from expiringdict import ExpiringDict
import dns.resolver

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
def checkIfSeen(ip_tuple,rec_time):
    return True

class VPNBlocker(object):
    @cherrypy.expose
    def query(self,request_id,rec_time):
        print request_id,rec_time
        ip_tuple = url_cache.get(request_id)
        seen = checkIfSeen(ip_tuple,rec_time)
        if(seen):
            return '1'
        return '0'
    
    @cherrypy.expose
    def record(self,domain,request_id,send_time):
        print domain,send_time
        answers = dns.resolver.query(domain,'A')
        for rdata in answers:
            url_cache[request_id] = (rdata,send_time)

        return ''

    @cherrypy.expose
    def block(self):
        return BLOCK_HTML

if __name__ == '__main__':
    cherrypy.quickstart(VPNBlocker())

