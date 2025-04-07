import queue

class Terminal():
    def __init__(self, outbox):
        self.outbox = outbox

    def start(self): 
        while True:
            try:
                message = input("You: ") # For some reaosn this is dominating the main thread despite being ran on new thread..
                self.outbox.put(message)
                print("Added to queue!")
            except Exception as e:
                print(f"Error at terminal feed: {e}")



