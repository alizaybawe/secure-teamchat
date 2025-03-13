import queue
import asyncio
import aioconsole

class Terminal():
    def __init__(self):
        print("Hello?")
        self.send_queue = queue.Queue()

    async def start(self): 
        print("start Hello?")
        asyncio.create_task(self.feed())
        print("start Hello? 2")
    async def feed(self):
        while True:
            try:
                print("Feed loop.")
                message = await aioconsole.ainput("You: ")
                self.send_queue.put(message)
                print("Added to queue")
            except Exception as e:
                print(f"Error at terminal feed: {e}")


