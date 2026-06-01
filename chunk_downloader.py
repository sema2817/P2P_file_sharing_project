import socket
import json
import base64
import time
import os
import random
import shared_dicts
from pyDes import des, CBC, PAD_PKCS5

P_PRIME = 907
G_BASE = 7

download_history = []
LOG_FILE = "download_log.txt"
CHUNK_DIR = "my_chunks"

def calculate_dh_key(private_key, received_public_key):
    shared_secret = pow(received_public_key, private_key, P_PRIME)
    des_key_string = str(shared_secret).zfill(8)[:8]
    return des_key_string.encode('utf-8')

def decrypt_chunk(encrypted_string, des_key_bytes):
    encrypted_bytes = base64.b64decode(encrypted_string)
    cipher = des(des_key_bytes, CBC, des_key_bytes, pad=None, padmode=PAD_PKCS5)
    decrypted_bytes = cipher.decrypt(encrypted_bytes)
    return decrypted_bytes.decode('utf-8')

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

            file_request = {"requested secured content": chunk_name}
            client_socket.sendall(json.dumps(file_request).encode('utf-8'))
            
            file_response_bytes = client_socket.recv(4096)
            file_response_data = json.loads(file_response_bytes.decode('utf-8'))
            
            encrypted_string = file_response_data["encrypted_chunk"]
            decrypted_data = decrypt_chunk(encrypted_string, shared_des_key)
            return decrypted_data
            
        else:
            file_request = {"requested content": chunk_name}
            client_socket.sendall(json.dumps(file_request).encode('utf-8'))
            
            file_response_bytes = client_socket.recv(4096)
            file_response_data = json.loads(file_response_bytes.decode('utf-8'))
            
            encoded_data = file_response_data["data"]
            decrypted_data = base64.b64decode(encoded_data).decode('utf-8')
            return decrypted_data
            
    except Exception as e:
        return None
    finally:
        client_socket.close()

def log_download_to_file(chunk_name, ip_address):
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Chunk: {chunk_name} | Downloaded From IP: {ip_address}\n")
    except Exception as log_err:
        print(f"[LOG HATA] Dosyaya log yazilamadi: {log_err}")

def start_downloader_ui():
    if not os.path.exists(CHUNK_DIR):
        os.makedirs(CHUNK_DIR)
        
    time.sleep(1) 
    
    while True: 
        print("\n========================================")
        print("          P2P DOWNLOAD MENU             ")
        print("========================================")
        print("-> Type 'View Contents'   : Available files in network")
        print("-> Type 'Download Content': Initiate a chunk download")
        print("-> Type 'History'         : Show download history")
        print("-> Type 'Exit'            : Close program")
        print("========================================")
        
        secim = input("Enter your command: ").strip()


        if secim.lower() == "view contents":
            with shared_dicts.dict_lock:
                if not shared_dicts.content_dict:
                    print("[UI] Agda henuz kesfedilen bir dosya yok.")
                else:
                    print("\n--- AVAILABLE FILES IN NETWORK (NO REPLICAS) ---")
                    unique_files = set()
                    
                    for chunk_name in shared_dicts.content_dict.keys():
                        if " " in chunk_name:
                            base_file_name = chunk_name.rsplit(" ", 1)[0]
                            unique_files.add(base_file_name)
                    
                    for file in unique_files:
                        print(f"-> File: {file}.png")
                        

        elif secim.lower() == "download content":
            file_name = input("Enter content name to download (e.g., forest): ").strip()
            mode_input = input("Do you want secure download? (Y/N): ").strip().lower()
            is_secure = True if mode_input == 'y' else False
            
            full_file_content = ""
            download_success = True
            
            for i in range(1, 4):
                target_chunk = f"{file_name} {i}" 
                
                with shared_dicts.dict_lock:
                    possible_users = shared_dicts.content_dict.get(target_chunk, [])
                
                if not possible_users:
                    print(f"[UI] CHUNK {target_chunk} CANNOT BE DOWNLOADED FROM ONLINE PEERS. (No owners found)")
                    download_success = False
                    break
                
                chunk_data = None
                chunk_downloaded_successfully = False
                
                for user in possible_users:
                    target_ip = shared_dicts.username_to_ip.get(user)
                    if not target_ip:
                        continue
                    
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                    print(f"[UI][{timestamp}] Requesting '{target_chunk}' from user '{user}' ({target_ip})...")
                    
                    chunk_data = download_chunk_worker(target_chunk, target_ip, secure=is_secure)
                    
                    if chunk_data:
                        chunk_downloaded_successfully = True
                        print(f"[{timestamp}] Chunk '{target_chunk}' received from '{user}' ({target_ip}) - MARKED AS 'RECEIVED'")
                        
                        log_download_to_file(target_chunk, target_ip)
                        
                        chunk_path = os.path.join(CHUNK_DIR, target_chunk)
                        with open(chunk_path, "w", encoding="utf-8") as cf:
                            cf.write(chunk_data)
                            
                        full_file_content += chunk_data
                        break
                    else:
                        print(f"[UI - UYARI] Chunk {target_chunk} cannot be downloaded from {user}.")

                if not chunk_downloaded_successfully:
                    print(f"\n[UI - CRITICAL] CHUNK {target_chunk} CANNOT BE DOWNLOADED FROM ONLINE PEERS.")
                    download_success = False
                    break
            
            if download_success:
                print(f"\n[UI] All 3 chunks of '{file_name}' obtained successfully (Req. 2.3.0-I).")
                
                try:
                    merged_file_path = f"{file_name}.png"
                    with open(merged_file_path, "w", encoding="utf-8") as mf:
                        mf.write(full_file_content)
                    print(f"🎉 [UI] File '{merged_file_path}' has been successfully downloaded and merged!")
                except Exception as merge_err:
                    print(f"[UI - HATA] Dosya birlestirilirken hata olustu: {merge_err}")

                download_history.append(f"[{time.strftime('%H:%M:%S')}] {file_name}.png - Success (Secure: {is_secure})")
            else:
                download_history.append(f"[{time.strftime('%H:%M:%S')}] {file_name}.png - Failed")
                
        elif secim.lower() == "history":
            print("\n--- DOWNLOAD HISTORY ---")
            if not download_history:
                print("No downloads recorded yet.")
            else:
                for entry in download_history:
                    print(entry)
                    
        elif secim.lower() == "exit":
            print("Exiting application...")
            break
        else:
            print("Invalid command! Please type exact keywords ('View Contents', 'Download Content', 'History').")
            

