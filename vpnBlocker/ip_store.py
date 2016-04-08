import time
from multiprocessing.managers import BaseManager, BaseProxy

class IpStore(object):
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
        self.store = recursive_insert(self.store,ip_list,time)
    
    def query(self,ip):
        
        def recursive_query(nodes,ip_list):
            if len(ip_list) == 1:
                return nodes.get(ip_list[0],-1)
            else:
                if ip_list[0] in nodes.keys():
                    return recursive_query(nodes[ip_list[0]],ip_list[1:])
                else:
                    return -1
        
        print "query-func",type(ip)
        ip_list= map(int,ip.split('.'))
        last_seen = recursive_query(self.store,ip_list)
        return last_seen
    
    def __repr__(self):
        return str(self.store)
    
    def get_store(self):
        return self.store

class IpStoreManager(BaseManager):
    pass

class IpStoreProxy(BaseProxy):
    __exposed__ = ('__getattribute__', '__setattr__', '__delattr__', 'insert','query')

    def insert(self,ip,time):
        callmethod = object.__getattribute__(self,'_callmethod')
        return callmethod(self.insert.__name__, (ip,time,))

    def query(self,ip):
        callmethod = object.__getattribute__(self,'_callmethod')
        return callmethod(self.query.__name__, (ip,))

    def get_store(self):
        callmethod = object.__getattribute__(self,'_callmethod')
        return callmethod(self.get_store.__name__,)

IpStoreManager.register('IpStore',IpStore,IpStoreProxy)

