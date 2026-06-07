#2BME1CENG
import socket
import json
import threading
import base64
import os
import time
import shared_dicts
from pyDes import des, ECB, PAD_PKCS5

P_PRIME = 907
G_BASE = 7
MY_PRIVATE_KEY = 42

CHUNK_DIR = "my_chunks"
UPLOAD_LOG_FILE = "upload_log.txt"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '0.0.0.0'
    finally:
        s.close()
    return local_ip

def calculate_dh_key(received_key):
    shared_secret = pow(received_key, MY_PRIVATE_KEY, P_PRIME)
    des_key_string = str(shared_secret).zfill(8)[:8]
    return des_key_string.encode('utf-8')

def encrypt_chunk(chunk_data, des_key_bytes):
    cipher = des(des_key_bytes, ECB, pad=None, padmode=PAD_PKCS5)
    encrypted_bytes = cipher.encrypt(chunk_data)
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def log_upload_to_file(chunk_name, recipient_name):
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        with open(UPLOAD_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp}, {chunk_name}, {recipient_name}, SENT\n")
    except Exception:
        pass

def handle_client(client_socket, client_address):
    client_ip = client_address[0]
    recipient_name = shared_dicts.get_username_by_ip(client_ip)
        
    print(f"[UPLOADER] {recipient_name} ({client_ip}) istemcisinden TCP bağlantısı alındı.")
    shared_des_key = None
    
    try:
        while True:
            request_bytes = client_socket.recv(4096)
            if not request_bytes:
                break
                
            try:
                request_data = json.loads(request_bytes.decode('utf-8'))
            except json.JSONDecodeError:
                continue
            
            if "key" in request_data:
                client_public_key = int(request_data["key"])
                my_public_key = pow(G_BASE, MY_PRIVATE_KEY, P_PRIME)
                shared_des_key = calculate_dh_key(client_public_key)
                
                response = {"key": str(my_public_key)}
                client_socket.sendall(json.dumps(response).encode('utf-8'))
                print(f"[UPLOADER] {recipient_name} ile ortak DES anahtarı kuruldu.")
                continue

            elif "requested_secured_content" in request_data:
                if shared_des_key is None:
                    print(f"[UPLOADER - UYARI] Anahtar değişimi yapılmadan güvenli içerik istendi!")
                    continue
                
                chunk_name = request_data["requested_secured_content"]
                chunk_path = os.path.join(CHUNK_DIR, chunk_name)
                
                if os.path.exists(chunk_path):
                    with open(chunk_path, "rb") as cf:
                        raw_data = cf.read()
                    
                    encrypted_string = encrypt_chunk(raw_data, shared_des_key)
                    response = {
                        "chunk_name": chunk_name,
                        "encrypted_chunk": encrypted_string
                    }
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    print(f"[UPLOADER] {chunk_name} (ŞİFRELİ) -> {recipient_name}")
                    log_upload_to_file(chunk_name, recipient_name)
                continue
                
            elif "requested_content" in request_data:
                chunk_name = request_data["requested_content"]
                chunk_path = os.path.join(CHUNK_DIR, chunk_name)
                
                if os.path.exists(chunk_path):
                    with open(chunk_path, "rb") as cf:
                        raw_data = cf.read()
                        

                    encoded_string = base64.b64encode(raw_data).decode('utf-8')
                    
                    response = {
                        "chunk_name": chunk_name,
                        "data": encoded_string,
                        "team_info": "TEAM MEMBERS: Sema, Gozde, Ipek" 
                    }
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    print(f"[UPLOADER] {chunk_name} (ŞİFRESİZ) -> {recipient_name}")
                    log_upload_to_file(chunk_name, recipient_name)
                continue

    except Exception as e:
        pass
    finally:
        client_socket.close()
        print(f"[UPLOADER] {recipient_name} ile olan TCP bağlantısı sonlandırıldı.")

def start_uploader():
    if not os.path.exists(CHUNK_DIR):
        os.makedirs(CHUNK_DIR)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    my_ip = get_local_ip()
    server_socket.bind((my_ip, 6001))
    server_socket.listen(10)
    print(f"[UPLOADER] TCP Dosya yükleme servisi başlatıldı ({my_ip}:6001)...")
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            pass

if __name__ == "__main__":
    start_uploader()
