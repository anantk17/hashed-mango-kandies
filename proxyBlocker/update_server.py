import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
import json
from server_model import *

connection_list = set()
database.connect()
database.create_tables([Blacklist],safe=True)

class EchoWebSocket(tornado.websocket.WebSocketHandler):

    def open(self):
    	connection_list.add(self)
    	url_list = [url.url for url in Blacklist.select()]
    	self.write_message(json.dumps(url_list))
        print("WebSocket opened")

    def on_message(self, message):
    	message_list = json.loads(message)
    	for message in message_list:
	    	Blacklist.create_or_get(url = message)
    	for connection in connection_list:
    		if connection != self:
        		connection.write_message(json.dumps(message_list))

    def on_close(self):
    	connection_list.remove(self)
        print("WebSocket closed")

application = tornado.web.Application([
    (r'/ws', EchoWebSocket),
])
 
 
if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
 