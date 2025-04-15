import socket
from cryptography.fernet import Fernet 
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os
import base64
import getpass
import sys
import queue
import asyncio
import terminal as tty
from time import time


class Client():
    def __init__(self):
        
        # Initialize client
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.reader = None
        self.writer = None
        self.connection_info = None
        self.terminal = None
        self.gui = None
        self.outbox = None
        self.inbox = None
        self.username = None

        # Catching exit signals
        # signal.signal(signal.SIGINT, lambda sig, frame: self.close(sig, frame))
        # signal.signal(signal.SIGTERM, lambda sig, frame: self.close(sig, frame))



    async def connect(self, connection_info):
        self.connection_info = connection_info
        ip, port = connection_info
        try:
            self.reader, self.writer = await asyncio.open_connection(host=ip, port=port)
        except Exception as e:
            print(f"Connection failed: {e}")

    def get_password(self): # To allow for piping passwords
        return getpass.getpass("Enter the chat's passphrase:")

    async def authenticate(self, passphrase):
        # client = self.socket
        reader = self.reader
        writer = self.writer
        try: # Authenticate 
            # Access password is sent in plain text: not a good idea
            access_salt = os.urandom(16)
            print(f"Access salt {base64.b64encode(access_salt)}")
            writer.write(len(access_salt).to_bytes(4, byteorder="big"))
            writer.write(access_salt)
            iterations = 100000
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=access_salt,
                iterations=iterations
            )
            derived_key = kdf.derive(passphrase.encode())
            fernet_safe_key = base64.urlsafe_b64encode(derived_key)
            cipher_suite = Fernet(fernet_safe_key)
            writer.write(cipher_suite.encrypt(passphrase.encode()))
            await writer.drain()
        except Exception as e:
                print(f"Failed to send the inserted password over to the server {e}")
        try: 
            # Get salt 
            salt_size = int.from_bytes(await reader.read(4), byteorder="big")
            if salt_size == 0:
                return print("Authentication failed. Reload this window to reconnect!")
            
            salt = await reader.read(salt_size)
            encrypted_key_size = int.from_bytes(await reader.read(4), byteorder="big")

            # Receive the session key from server
            encrypted_session_key = await reader.read(encrypted_key_size)
            
            print(f"Received session key that is encrypted by shared secret: {encrypted_session_key}\nSalt: {salt}")
        except OSError as e:
            print(f"Failed to receive salt and session key.\nReason: {e}")
            return None

        # Decrypting session key based on shared secret (passphrase):
        try:
            iterations = 100000
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations
            )
            # Get 32-sized salted iterated key from shared secret using PBKDF2
            print(f"Password entered: {passphrase.encode()}")
            derived_key = kdf.derive(passphrase.encode())

            session_key = base64.urlsafe_b64encode(derived_key)
            print(f"URLSAFE base64 session_key = {session_key}")
            
            cipher_suite = Fernet(session_key)

            decrypted_session_key = cipher_suite.decrypt(encrypted_session_key)
        except Exception as e:
            print(f"Error decrypting session key: {e}")
        
        self.session_key = decrypted_session_key
        
        return decrypted_session_key

    def encrypt (self, data):
        cipher_suite = Fernet(self.session_key)

        # Encrypt message
        encrypted_data = cipher_suite.encrypt(data.encode())
        encrypted_header = cipher_suite.encrypt(len(encrypted_data).to_bytes(4, byteorder="big"))
        print(f"Encrypted '{data}' (LEN: {len(data)}) into {encrypted_data} (LEN: {len(encrypted_data)});\n header {encrypted_header} (LEN: {len(encrypted_header)})")
        return (encrypted_header, encrypted_data)
        
    async def send_message(self, message):
        # client = self.socket
        writer = self.writer
        msg_size = len(message)
        msg_size_bytes = msg_size.to_bytes(4, byteorder="big")
        # Message is not empty
        if msg_size > 0:     

            # Player is sending a command
            if self.is_command(message):
                await self.send_command(message)

            # Player is sending a normal message that needs to be relayed
            else:
                print("Encrypting message before sending.")
                encrypted_header, encrypted_message = self.encrypt(message)
    
                writer.write(encrypted_header)
                writer.write(encrypted_message)

                # Send the encrypted message and its header
                await writer.drain()
                print(f"Transmitted encrypted message: {encrypted_message} at {time()}")

    async def receive_messages(self):
        reader = self.reader
        buffer_size = 1024
        cipher_suite = Fernet(self.session_key)
        # message = b''
        while True:
            print("receive_messages loop has started.")
            try:
                # Receive encrypted length header
                encrypted_header = await reader.read(100)  # Fernet 
                
                if not encrypted_header: # Connection is lost
                    break
                
                # Decrypt length header
                header = cipher_suite.decrypt(encrypted_header)
                msg_size = int.from_bytes(header, byteorder="big")
                print(f"MSG SIZE (integer): {msg_size}")
                
                # There is data, and we know the size of it
                encrypted_message = b''
                while len(encrypted_message) < msg_size:
                    print(f"Current chunk size: {len(encrypted_message)} < Total message size from header: {msg_size}")
                    
                    chunk = await reader.read(min(buffer_size, msg_size - len(encrypted_message)))

                    if not chunk: # Connection is lost?
                        print("[err] Chunk is empty! connection closed abruptly.")
                        return

                    print(f"Got chunk {chunk}, which weighs {len(chunk)} out of {msg_size}\nMIN FUNCTION RESULT: {min(buffer_size, msg_size - len(encrypted_message))}")

                    encrypted_message += chunk
                    print(f"Message size is now {len(encrypted_message)} after adding chunk.")
                
                print(f"Chunking finished; entire message in encrypted form:\n {encrypted_message}")
                # End of message
                try: 
                    decrypted_message = cipher_suite.decrypt(encrypted_message)
                    print("\nOther Person:", decrypted_message.decode('utf-8'))

                    # Queue up data for handling by tty or gui
                    self.inbox.put(decrypted_message)
                    
                except Exception as e:
                    print(f"Error at decryption: {e}")

            except Exception as e: 
                    print(f"Error receiving message: {e}")
                    break
            # Yield control to other tasks
            print("Receive messages finished. Yielding control.")
            await asyncio.sleep(0)
            

    async def outbox_checker(self):
        while True:
            try: 
                msg = self.outbox.get(block=False)
            except queue.Empty: 
                await asyncio.sleep(0)
                continue

            asyncio.create_task(self.send_message(msg))
            await asyncio.sleep(0)

    def is_command(self, cmd):
        if cmd[0:1] == b"." or cmd[0] == ".": 
            return True
        else:
            return False
    async def send_command(self, cmd): # Send plain unencrypted commands
        writer = self.writer
        if cmd == b".exit":
            self.close()
        else:
            writer.write(cmd.encode())

    async def heartbeat(self):
        while True:
            await self.send_command(".update")
            await asyncio.sleep(25)

    async def close(self, sig=None, frame=None):
        print(f"RECEIVED {sig} {frame}")
        if self.socket:
            self.writer.write(".exit".encode())
            self.socket.close()
            print("Closed socket")
        print("Closing program")
        sys.exit(0) # Exit program


