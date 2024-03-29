from libmproxy.script import concurrent
from libmproxy.models import HTTPResponse
from netlib.http import Headers
import requests,re,urllib,copy,urlparse
from pybloomfilter import BloomFilter
from model import *
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import websocket
import thread
import threading
import time
import json
import multiprocessing


browser = webdriver.PhantomJS()

database.connect()
database.create_tables([Blacklist],safe=True)

try:
    bloom_Filter = BloomFilter.open('blacklist')
except OSError: 
    bloom_Filter = BloomFilter(10000000, 0.01, 'blacklist')

ref_url = "athena.nitc.ac.in/anant_b120519cs/refURL"
refPrime = "2074722246773485207821695222107608587480996474721117292752992589912196684750549658310084416732550077"
url_regex = r"(((https?:\/\/)?(www\.)?)?([-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6})\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))"
matcher = re.compile(url_regex)

block_html = "<html><head><title>PAGE BLOCKED</title></head><body>Suspected Proxy Usage</body></html>"

def update_client(task_queue):
    """
    Collaborative blacklist update client
    On connecting to the central server , updates will be recieved
    On encountering new proxy site, update will be pushed to central server 
    """
    def on_message(ws, message):
        data = json.loads(message)
        for url in data:
            Blacklist.create_or_get(url = url)
            bloom_Filter.add(url)

    def on_error(ws, error):
        print(error)

    def on_close(ws):
        print("### closed ###")

    def on_open(ws):
        def run(*args):
            while True:
                next_task = task_queue.get()
                time.sleep(2)
                if next_task:
                    ws.send(json.dumps(next_task))
                    task_queue.task_done()

        thread.start_new_thread(run, ())

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:8888/ws",
                                    on_message = on_message,
                                    on_error = on_error,
                                    on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

tasks = multiprocessing.JoinableQueue()

thread.start_new_thread(update_client, (tasks, ))

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

@concurrent
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

                if(primeFound >= 0):
                    context.log("Prime Found")
                    bloom_Filter.add(target_url)
                    add_to_blacklist_db(target_url)
                    tasks.put([target_url])
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
                        #r = requests.get(locate_url,cookies=cookies)
                    parsed_url = urlparse.urlparse(new_locate_url)
                    scheme = parsed_url[0]
                    hostname = parsed_url[1]
                    browser.get(scheme + "://" + hostname + "/" + refPrime)
                    for key,value in cookies.items():
                        try:
                            c = {'name':key,'value':value}
                            browser.add_cookie(c)
                        except WebDriverException as e:
                            continue
                    
                    browser.get(locate_url)
                    source = browser.page_source
                    #with open('proxyPage.html','w') as outfile:
                    #    outfile.write(source)
                    #
                    primeFound = source.find(refPrime)
                    #logging.critical("Cookies follow")
                    #logging.critical(cookies)
                    #primeFound = r.text.find(refPrime)
                    if(primeFound >= 0):
                        context.log("Prime Found")
                        bloom_Filter.add(base_url)
                        add_to_blacklist_db(base_url)
                        bloom_Filter.add(new_locate_url)
                        add_to_blacklist_db(new_locate_url)
                        tasks.put([base_url,new_locate_url])
                        #tasks.put(new_locate_url)
                        #context.log(db_list)
                        block_request(flow)

                else:
                    pass

                flow.accept_intercept(context._master)


            #raise NotImplementedError
            