"""
import socket
import json
import base64
import time
import shared_dicts
from pyDes import des, CBC, PAD_PKCS5

P_PRIME = 907
G_BASE = 7
MY_PRIVATE_KEY = 19 

def calculate_dh_key(received_key):
    shared_secret = pow(received_key, MY_PRIVATE_KEY, P_PRIME)
    des_key_string = str(shared_secret).zfill(8)[:8]
    return des_key_string.encode('utf-8')

def decrypt_chunk(encrypted_string, des_key_bytes):
    encrypted_bytes = base64.b64decode(encrypted_string)
    cipher = des(des_key_bytes, CBC, des_key_bytes, pad=None, padmode=PAD_PKCS5)
    des_key_bytes: Bir önceki fonksiyonda ürettiğimiz 8 byte'lIk gizli şifreleme anahtarI
    CBC: DES, verileri 8'er byte'lIk bloklar halinde çözer. CBC modu, bir bloğu çözerken bir önceki bloğun şifreli verisinden de yararlanIr. Bu sayede şifreleme çok daha güvenli hale gelir (aynI kelimeler farklI bloklarda farklI şifrelenir)
    des_key_bytes: CBC modunun çalisabilmesi için ilk bloğun "bir önceki blok" yerine kullanacagi bir başlangic değerine (Initialization Vector) ihtiyaci vardir. Normalde bu değerin tamamen rastgele olmasi istenir ancak bu kodda pratiklik olsun diye anahtarin kendisi IV olarak verilmiştir.
    pad=None & padmode=PAD_PKCS5: DES blok blok (8 byte) çalistigi için, şifrelenecek orijinal veri tam 8'in kati olmayabilir (örn: 13 byte). Eksik kalan kisimlari standart bir şekilde doldurmak için uploader tarafi PKCS5 dolgusu yapmistir. Burada da şifre çözülürken bu dolgularin otomatik olarak temizlenmesi söyleniyor.
    decrypted_bytes = cipher.decrypt(encrypted_bytes)
    return decrypted_bytes.decode('utf-8')


def download_chunk_worker(chunk_name, target_ip, secure=True):
    Eğer kullanici menüden güvenli indirmeyi seçerse burasi True kalir ve Diffie-Hellman/DES şifreleme adimlari devreye girer. Eğer şifresiz düz indirme istenirse bu değer disaridan False olarak gönderilir.
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    shared_des_key = None
    Eğer secure=True ise, fonksiyonun devam eden satirlarinda bu shared_des_key değişkeninin içi Diffie-Hellman fonksiyonundan gelen 8 byte'lik anahtar ile doldurulacaktir. Sifresiz modda ise None olarak kalmaya devam eder.

    try:
        client_socket.connect((target_ip, 6001))
        Hedef bilgisayar (target_ip) o an internete/ağa bağli olmayabilir.
        Karsi bilgisayar acik olsa bile P2P programi (uploader tarafi) çalismiyor veya 6001 portunu açmamis olabilir.
        Araya bir antivirüs veya Windows Güvenlik Duvari (Firewall) girip bu bağlantiyi engelliyor olabilir. o yuzden try blogu lazim
        
        if secure:
            my_public_key = pow(G_BASE, MY_PRIVATE_KEY, P_PRIME)
            
            key_request = {"key": str(my_public_key)}
            Hesaplanan acik anahtar, karsi tarafin (uploader) rahatça okuyup işleyebilmesi için standart bir sözlük (dictionary) yapisina dönüştürülür. Python'daki bu sözlük yapisi, ağ üzerinden gönderilmeye hazir bir paket haline getirilir
            client_socket.sendall(json.dumps(key_request).encode('utf-8'))
            
            response_bytes = client_socket.recv(4096)
            4096: tek seferde alinabilecek max byte
            response_data = json.loads(response_bytes.decode('utf-8'))
            server_public_key = int(response_data["key"])
            
            shared_des_key = calculate_dh_key(server_public_key)
            
            file_request = {"requested_secured_content": chunk_name}
            client_socket.sendall(json.dumps(file_request).encode('utf-8'))
            
            file_response_bytes = client_socket.recv(4096)
            file_response_data = json.loads(file_response_bytes.decode('utf-8'))
            
            encrypted_string = file_response_data["encrypted_chunk"]
            decrypted_data = decrypt_chunk(encrypted_string, shared_des_key)
            return decrypted_data
            ------------------------------------------------------  
        else:
            file_request = {"requested_content": chunk_name}
            client_socket.sendall(json.dumps(file_request).encode('utf-8'))
            
            file_response_bytes = client_socket.recv(4096)
            file_response_data = json.loads(file_response_bytes.decode('utf-8'))
            
            encoded_data = file_response_data["data"]
            decrypted_data = base64.b64decode(encoded_data).decode('utf-8')
            return decrypted_data
            
    except Exception as e:
        print(f"[DOWNLOADER - HATA] {chunk_name} indirilirken hata oluştu ({target_ip}): {e}")
        return None
    finally:
        client_socket.close()

def start_downloader_ui():
    time.sleep(2) 
    
    while True:
        print("\n--- P2P DOSYA PAYLAŞIM MENÜSÜ ---")
        print("1. Ağdaki Aktif İçerikleri Listele (Discovery)")
        print("2. Dosya İndir (Download - 3 Parça Halinde)")
        print("3. Çikiş")
        secim = input("Seçiminiz (1/2/3): ")
        
        if secim == "1":
            with shared_dicts.dict_lock:
                if not shared_dicts.content_dict:
                    print("[UI] Ağda henüz keşfedilen bir dosya parçasi yok.")
                else:
                    print("\n--- AĞDA BULUNAN DOSYALAR VE SAHİPLERİ ---")
                    for chunk, ips in shared_dicts.content_dict.items():
                        owners = [shared_dicts.ip_to_username.get(ip, ip) for ip in ips]
                        print(f"-> Parça: '{chunk}' | Bulunduğu Kişiler: {owners}")
                        
        elif secim == "2":
            file_name = input("İndirmek istediğiniz dosya adini girin (Örn: forest): ").strip()
            mode_input = input("Güvenli indirme aktif olsun mu? (E/H): ").strip().lower()
            is_secure = True if mode_input == 'e' else False
            
            full_file_content = ""
            download_success = True
            
            for i in range(1, 4):
                target_chunk = f"{file_name}_{i}"
                
                with shared_dicts.dict_lock:
                    possible_ips = shared_dicts.content_dict.get(target_chunk, [])
                
                if not possible_ips:
                    print(f"[UI] Üzgünüm, {target_chunk} ağda hiç kimsede bulunamadi!")
                    download_success = False
                    break
                
                chunk_data = None
                for ip in possible_ips:
                    owner_name = shared_dicts.ip_to_username.get(ip, ip)
                    print(f"[UI] {target_chunk} parçasi {owner_name} cihazindan talep ediliyor...")
                    chunk_data = download_chunk_worker(target_chunk, ip, secure=is_secure)
                    if chunk_data:
                        break
                
                if chunk_data:
                    full_file_content += chunk_data
                    print(f"[UI - RECEIVED] {target_chunk} başariyla alindi.")
                else:
                    print(f"[UI] {target_chunk} parçasi hiçbir kaynaktan indirilemedi!")
                    download_success = False
                    break
            
            if download_success:
                print("\n🎉 TEBRİKLER! Dosyanin tüm parçalari başariyla indirildi ve birleştirildi.")
                print(f"--- DOSYA İÇERİĞİ ---\n{full_file_content}\n---------------------")
                
        elif secim == "3":
            print("Uygulamadan çikiliyor...")
            break
        else:
            print("Geçersiz seçim, lütfen tekrar deneyin.")
"""