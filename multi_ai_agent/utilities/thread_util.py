initial_thread_id = 1234

def getConfig():
    return { "configurable": { "thread_id": str(initial_thread_id) } }

def new_thread():
    global initial_thread_id
    initial_thread_id += 1
    return initial_thread_id