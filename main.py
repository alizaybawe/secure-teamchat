# client-side 
import client as cli
import asyncio
import threading 
import os
import terminal as tty
import queue

IS_WINDOWS = os.name == "nt"
IS_POSIX  = os.name == "posix"

if IS_WINDOWS:
    import gui

def app():
    asyncio.run(connect()) 

async def connect():
    print(f"Starting garage on {os.name}")
    # Connect
    client = cli.Client()

    try:  
        print("Connecting..")
        await client.connect(("194.164.199.39", 7719))
        print("Getting password..")
        password = client.get_password()
        print("Authenticating..")
        if await client.authenticate(password):

            asyncio.create_task(client.outbox_checker())
            
            asyncio.create_task(client.receive_messages())

            send_queue = queue.Queue()
            client.outbox = send_queue

            if IS_POSIX:
                terminal = tty.Terminal(send_queue)
                threading.Thread(target=terminal.terminal_chat).start()
            elif IS_WINDOWS:
                terminal = tty.Terminal(send_queue)
                threading.Thread(target=terminal.terminal_chat).start()

        while True: # Keep program alive
            await asyncio.sleep(0)
    except Exception as e:
        print(f"Error in establishing client connection: {e}")
        client.close()
def start_gui(client):    
    app = gui.AppWindow(client)
    app.load_incoming_data()
    app.mainloop()

if __name__ == "__main__":
    threading.Thread(target=app).start()




