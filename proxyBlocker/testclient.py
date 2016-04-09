import websocket
import thread
import threading
import time
import multiprocessing
value_global = 'dsdfasdas'
def update_client(task_queue):

    def on_message(ws, message):
        print message

    def on_error(ws, error):
        print error

    def on_close(ws):
        print "### closed ###"

    def on_open(ws):
        def run(*args):
            while True:
                next_task = task_queue.get()
                time.sleep(5)
                if next_task:
                    # Poison pill means shutdown
                    #print '%s: Exiting' % proc_name
                    ws.send(str(next_task))
                    print value_global
                    task_queue.task_done()

    print "something"
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:8888/ws",
                                    on_message = on_message,
                                    on_error = on_error,
                                    on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

tasks = multiprocessing.JoinableQueue()
'''
p = multiprocessing.Process(target = update_client, args=(tasks, ))
p.daemon = True
p.start()
'''
#thread.start_new_thread(update_client, (tasks, ))

update_client(tasks)
