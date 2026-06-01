import socket
import time
import json
import os

def start_announcer(username, chunk_dir):
    announcer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    announcer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    broadcast_address = ("192.168.1.255", 6000)
    
    print(f"[ANNOUNCER] {username} icin UDP Anons servisi baslatildi (Port: 6000)...")
    
    while True:
        try:
            current_chunks = os.listdir(chunk_dir) if os.path.exists(chunk_dir) else []
            
            payload = {
                "username": username,
                "chunks": current_chunks
            }
            
            json_message = json.dumps(payload)
            message_bytes = json_message.encode('utf-8')
            
            announcer_socket.sendto(message_bytes, broadcast_address)
            
            print(f"[ANNOUNCER - SENT] Anons gonderildi: {payload}")
            
        except Exception as e:
            print(f"[ANNOUNCER - HATA] Anons gonderilirken hata olustu: {e}")
            
        time.sleep(8)


"""
import socket
Bilgisayarinin ağ kartini (Wi-Fi veya Ethernet) kontrol etmek, ağ üzerinden veri paketleri göndermek ve almak için kullanilan temel Python kütüphanesi
import time
kodun araya sure koymasi icin (8sn)
import json
ython sözlüklerini (dict), tüm dillerin ortaklaşa anlayabildiği standart bir metin formati olan JSON'a dönüştürmek için kullan

def start_announcer(username, chunk_list):
    
    announcer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Bana IPv4 adreslerini kullanan, telsiz mantigiyla (UDP) çalisan ve ağdaki herkese hizlica anons geçebileceğim bir iletişim kapisi aç. Bu kapinin adini da 'announcer_socket' koy
    (SOCK_STREAM: TCP)
    
    announcer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    socket.SOL_SOCKET: Bilgisayara, "Bu yapacağim ayar, internet protokolleriyle ilgili değil, doğrudan bu soketin  kendi genel ayarlariyla ilgili" der. Ayar menüsündeki "Genel Ayarlar" sekmesidir.

socket.SO_BROADCAST: Ayarlamak istediğimiz asil seçenektir. Bilgisayara "Ben bu telsizle herkese Broadcast yapmak istiyorum" talebini iletir.

1: Bu ayari aktif et (True) Eğer 0 yazsaydik bu özelliği kapatmiş olurdu
    
    broadcast_address = ("192.168.1.255", 6000)
    .255 yerel agdaki bagli tum cihazlar
    Ben bu anonsu 6000 numarali kapidan bağirarak yapiyorum. Beni duymak istiyorsaniz, siz de kendi bilgisayarinizdaki 6000 numarali kapiyi açin ve dinlemeye başlayin.
    
    print(f"[ANNOUNCER] {username} için UDP Anons servisi başlatildi (Port: 6000)...")
    
    while True:
        try:
Bilgisayarlar ağ üzerinden doğrudan karmaşik listeleri veya yazilari gönderemezler. Veriyi paketleyip kargoya hazir hale getirmemiz lazim
            payload = {
                "username": username,
                "chunks": chunk_list
            }
            
            json_message = json.dumps(payload)
            json.dumps komutu json standart metnine donusturur
            
            message_bytes = json_message.encode('utf-8')
            Ağ kartlari (Wi-Fi veya Ethernet) düz yazilari gönderemez, sadece elektrik sinyallerinden oluşan 0 ve 1'leri (Byte) anlar. .encode('utf-8') komutu, hazi    rlaigimiz yaziyi ağ kablosundan akip gidebilecek dijital paketçiklere (büyüklüklere) dönüştürür.
            
            announcer_socket.sendto(message_bytes, broadcast_address)
            
            print(f"[ANNOUNCER - SENT] Anons gönderildi: {payload}")
            
        except Exception as e:
            "Eğer yukaridaki adimlari yaparken elektrik kesilir, internet kopar veya beklenmedik bir hata (ariza) çikarsa programi çökertme! Hatayi e isimli değişkene kaydet ve ekrana yazdir." Böylece program hata alsa bile kapanmaz, bir sonraki 8 saniyede tekrar denemeye devam eder.
            print(f"[ANNOUNCER - HATA] Anons gönderilirken hata oluştu: {e}")
            
        time.sleep(8)
"""