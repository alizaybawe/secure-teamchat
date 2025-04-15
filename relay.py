import socket
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os
import base64
import asyncio
import time

# List to store all connected clients
clients = {}


session_key = Fernet.generate_key()
print(f"[info] The session key is {session_key}")

# Shared Secret between clients
shared_secret = b"Aboody1106"

async def handle_client(reader, writer):
    client_address = writer.get_extra_info('peername')
    # When a client sends a message, relay it to other clients
    while True:
        try:


            if reader is None: 
                break # Shutdown signal
            message = await asyncio.wait_for(reader.read(1024), timeout = None)

            if not message: # Empty message, client disconnected
                clients.pop(client_address, None)
                print(f"Connection from {client_address} abruptly closed.")
                writer.close()
                await writer.wait_closed() 
                break

            if message:
                print(f"[got-msg] {client_address} {message} at {int(time.time())} for {client_address}")

                print("--------------------------")
                if message == b".update":
                    clients[client_address]["last-communication"] = int(time.monotonic())
                    print(f"User heartbeat: {client_address}")
                if message == b".clients":
                    print("Displaying current clients list:")
                    print(clients)         
                if message == b".exit":
                    clients.pop(client_address, None)
                    print(f"Connection from {client_address} gracefully closed.")
                    writer.close()
                    await writer.wait_closed()     
                    print(f"Received exit from {client_address}")
                    clients[client_address]["last-communication"] = int(time.monotonic())
                    clients[client_address]["connection-status"] = False
                    break


                for addr, client_info in clients.items():
                    #if addr != addr and not client_info["socket"]._closed:
                    if addr != client_address:
                        print(f"Operating on {addr}\nClient info:\n")
                        print(client_info)
                        print("----")
                        try:
                            #bytes_sent = client_info["socket"].send(message)
                            if clients[client_address]["authenticated"] == True:
                                bytes_sent = client_info["sock_writer"].write(message)
                                print(f"[relay-msg] Sent bytes to {addr} from {client_address}: {message}")
                                clients[client_address]["last-communication"] = int(time.monotonic())
                            else:
                                raise Exception("cannot relay for unauthenticated client: {client_address}")
                        except OSError as e:
                            if e.errno == 9: # Bad file descriptor
                                print(f"Bad socket descriptor:\n{clients[addr]}")
                        except Exception as e:
                            print(f"Error in communicating with client {e}") # Test again to see the error (to prevent ghosting effect)
        except Exception as e: 
            # If the connection is lost, remove the client
            print(f"[Exception] {e}")
            clients.pop(client_address, None)
            writer.close()
            await writer.wait_closed()     
            break 
    print("Processed handle_client()")

async def authenticate_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"CALLED AUTHENTICATE_CLIENT")
    try:
        
        salt_header = await asyncio.wait_for(reader.read(4), timeout = 30) 
        salt_size = int.from_bytes(salt_header, byteorder="big")
        salt = await asyncio.wait_for(reader.read(salt_size), timeout = 30) 
        print(f"Received salt header {base64.b64encode(salt_header)} and salt {base64.b64encode(salt)}")
        

        # Decrypt received password:
        try: 
            iterations = 100000
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations
            )
            # Get 32-sized salted iterated key from shared secret using PBKDF2
            passphrase = await asyncio.wait_for(reader.read(1024), timeout = 30) 
            print(f"Password entered: {passphrase}")
            derived_key = kdf.derive(shared_secret)
            print(f"derived key {derived_key}")

            fernet_safe_key = base64.urlsafe_b64encode(derived_key)
            print(f"FSK {fernet_safe_key}")
            cipher_suite = Fernet(fernet_safe_key)
            print(f"cipher suite {cipher_suite}")
            client_passphrase = cipher_suite.decrypt(passphrase)
            print(f"The shared secret is: {client_passphrase}")
        except Exception as e:
            print(f"Error at decrypting {e} password")
        # Authentication
        if client_passphrase != b'Aboody1106':
            print(f"Received wrong password {client_passphrase} from {addr}; closing the connection.")
            writer.close()
            await writer.wait_closed() 
        else: 
            print(f"Accepted connection for {addr}")

            # Encrypt session key based on shared secret
            salt = os.urandom(16)
            writer.write(len(salt).to_bytes(4, byteorder="big"))
            writer.write(salt)
            print(f"Sent salt {salt}")
            
            iterations = 100000
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations
            )
            # Get 32-sized salted iterated key from shared secret using PBKDF2
            derived_key = kdf.derive(shared_secret) # Derive a use-able key from shared secret
            
            # Encode it to be Fernet-safe
            fernet_safe_key = base64.urlsafe_b64encode(derived_key)
            
            # Create the Fernet instance
            cipher_suite = Fernet(fernet_safe_key)

            # Encrypt the current session key using the shared secret's derived key
            encrypted_session_key = cipher_suite.encrypt(session_key)
            
            # Now that the session key is encrypted (by a shared secret among clients), it can be transmitted over unsecure channels
            writer.write(len(encrypted_session_key).to_bytes(4, byteorder='big'))
            writer.write(encrypted_session_key)

            await writer.drain()
            print(f"Transmitted encrypted session key: {encrypted_session_key}")

            # Client is authorized
            clients[addr]["authenticated"] = True
            return True
            

    except Exception as e:
        # No password received.
        await writer.drain()
        writer.close()
        await writer.wait_closed() 
    return False

async def start_server():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 7719))  # Listen on all interfaces
    server.listen() 
    server.setblocking(False)
    
    loop = asyncio.get_running_loop()

    print("Server is running on 194.164.199.39:7719, waiting for connections...")


    while True:
        #client_socket, addr = server.accept()
        client_socket, addr = await loop.sock_accept(server)
        client_socket.setblocking(False)


        # Add disconnection timer if client doesnt send pasword within X time..
        # Add the new client to the clients dictionary

        reader, writer = await asyncio.open_connection(sock=client_socket)
        
        print(f"New connection from {addr}")
        
        clients[addr] = {
            "sock_writer": writer,
            "sock_reader": reader,
            "session-key": session_key,
            "last-communication": time.monotonic(),
            "connection-status": True,
            "authenticated": False
        }

        task = asyncio.create_task(authenticate_client(reader, writer))
        task.add_done_callback(lambda t: asyncio.create_task(handle_client(reader, writer)))

# async def get_online_users():
#     for addr, client_info in clients.items():
        

if __name__ == "__main__":
    asyncio.run(start_server())
