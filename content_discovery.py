import socket
import json
import threading
import time
import shared_dicts

def start_discovery():
    discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    discovery_socket.bind(('', 6000))
    
    print("[DISCOVERY] UDP Kesif servisi baslatildi, ag dinleniyor (Port: 6000)...")
    
    while True:
        try:
            data, addr = discovery_socket.recvfrom(1024)
            sender_ip = addr[0]  
            
            json_message = data.decode('utf-8')
            payload = json.loads(json_message)
            
            username = payload.get("username")
            chunks = payload.get("chunks", [])
            
            with shared_dicts.dict_lock:
                shared_dicts.ip_to_username[sender_ip] = username
                
                shared_dicts.username_to_ip[username] = sender_ip

                for chunk in chunks:
                    if chunk not in shared_dicts.content_dict:
                        shared_dicts.content_dict[chunk] = []
                    
                    if username not in shared_dicts.content_dict[chunk]:
                        shared_dicts.content_dict[chunk].append(username)

            chunks_str = ", ".join(chunks)
            print(f"[DISCOVERY - ONLINE] {username} : {chunks_str}")
            print(f"[DISCOVERY - RECEIVED] {username} ({sender_ip}) cihazindan anons alindi.")
            
        except Exception as e:
            print(f"[DISCOVERY - HATA] Paket alinirken veya islenirken hata: {e}")

def start_content_wiper():
    print("[WIPER] Icerik temizleme (Wiper) servisi aktif edildi.")
    while True:
        time.sleep(60)
        
        with shared_dicts.dict_lock:
            shared_dicts.content_dict.clear()
            print("[WIPER - REFRESH] Icerik sozlucu (Content Dictionary) temizlendi. Yeni anonslar bekleniyor...")

"""
import socket
import json
import threading
import time
import shared_dicts

def start_discovery():
    Bu fonksiyonun temel amaci, ağa bağli diğer bilgisayarlarin "Ben buradayim, kullanici adim bu ve elimde şu dosyalar var" diyerek çevreye yayinladigi (UDP Broadcast) mesajlari yakalamaktir.
    discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    discovery_socket.bind(('', 6000))
    ilk kisim bos olunca hangi ag kartindan gelrise gelsin kabul et demek
    6000 numarali kapiyi bana ayir. Bu kapiya gelen tüm mesajlari benim programima (discovery_socket) yönlendir. 
    
    print("[DISCOVERY] UDP Keşif servisi başlatildi, ağ dinleniyor (Port: 6000)...")
    
    while True:
        try:
            ilk koruma duvari
            data, addr = discovery_socket.recvfrom(1024)
            veri paketini ikiye boler icerik data, ip address. recieve from. 1024 max1024byte kabul et
            sender_ip = addr[0]
            bir bilgisayarin adresi sadece tek bir bilgiden oluşmaz. addr dediğimiz şey, bilgisayarin hafizasinda ikili bir paket (buna Python'da tuple denir) olarak tutulur ve şuna benzer: ('192.168.1.50', 5005) (ip adresi, port no)
            
            json_message = data.decode('utf-8')
            
            payload = json.loads(json_message)
            Sana verdiğim bu JSON formatindaki düz yaziyi incele, süslü parantezleri ve iki nokta üst üsteleri çözerek bunu Python'in anlayacaği akilli bir veri yapisina dönüştü
            

            username = payload.get("username")
            İşte .get() komutu programin çökmesini engelleyen güvenli bir kapicidir: "Varsa ver, yoksa programi çökertme!" der.
            göndermediyse, program çökmez; username kutusunun içine None yazar.
            chunks = payload.get("chunks", [])
            Eğer paketin içinde 'chunks' diye bir şey bulamazsan, bu kutuyu boş biirakma (None yapma), içine boş bir liste [] koy.
        

            with shared_dicts.dict_lock:
                herkes ayni anda yazmasin diye "Güvenli odaya giriyorum, kapiyi kilitle!" emridir. satiri bittiği anda kapiyi otomatik olarak bir sonraki bilgisayar için geri açar (donmasin diye)
                shared_dicts.ip_to_username[sender_ip] = username
                Örnek: 192.168.1.50 adresinin karşisina "Ahmet123" yazdi
                shared_dicts.username_to_ip[username] = sender_ip
                
                for chunk in chunks:
                    if chunk not in shared_dicts.content_dict:
                        shared_dicts.content_dict[chunk] = []
                    
                    if sender_ip not in shared_dicts.content_dict[chunk]:
                        shared_dicts.content_dict[chunk].append(sender_ip)
                        
            print(f"[DISCOVERY - RECEIVED] {username} ({sender_ip}) cihazindan anons alindi.")
            
        except Exception as e:
            print(f"[DISCOVERY - HATA] Paket alinirken veya işlenirken hata: {e}")

def start_content_wiper():
    print("[WIPER] İçerik temizleme (Wiper) servisi aktif edildi.")
    while True:
        time.sleep(60)
        
        with shared_dicts.dict_lock:
            shared_dicts.content_dict.clear()
            print("[WIPER - REFRESH] İçerik sözlüğü (Content Dictionary) temizlendi. Yeni anonslar bekleniyor...")
"""