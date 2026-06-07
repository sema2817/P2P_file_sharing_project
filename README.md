# P2P_file_sharing_project# P2P File Sharing

# How to Run - Summary

1. Make sure all peers are connected to the same LAN.
2. Install the required dependency (if it is not already installed):

   pip install pyDes

3. Place the file to be shared in the appropriate folder.
4. Run the program on terminal:

   For Windows users: python main.py
   For macOS users: python3 main.py

5. Enter your username and file name.
6. The application will automatically split the file into three chunks and start all background services.

## How to Run & Limitations

This project is a P2P file-sharing application where users connected to the same local network can share and download files directly. This system enables concurrent peer discovery, chunk announcement, and hybrid secure and unsecure content transfers.

## System Architecture

It starts with running the main.py in terminal. The application divides the project into 4 main background services that run at the same time using threads:

- System Entry ('main.py'): This is the starting point. It takes your username and splits your file into exactly 3 parts without any extension (like \_1, \_2, \_3).
  Then, it starts all the background services (announcer, discovery, uploader) at the same time using threads.

- Chunk Announcer (chunk_announcer.py):Periodically broadcasts a JSON payload ('{"username": "...", "chunks": [...]}') every 8 seconds to the designated broadcast address '192.168.1.255' on port '6000'.

- Content Discovery ('content_discovery.py'):This service listens to the network on UDP port 6000 to catch announcements from other users. It connects usernames with their IP addresses so the app knows who is online.

- Chunk Downloader ('chunk_downloader.py'): This is the user menu for downloading files. It finds which users have the chunks you need. After getting all 3 parts, it merges them back into the original file and logs the download history to 'download_log.txt' as RECEIVED.

- Chunk Uploader ('chunk_uploader.py'): This runs continuously in the background and listens on TCP port 6001 for download requests. It checks what the other user wants (a key exchange, a secure chunk, or a normal chunk), sends the requested data, and saves the upload history to 'upload_log.txt'.

## Secure Download Process

When a user chooses "Secure Download", the system runs a key-exchange handshake between the client and the server to protect the data:

1. Mathematical Parameters: The system uses fixed Diffie-Hellman numbers where prime p = 907 and generator g = 7.

2. Key Exchange Protocol: The client generates a random private key using 'random.randint(2, P_PRIME - 2)', calculates its public key, and sends it as a JSON message. The server receives it and sends back its own public key over the TCP connection.

3. Symmetric Key Derivation: Both sides calculate the same shared secret number using the Diffie-Hellman formula. To fit the strict requirements of the 'pyDes' library, this number is converted to a string, padded with zeros using '.zfill(8)', and cut to exactly 8 bytes.

4. Cipher Execution: The file chunks are encrypted using the DES-ECB mode with 'PAD_PKCS5'. Finally, the encrypted data is converted into a Base64 string so it can be safely sent inside a JSON payload.

## Limitations & Constraints

1. Network Subnet Isolation: The app uses a fixed broadcast address ('192.168.1.255').

2. Fixed File Splitting: The project is designed to work with exactly 3 parts per file.

3. 60-Second Network Clean-up: The background service completely clears the discovered users and file lists every 60 seconds to keep the data fresh.

4. Memory and format limitations:To meet JSON specifications, file pieces are loaded entirely into memory, turned into strings using Base64, and sent inside JSON messages. The system is
   strictly optimized for small text files and light images ('.png', '.jpg').
