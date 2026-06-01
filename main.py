import threading
import sys
import shared_dicts
from announcer import start_announcer
from discovery import start_discovery, start_content_wiper
from uploader import start_uploader
from downloader import start_downloader_ui

if __name__ == "__main__":
    print("==================================================")
    print("      P2P DOSYA PAYLAŞIM UYGULAMASINA HOŞ GELDİNİZ")
    print("==================================================")
    
    username = input("Kullanici adinizi girin: ").strip()
    if not username:
        print("Kullanici adi boş birakilamaz!")
        sys.exit(1)
        
    owned_file = input("Ağa sunmak istediğiniz başlangiç dosya adini girin (Örn: forest): ").strip()
    
    my_chunks = [f"{owned_file}_1", f"{owned_file}_2", f"{owned_file}_3"]
    
    print(f"\n[SİSTEM] Profil oluşturuldu. Sahip olduğunuz parçalar: {my_chunks}")
    print("[SİSTEM] Arka plan servisleri ateşleniyor...\n")
    
    announcer_thread = threading.Thread(target=start_announcer, args=(username, my_chunks), daemon=True)
    discovery_thread = threading.Thread(target=start_discovery, daemon=True)
    wiper_thread = threading.Thread(target=start_content_wiper, daemon=True)
    uploader_thread = threading.Thread(target=start_uploader, daemon=True)
    
    announcer_thread.start()
    discovery_thread.start()
    wiper_thread.start()
    uploader_thread.start()
    
    try:
        start_downloader_ui()
    except KeyboardInterrupt:
        print("\n[SİSTEM] Uygulama kapatiliyor.")