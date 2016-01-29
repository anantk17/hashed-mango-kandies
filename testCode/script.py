from libmproxy.script import concurrent
from libmproxy.models import HTTPResponse
from netlib.http import Headers
import requests,re,urllib,copy,urlparse

ref_url = "athena.nitc.ac.in/anant_b120519cs/refURL"
refPrime = "123456"
url_regex = r"(https?:\/\/(www\.)?([-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6})\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))"
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

def request(context,flow):
    """
    if "application/x-www-form-urlencoded" in flow.request.headers.get("content-type", ""):
        form = flow.request.get_form_urlencoded()
        if(form.get("u",None)):
            #flow.intercept(context._master)
            context.log(flow.request.headers.get_all("cookie"))
            f = context.duplicate_flow(flow)
            flow.intercept(context._master)
            form = f.request.get_form_urlencoded()
            form["u"] = ["athena.nitc.ac.in"]
            f.request.set_form_urlencoded(form)
            context.replay_request(f)
             
            context.log(f.response)
            context.log(f.response.headers.get_all("set-cookie"))
            locate_url = f.response.headers.get("Location","")
            context.log("Redirect URL : " +  locate_url)
           r = requests.get(locate_url)
            context.log(r)
     """

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
            context.log(flow.request.url)
            current_url = flow.request.url
            target_url = urlparse.urlunparse(urlparse.urlparse(current_url)._replace(query=""))

            r = requests.get(target_url,params=query,
                    cookies=cookies)
            
            context.log(flow.request.url)
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
    
    else:
        pass
        #raise NotImplementedError

