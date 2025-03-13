# client-side 
import client as cli
import asyncio
import threading 
import os
import terminal as tty

IS_WINDOWS = os.name == "nt"
IS_POSIX  = os.name == "posix"

if IS_WINDOWS:
    import gui

async def main():
    print(f"Starting garage on {os.name}")
    # Connect
    client = cli.Client()

    try:  
        await client.connect(("194.164.199.39", 7719))
        password = client.get_password()
        
        if await client.authenticate(password):
            if IS_POSIX:
                await tty.Terminal().start()
                print("Started TERMINAL.")
            elif IS_WINDOWS:
                await tty.Terminal().start()
                # threading.Thread(target=start_gui, args=(client,)).start()
                # print("Started GUI.")
        
        while True: # Keep program alive
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in establishing client connection: {e}")
        client.close()
def start_gui(client):    
    app = gui.AppWindow(client)
    app.load_incoming_data()
    app.mainloop()

if __name__ == "__main__":
    asyncio.run(main()) 




