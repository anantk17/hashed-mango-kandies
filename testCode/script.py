from libmproxy.script import concurrent
from libmproxy.models import HTTPResponse
from netlib.http import Headers
import requests,re,urllib,copy,urlparse
from pybloomfilter import BloomFilter
from model import *


database.connect()
database.create_tables([Blacklist],safe=True)

try:
    bloom_Filter = BloomFilter.open('blacklist')
except OSError: 
    bloom_Filter = BloomFilter(10000000, 0.01, 'blacklist')

ref_url = "athena.nitc.ac.in/anant_b120519cs/refURL"
refPrime = "123456"
url_regex = r"(((https?:\/\/)?(www\.)?)?([-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6})\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))"
matcher = re.compile(url_regex)

block_html = "<html><head><title>PAGE BLOCKED</title></head><body>Suspected Proxy Usage</body></html>"

def in_blacklist(suspect_url):
    """
        Given a url, returns whether it is present in the blacklist
    """
    return Blacklist.select(Blacklist.url).where(Blacklist.url << [suspect_url]).count() > 0

def strip_query_params_from_url(url):
    """
        Given a URL, remove GET request query params and return the 
        remaining URL string
    """
    return urlparse.urlunparse(urlparse.urlparse(url)._replace(query=""))

def add_to_blacklist_db(url):
    """
        Given a URL, adds it to the blacklist database 
    """ 
    Blacklist.insert(url = url).execute()


def block_request(flow):
    """
        Modifies flow and blocks request for suspected proxy usage
    """
    resp = HTTPResponse("HTTP/1.1",200,"OK",
                        Headers(Context_Type="text/html"),
                        block_html)
    flow.reply(resp)

def url_in_query(query):
    """
        Given a GET request query dictionary, returns the key which has a URL-like value.
        Returns None if no such key exists
    """

    for key,value in query:
        if matcher.match(urllib.unquote(value).decode('utf8')):
            return key

    return None

def get_url_key(form):
    """
        Given a POST request form dictionary, returns the key which contains a array having a
        URL-like value.
        Returns None if no such key exists
    """

    for key, value in form:
        for v in value:
            if matcher.match(urllib.unquote(value).decode('utf8')):
                return key

    return None

def parse_cookie_string(cookie_string, cookies):
    """
        Given a string of all cookie header values, converts the cookies into a dictionary
        compatible with the requests library
    """

    if len(cookie_string) > 0 :
        cookie_list = cookie_string[0].split(';')
        for cookie in cookie_list:
            if ( cookie.count('=') == 1):
                key,val = cookie.strip().split('=')
                cookies[key] = val

def get_all_cookies(flow):
    """
        Extracts all cookies from the flow object into a dictionary
    """

    cookies = {}
    if "cookie" in flow.request.headers:
        c_string = flow.request.headers.get_all("cookie")
        parse_cookie_string(c_string,cookies)
    
    if "set-cookie" in flow.response.headers:
        c_string = flow.response.headers.get_all("set-cookie")
        parse_cookie_string(c_string,cookies)
    
    return cookies
        
def request(context,flow):
    current_url = flow.request.url
    base_url = strip_query_params_from_url(current_url) 
    
    if base_url in bloom_Filter and in_blacklist(base_url):
        context.log(base_url)
        block_request(flow)

    else:
        if flow.request.method == 'GET':
            q = flow.request.get_query()
            key = url_in_query(q)
            if key:
                #cookies = parse_cookies_from_request(flow.request)
                cookies = {}
                flow.intercept(context._master)
                query = copy.deepcopy(q)
                query[key] = [ref_url]
                locate_url = flow.request.headers.get("Location","")
                target_url = base_url
                try:
                    r = requests.get(target_url,params=query,
                        cookies=cookies)
                except requests.exceptions.SSLError,requests.exceptions.MissingSchema:
                    flow.accept_intercept(context._master)
                    return 

                #context.log(flow.request.url)
                primeFound = r.text.find(refPrime)

                if(primeFound):
                    context.log("Prime Found")
                    bloom_Filter.add(target_url)
                    add_to_blacklist_db(target_url)
                    block_request(flow)

                else:
                    pass

                flow.accept_intercept(context._master)
        
        elif flow.request.method == 'POST':
            if "application/x-www-form-urlencoded" in flow.request.headers.get("content-type",""):
                form = flow.request.get_form_urlencoded()
                key = get_url_key(form)
                #logging.debug(key)
                if(key):
                    #logging.critical(key)
                    f = context.duplicate_flow(flow)
                    flow.intercept(context._master)
                    form = f.request.get_form_urlencoded()
                    form[key] = [ref_url]
                    f.request.set_form_urlencoded(form)
                    context.replay_request(f)
                    
                    locate_url = f.response.headers.get("Location","")
                    new_locate_url = strip_query_params_from_url(locate_url)
                    cookies = get_all_cookies(f)
                    try:
                        r = requests.get(locate_url,cookies=cookies)
                    except requests.exceptions.MissingSchema as e:
                        flow.accept_intercept(context._master)
                        return 
                    #logging.critical("Cookies follow")
                    #logging.critical(cookies)
                    primeFound = r.text.find(refPrime)
                    if(primeFound):
                        context.log("Prime Found")
                        bloom_Filter.add(base_url)
                        add_to_blacklist_db(base_url)
                        bloom_Filter.add(new_locate_url)
                        add_to_blacklist_db(new_locate_url)
                        #context.log(db_list)
                        block_request(flow)

                else:
                    pass

                flow.accept_intercept(context._master)


            #raise NotImplementedError
            
