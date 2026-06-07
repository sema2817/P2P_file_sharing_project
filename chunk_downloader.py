#2BME1CENG
import socket
import json
import base64
import time
import os
import random
import shared_dicts
from pyDes import des, ECB, PAD_PKCS5

P_PRIME = 907
G_BASE = 7
LOG_FILE = "download_log.txt"
CHUNK_DIR = "my_chunks"
download_history = []

def calculate_dh_key(private_key, received_public_key):
    shared_secret = pow(received_public_key, private_key, P_PRIME)
    des_key_string = str(shared_secret).zfill(8)[:8]
    return des_key_string.encode('utf-8')

def decrypt_chunk(encrypted_string, des_key_bytes):
    encrypted_bytes = base64.b64decode(encrypted_string)
    cipher = des(des_key_bytes, ECB, pad=None, padmode=PAD_PKCS5)
    return cipher.decrypt(encrypted_bytes)

def download_chunk_worker(chunk_name, target_ip, secure=True):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(5.0)
    
    try:
        client_socket.connect((target_ip, 6001))
        
        if secure:
            my_private_key = random.randint(2, P_PRIME - 2)
            my_public_key = pow(G_BASE, my_private_key, P_PRIME)
            
            key_request = {"key": str(my_public_key)}
            client_socket.sendall(json.dumps(key_request).encode('utf-8'))
            
            response_bytes = client_socket.recv(4096)
            response_data = json.loads(response_bytes.decode('utf-8'))
            server_public_key = int(response_data["key"])
            
            shared_des_key = calculate_dh_key(my_private_key, server_public_key)

            file_request = {"requested_secured_content": chunk_name}
            client_socket.sendall(json.dumps(file_request).encode('utf-8'))
            
            file_response_bytes = b""
            while True:
                more = client_socket.recv(4096)
                if not more:
                    break
                file_response_bytes += more
                try:
                    file_response_data = json.loads(file_response_bytes.decode('utf-8'))
                    break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                
            encrypted_string = file_response_data["encrypted_chunk"]
            return decrypt_chunk(encrypted_string, shared_des_key)
            
        else:
            file_request = {"requested_content": chunk_name}
            client_socket.sendall(json.dumps(file_request).encode('utf-8'))
            
            file_response_bytes = b""
            while True:
                more = client_socket.recv(4096)
                if not more:
                    break
                file_response_bytes += more
                try:
                    file_response_data = json.loads(file_response_bytes.decode('utf-8'))
                    break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                
            encoded_data = file_response_data["data"]
            return base64.b64decode(encoded_data)
            
    except Exception as e:
        return None
    finally:
        client_socket.close()

def log_download_to_file(chunk_name, ip_address):
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{timestamp}, {chunk_name}, {ip_address}, RECEIVED\n")
    except Exception as log_err:
        pass

def find_chunk_users(file_name, part):
    candidates = [
        f"{file_name}_{part}",
        f"{file_name}{part}",
        f"{file_name}-{part}",
        f"{file_name}{part:02d}",
    ]
    current_content = shared_dicts.get_content_dict()
    
    for candidate in candidates:
        users = current_content.get(candidate)
        if users:
            return candidate, users
    return None, []

def start_downloader_ui():
    if not os.path.exists(CHUNK_DIR):
        os.makedirs(CHUNK_DIR)
        
    while True:
        print("\n========================================")
        print("          P2P DOWNLOAD MENU             ")
        print("========================================")
        print("  1 - View Contents")
        print("  2 - Download Content")
        print("  3 - History")
        print("  4 - Exit")
        print("========================================")
        
        secim = input("Seçiminiz (1-4): ").strip()

        if secim == "1" or secim.lower() == "view contents":
            current_content = shared_dicts.get_content_dict()
            
            if not current_content:
                print("Ağda henüz keşfedilen bir dosya yok.")
            else:
                print("\n--- AVAILABLE FILES IN NETWORK ---")
                unique_files = set()
                for chunk_name in current_content.keys():
                    if "_" in chunk_name:
                        base_file_name = chunk_name.rsplit("_", 1)[0]
                    elif chunk_name[-1].isdigit():
                        base_file_name = chunk_name.rstrip("0123456789")
                    else:
                        base_file_name = chunk_name
                    unique_files.add(base_file_name)
                
                for file in sorted(unique_files):
                    print(f"-> File: {file}")

        elif secim == "2" or secim.lower() == "download content":
            file_name = input("İndirilecek içerik adını girin (Örn: forest): ").strip()
            if "." in file_name:
                file_name = file_name.rsplit(".", 1)[0]
                
            mode_input = input("Güvenli indirme istiyor musunuz? (Y/N): ").strip().lower()
            is_secure = True if mode_input == 'y' else False
            
            full_file_content = b""
            download_success = True
            
            for i in range(1, 4):
                target_chunk, possible_users = find_chunk_users(file_name, i)
                
                if not possible_users:
                    print(f"\nCHUNK {file_name} part {i} CANNOT BE DOWNLOADED FROM ONLINE PEERS.")
                    download_success = False
                    break
                
                chunk_data = None
                chunk_downloaded_successfully = False
                
                for user in possible_users:
                    target_ip = shared_dicts.get_ip_by_username(user)
                    if not target_ip:
                        continue
                    
                    print(f"Requesting '{target_chunk}' from user '{user}'")
                    
                    chunk_data = download_chunk_worker(target_chunk, target_ip, secure=is_secure)
                    
                    if chunk_data:
                        chunk_downloaded_successfully = True
                        print(f"Chunk: {target_chunk}, Received from: {user}, MARKED AS \"RECEIVED\"")
                        log_download_to_file(target_chunk, target_ip)
                        
                        chunk_path = os.path.join(CHUNK_DIR, target_chunk)
                        with open(chunk_path, "wb") as cf:
                            cf.write(chunk_data)
                            
                        full_file_content += chunk_data
                        break
                    else:
                        print(f"Chunk [{target_chunk}] cannot be downloaded from [{user}]")

                if not chunk_downloaded_successfully:
                    print(f"\nCHUNK {target_chunk} CANNOT BE DOWNLOADED FROM ONLINE PEERS.")
                    download_success = False
                    break
            
            if download_success:
                try:
                    if full_file_content.startswith(b'\x89PNG\r\n\x1a\n'):
                        detected_ext = ".png"
                    elif full_file_content.startswith(b'\xff\xd8\xff'):
                        detected_ext = ".jpg"
                    else:
                        detected_ext = ".jpg"
                    
                    merged_file_path = f"{file_name}{detected_ext}"
                    with open(merged_file_path, "wb") as mf:
                        mf.write(full_file_content)
                    
                    print(f"🎉 Dosya '{merged_file_path}' başarıyla birleştirildi!")
                    download_history.append(f"[{time.strftime('%H:%M:%S')}] {file_name}{detected_ext} - Başarılı")
                except Exception as merge_err:
                    pass
            else:
                download_history.append(f"[{time.strftime('%H:%M:%S')}] {file_name} - Başarısız")
                
        elif secim == "3" or secim.lower() == "history":
            print("\n--- DOWNLOAD HISTORY ---")
            if not download_history:
                print("Henüz indirme geçmişi yok.")
            for entry in download_history:
                print(entry)
                    
        elif secim == "4" or secim.lower() == "exit":
            print("Uygulama kapatılıyor...")
            break

if __name__ == "__main__":
    start_downloader_ui()
