import queue

class Terminal():
    def __init__(self, client):
        self.client = client
        self.outbox = client.outbox

    def terminal_chat(self): 
        while True:
            try:
                message = input("You: ") # For some reaosn this is dominating the main thread despite being ran on new thread..
                formatted_message = self.format_message(message)
                self.outbox.put(formatted_message)
                print("Added to queue!")
            except Exception as e:
                print(f"Error at terminal feed: {e}")
    # Must be str
    def format_message(self, message):
        formatted_message = self.client.username + ":" + " " + message
        return formatted_message



