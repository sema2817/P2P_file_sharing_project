import socket
import json
import time
import threading
import shared_dicts

def start_discovery():
    discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    discovery_socket.bind(('', 6000))
    
    print("[DISCOVERY] UDP Keşif servisi başlatıldı, port 6000 dinleniyor...")
    
    while True:
        try:
            data, addr = discovery_socket.recvfrom(4096)
            sender_ip = addr[0]
            
            json_message = data.decode('utf-8')
            payload = json.loads(json_message)
            
            username = payload.get("username")
            chunks = payload.get("chunks", [])
            
            if not username:
                continue

            shared_dicts.update_ip_to_username(sender_ip, username)
            
            shared_dicts.update_username_to_ip(username, sender_ip)
            
            shared_dicts.update_content_dict(chunks, username)

            chunks_str = ", ".join(chunks)
            print(f"{username} {chunks_str}")
            
        except Exception as e:
            pass

def start_content_wiper():
    while True:
        time.sleep(60)
        shared_dicts.clear_content_dict()

if __name__ == "__main__":  
    discovery_thread = threading.Thread(target=start_discovery, daemon=True)
    wiper_thread = threading.Thread(target=start_content_wiper, daemon=True)
    
    discovery_thread.start()
    wiper_thread.start()
    

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[DISCOVERY] Keşif servisi kullanıcı tarafından kapatıldı.")
