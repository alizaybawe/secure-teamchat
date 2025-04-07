# Secure TeamChat

This is a Python project that implements a secure team chat application suitable for cross-platform usage. 

## Features
- **Cross-Platform**: Runs on both Windows and POSIX/Linux devices.
- **GUI on Windows**: The application uses Python's built-in `tkinter` library to provide a graphical user interface (GUI) for Windows users.
- **Terminal Chat on POSIX/Linux**: On POSIX/Linux devices, the chat is run through the terminal.
- **Password-based Authentication & Encryption**: 
  - Users agree on a session password that is set by the session manager (relay).
  - The password is used to authenticate users and encrypt the session key with AES256.
  - The session key is transmitted securely using HMAC PBKDF (Password-Based Key Derivation Function).
  - Each session has its own unique key, ensuring that each session is cryptographically separated and secured.

## Requirements
- Python 3.x
- `tkinter` (for GUI on Windows)
- Libraries for cryptographic operations such as HMAC and PBKDF

## Usage

### Starting a session
1. Launch the application using the appropriate command for your platform.
   - **Windows (GUI)**: `python client.py`
   - **Linux/Unix (Terminal)**: `python client.py`

2. The session manager will ask for a session password. Once agreed upon, users can authenticate and join the session.

3. All communication in the session is encrypted using the unique session key.

## How It Works
1. **Session Password**: Users agree on a password that the session manager sets.
2. **Authentication**: The password is used to authenticate users.
3. **Secure Session Key**: The session manager derives a unique session key and transmits it to the users via a secured method (HMAC PBKDF2).
4. **Cryptographically Isolated**: Each session uses a unique session key, ensuring that data from one session is cryptographically separated from other sessions.
5. **Communication**: Users communicate securely via AES256 encryption based on the session key.

## Security Considerations
- The session key is derived and transmitted securely using HMAC PBKDF2, ensuring strong encryption.
- Only authenticated users are allowed to access the session.
- Each session has a unique session key to protect against unauthorized access or data leaks between sessions.

## License
MIT License. See `LICENSE` for more details.

## Contributing
Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your changes.
