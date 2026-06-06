import socket
import json
import time
import os


ANNOUNCE_INTERVAL = 8  

BROADCAST_IP = '192.168.1.255' 

def start_announcer(username, chunk_dir):
    announce_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    announce_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    announce_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print(f"[ANNOUNCER] Anonslayıcı başlatıldı. Kullanıcı: '{username}', Hedef: {BROADCAST_IP}:6000")

    while True:
        try:
            if os.path.exists(chunk_dir):
                chunks = [f for f in os.listdir(chunk_dir) if not f.startswith(".")]
            else:
                chunks = []

            payload = {
                "username": username,
                "chunks": chunks
            }
            message = json.dumps(payload).encode('utf-8')

            announce_socket.sendto(message, (BROADCAST_IP, 6000))
            

        except Exception as e:
            pass

        time.sleep(ANNOUNCE_INTERVAL)

if __name__ == "__main__":
    MY_USERNAME = "Sema"
    MY_CHUNK_DIR = "my_chunks"
    
    start_announcer(MY_USERNAME, MY_CHUNK_DIR)
