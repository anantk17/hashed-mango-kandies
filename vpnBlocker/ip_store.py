import time

class IpStore:
    def __init__(self):
        self.store = dict() 
    
    def insert(self,ip,time):
        
        def recursive_insert(nodes,ip_list,time):
            if len(ip_list) == 1:
                nodes[ip_list[0]] = time
                return nodes
            else:
                if ip_list[0] in nodes.keys():
                    nodes[ip_list[0]] = recursive_insert(nodes[ip_list[0]],ip_list[1:],time)
                    return nodes
                else:
                    nodes[ip_list[0]] = recursive_insert(dict(),ip_list[1:],time)
                    return nodes

        ip_list = map(int,ip.split('.'))
        self.store = recursive_insert(self.store,ip_list)
    
    def query(self,ip):
        
        def recursive_query(nodes,ip_list):
            if len(ip_list) == 1:
                return nodes.get(ip_list[0],-1)
            else:
                if ip_list[0] in nodes.keys():
                    return recursive_query(nodes[ip_list[0]],ip_list[1:])
                else:
                    return -1

        ip_list= map(int,ip.split('.'))
        last_seen = recursive_query(self.store,ip_list)
        return last_seen
    
    def __repr__(self):
        return str(self.store)

