#2BME1CENG
import threading
import sys
import os
import time
from chunk_announcer import start_announcer
from content_discovery import start_discovery, start_content_wiper
from chunk_uploader import start_uploader
from chunk_downloader import start_downloader_ui

def split_file_into_chunks(owned_file, chunk_dir):
    possible_names = [owned_file, f"{owned_file}.png", f"{owned_file}.jpg"]
    found_file = None
    for name in possible_names:
        if os.path.exists(name):
            found_file = name
            break

    if not found_file:
        print(f"[SİSTEM - UYARI] '{owned_file}' dosyası bulunamadı. Testler için otomatik oluşturuluyor...")
        found_file = f"{owned_file}.png"
        with open(found_file, "wb") as f:
            f.write(f"Orijinal dosya verisi - {owned_file} için 3 parça bölme testi.".encode('utf-8') * 50)

    with open(found_file, "rb") as f:
        file_bytes = f.read()

    file_size = len(file_bytes)
    chunk_size = (file_size + 2) // 3  

    base_name = os.path.basename(found_file)
    if "." in base_name:
        base_name = base_name.rsplit(".", 1)[0]

    print(f"[SİSTEM] '{found_file}' dosyası bölünüyor ({file_size} byte)...")
    for i in range(3):
        start = i * chunk_size
        end = min(start + chunk_size, file_size)
        chunk_data = file_bytes[start:end]

        chunk_name = f"{base_name}_{i+1}"
        chunk_path = os.path.join(chunk_dir, chunk_name)
        with open(chunk_path, "wb") as cf:
            cf.write(chunk_data)
        print(f" -> Hazırlandı: {chunk_path} ({len(chunk_data)} byte)")
        
    print(f"[SİSTEM] Başarıyla 3 chunk oluşturuldu. Sistem entegrasyonu tamamlandı.\n")

if __name__ == "__main__":
    print("==================================================")
    print("      P2P DOSYA PAYLAŞIM UYGULAMASINA HOŞ GELDİNİZ")
    print("==================================================")
    
    username = input("Kullanıcı adınızı girin: ").strip()
    if not username:
        print("Kullanıcı adı boş bırakılamaz!")
        sys.exit(1)
        
    owned_file = input("Ağa sunmak istediğiniz başlangıç dosya adını girin (Örn: forest): ").strip()
    if not owned_file:
        owned_file = "forest" 
    
    CHUNK_DIR = "my_chunks"
    if not os.path.exists(CHUNK_DIR):
        os.makedirs(CHUNK_DIR)
    
    split_file_into_chunks(owned_file, CHUNK_DIR)
    
    print(f"[SİSTEM] Profil oluşturuldu. Başlangıç içeriği: '{owned_file}'")
    print("[SİSTEM] Arka plan servisleri ateşleniyor...\n")
    
    
    announcer_thread = threading.Thread(target=start_announcer, args=(username, CHUNK_DIR), daemon=True)
    discovery_thread = threading.Thread(target=start_discovery, daemon=True)
    wiper_thread = threading.Thread(target=start_content_wiper, daemon=True)
    uploader_thread = threading.Thread(target=start_uploader, daemon=True)
    
    announcer_thread.start()
    discovery_thread.start()
    wiper_thread.start()
    uploader_thread.start()
    
    time.sleep(0.5)
    
    try:
        start_downloader_ui()
    except KeyboardInterrupt:
        print("\n[SİSTEM] Uygulama kullanıcı tarafından kapatıldı. Güvenli çıkış yapılıyor.")
        sys.exit(0)
