#import logging
#logging.basicConfig(filename='sample.log',level=logging.CRITICAL)

from libmproxy.script import concurrent
from libmproxy.models import HTTPResponse
from netlib.http import Headers
import requests,re,urllib,copy,urlparse

ref_url = "athena.nitc.ac.in/anant_b120519cs/refURL"
refPrime = "123456"
url_regex = r"(((https?:\/\/)?(www\.)?)?([-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6})\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))"
matcher = re.compile(url_regex)

block_html = "<html><head><title>PAGE BLOCKED</title></head><body>Suspected Proxy Usage</body></html>"

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
            #context.log(flow.request.url)
            current_url = flow.request.url
            target_url = urlparse.urlunparse(urlparse.urlparse(current_url)._replace(query=""))

            try:
                r = requests.get(target_url,params=query,
                    cookies=cookies)
            except requests.exceptions.SSLError,requests.exceptions.MissingSchema:
                flow.accept_intercept(context._master)
                return 

            #context.log(flow.request.url)
            primeFound = r.text.find(refPrime)

            if(primeFound):
                #context.log("Prime Found")
                #add_to_blacklist(flow.request.pretty_host)
                resp = HTTPResponse("HTTP/1.1",200,"OK",
                        Headers(Context_Type="text/html"),
                        block_html)
                flow.reply(resp)
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
                #logging.critical(locate_url)
                #context.log(f.request.headers.get_all("cookie"))
                #cookies = get_all_cookies(f)
                #logging.critical(f.request.headers.get_all("cookie"))
                #r = requests.get(locate_url,cookies=cookies)
                #logging.critical(f.response.headers.get_all("set-cookie"))
                #primeFound = r.text.find(refPrime)
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
                    #add_to_blacklist(flow.request.pretty_host)
                    resp = HTTPResponse("HTTP/1.1",200,"OK",
                            Headers(Context_Type="text/html"),
                            block_html)
                    flow.reply(resp)
            else:
                pass

            flow.accept_intercept(context._master)


        #raise NotImplementedError
        
