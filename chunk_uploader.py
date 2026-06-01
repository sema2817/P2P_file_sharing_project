import socket
import json
import threading
import base64
import os
import time
import shared_dicts
from pyDes import des, CBC, PAD_PKCS5

P_PRIME = 907
G_BASE = 7
MY_PRIVATE_KEY = 42 

CHUNK_DIR = "my_chunks"
UPLOAD_LOG_FILE = "upload_log.txt"

def calculate_dh_key(received_key):
    shared_secret = pow(received_key, MY_PRIVATE_KEY, P_PRIME)
    des_key_string = str(shared_secret).zfill(8)[:8]
    return des_key_string.encode('utf-8')

def encrypt_chunk(chunk_data, des_key_bytes):
    cipher = des(des_key_bytes, CBC, des_key_bytes, pad=None, padmode=PAD_PKCS5)
    encrypted_bytes = cipher.encrypt(chunk_data)
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def log_upload_to_file(chunk_name, recipient_name):

    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        with open(UPLOAD_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Chunk: {chunk_name} | Recipient: {recipient_name} | Status: SENT\n")
    except Exception as log_err:
        print(f"[UPLOADER - LOG HATA] Log dosyasina yazilamadi: {log_err}")

def handle_client(client_socket, client_address):
    client_ip = client_address[0]
    with shared_dicts.dict_lock:
        recipient_name = shared_dicts.ip_to_username.get(client_ip, client_ip)
        
    print(f"[UPLOADER] {recipient_name} ({client_ip}) adresinden yeni bir baglanti kabul edildi.")
    shared_des_key = None
    
    try:

        while True:
            request_bytes = client_socket.recv(4096)
            if not request_bytes:
                break
                
            request_data = json.loads(request_bytes.decode('utf-8'))
            
            if "key" in request_data:
                client_public_key = int(request_data["key"])
                my_public_key = pow(G_BASE, MY_PRIVATE_KEY, P_PRIME)
                
                shared_des_key = calculate_dh_key(client_public_key)
                
                response = {"key": str(my_public_key)}
                client_socket.sendall(json.dumps(response).encode('utf-8'))
                print(f"[UPLOADER] {recipient_name} ile anahtar degisimi basariyla tamamlandi.")
                continue 


            elif "requested secured content" in request_data:
                chunk_name = request_data["requested secured content"]
                chunk_path = os.path.join(CHUNK_DIR, chunk_name)
                
                if os.path.exists(chunk_path):
                    with open(chunk_path, "rb") as cf:
                        raw_data = cf.read()
                    
                    encrypted_string = encrypt_chunk(raw_data, shared_des_key)
                    
                    response = {
                        "chunk name": chunk_name,
                        "encrypted_chunk": encrypted_string
                    }
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    print(f"[UPLOADER - SENT] {chunk_name} sifreli olarak {recipient_name} kullanicisina gonderildi.")
                    
                    log_upload_to_file(chunk_name, recipient_name)
                else:
                    print(f"[UPLOADER - HATA] Talep edilen {chunk_name} yerelde bulunamadi!")
                break
                
            elif "requested content" in request_data:
                chunk_name = request_data["requested content"]
                chunk_path = os.path.join(CHUNK_DIR, chunk_name)
                
                if os.path.exists(chunk_path):
                    with open(chunk_path, "rb") as cf:
                        raw_data = cf.read()
                        
                    encoded_string = base64.b64encode(raw_data).decode('utf-8')
                    
                    response = {
                        "chunk name": chunk_name,
                        "data": encoded_string
                    }
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    print(f"[UPLOADER - SENT] {chunk_name} sifresiz olarak {recipient_name} kullanicisina gonderildi.")
                    
                    log_upload_to_file(chunk_name, recipient_name)
                else:
                    print(f"[UPLOADER - HATA] Talep edilen {chunk_name} yerelde bulunamadi!")
                break

    except Exception as e:
        print(f"[UPLOADER - HATA] {client_ip} istemci islemleri sirasinda hata: {e}")
    finally:
        client_socket.close()

def start_uploader():
    if not os.path.exists(CHUNK_DIR):
        os.makedirs(CHUNK_DIR)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind(('', 6001))
    server_socket.listen(10)
    print("[UPLOADER] TCP Dosya yukleme servisi hazir, baglantilar bekleniyor (Port: 6001)...")
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            print(f"[UPLOADER - CRITICAL] Sunucu dongusunde hata: {e}")


"""
import socket
import json
import threading
import base64
Şifrelenmiş ham verileri, internette bozulmadan tasinabilecek güvenli harf ve sayilara dönüştüren paketleyici
from pyDes import des, CBC, PAD_PKCS5
Verileri askeri düzeyde (DES yöntemiyle) şifrelememizi sağlayan özel bir kriptografi (şifreleme) kütüphanesi

P_PRIME = 907
G_BASE = 7
herkese açik sayilar 7 ve 907
MY_PRIVATE_KEY = 42
Bu bizim sunucumuzun "Gizli Anahtari" (gizli rengi). Bu sayi bilgisayarin hafizasindan asla disari çikmaz, internet kablosundan asla geçmez ve karsi bilgisayara bile söylenmez.

def calculate_dh_key(received_key):
    shared_secret = pow(received_key, MY_PRIVATE_KEY, P_PRIME)
    x ussu y mod z
    des_key_string = str(shared_secret).zfill(8)[:8]
    kod verileri sifrelemek icin DES kullaniyo. 8 byte olmak zorunda. str stringe donusturuyo. zfill 8 hane olana kadar onune sifir koyuyo. :8 8den fazlaysa ilk 8 hanesini alir
    return des_key_string.encode('utf-8')

def encrypt_chunk(chunk_data, des_key_bytes):
    cipher = des(des_key_bytes, CBC, des_key_bytes, pad=None, padmode=PAD_PKCS5)
    Cipher Block Chaining): Şifreleme modudur. Veriyi düz bir sira halinde değil, her bir parçayi bir önceki parçayla zincirleme bağlayarak şifreler
    CBC modunun çalişmasi için "Başlatma Vektörü" (Initialization Vector) denilen rastgele bir başlangiç değerine ihtiyaç vardir. Yazilimci kolaylik olsun diye gizli anahtarimizin aynisini başlangiç değeri olarak da kullanmiş.
    DES şifrelemesi verileri 8'er baytlik paketler halinde şifreler. Eğer bizim dosyamizin boyutu tam 8'in kati değilse (örneğin 13 baytsa), arkada kalan boşluğu doldurmak (pad etmek) gerekir. Bu komut, o boşluklari dünya standardina (PKCS5) göre otomatik doldurur.
    encrypted_bytes = cipher.encrypt(chunk_data)
    kurallara göre gerçek dosya verimizi (chunk_data) alir ve şifreler
    return base64.b64encode(encrypted_bytes).decode('utf-8')
    Şifrelenmiş ham veri bazen internet kablolarindan geçerken bazi ağ cihazlari tarafindan "yanliş ve garip karakterler" olarak algilanip bozulabilir


def handle_client(client_socket, client_address):
    print(f"[UPLOADER] {client_address} adresinden yeni bir bağlanti kabul edildi.")
    shared_des_key = None
    Bu çok önemli bir hazirlik adimidir. Yazilimci, birazdan karşi tarafla üreteceği o gizli DES şifre anahtari için hafizada boş bir yer ayiriyor. ilerde basarili olursa 8lik sey gelcek buraya
    
    try:
        request_bytes = client_socket.recv(4096)
        Müşterinin gönderdiği mesaji oku, tek seferde en fazla 4096 bayt (karakter) büyüklüğünde bir veriyi kabul et
        if not request_bytes:
            Eğer karşi bilgisayar bizimle bağlanti kurup hiçbir şey göndermeden aniden bağlantiyi keserse ici bos kalir
            return
            
        request_data = json.loads(request_bytes.decode('utf-8'))

        if "key" in request_data:
            "key" (anahtar) adinda bir etiket var mi?" * Eğer varsa, bilgisayar anlar ki bu müşteri güvenli bir transfer istiyor ve önce şifre üretmek için kendi ürettiği sayiyi bize uzatiyor
            client_public_key = int(request_data["key"])
            my_public_key = pow(G_BASE, MY_PRIVATE_KEY, P_PRIME)
            
            shared_des_key = calculate_dh_key(client_public_key)
            
            response = {"key": str(my_public_key)}
            Müşteriye göndermek üzere yeni bir cevap paketi (sözlük) hazirliyor. Bu paketin içine "key" etiketini koyuyor ve karsisina bizim az önce ürettiğimiz o hibrit sayiyi (my_public_key) yaziyor
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            json.dumps(response): Bizim hazirladiğimiz o sözlük paketini aliyor ve internet kablolarndan geçebilecek standart bir JSON metnine dönüştürüyor (Yani şuna benziyor: '{"key": "456"}').
            .encode('utf-8'): Bu düz metni, bilgisayarin ağ kartinin anlayacagi ham bayt (byte) paketine çeviriyor.
            client_socket.sendall(...): Ve tetiği çekiyor! Hazirlanan bu bayt paketini, müşterinin iletişim hattndan ona doğru firlatiyo. Karşi bilgisayar bu sayiyi alip kendi gizli sayisiyla harmanlayacak ve o da bizimle ayni şifreyi bulmuş olacak
            print(f"[UPLOADER] Anahtar değişimi başariyla tamamlandi.")
            
            request_bytes = client_socket.recv(4096)
            if request_bytes:
                request_data = json.loads(request_bytes.decode('utf-8'))
        
        if "requested_secured_content" in request_data:
            chunk_name = request_data["requested_secured_content"]
            
            raw_data = f"Bu veri {chunk_name} icerigine aittir. Gizlidir!".encode('utf-8')
            
            encrypted_string = encrypt_chunk(raw_data, shared_des_key)

            response = {
                "chunk_name": chunk_name,
                "encrypted_chunk": encrypted_string
            }
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            print(f"[UPLOADER - SENT] {chunk_name} şifreli olarak gönderildi.")

        elif "requested_content" in request_data:
            chunk_name = request_data["requested_content"]
            raw_data = f"Bu veri {chunk_name} icerigine aittir. Sifresizdir!".encode('utf-8')
            
            encoded_string = base64.b64encode(raw_data).decode('utf-8')
            
            response = {
                "chunk_name": chunk_name,
                "data": encoded_string
            }
            client_socket.sendall(json.dumps(response).encode('utf-8'))
            print(f"[UPLOADER - SENT] {chunk_name} şifresiz olarak gönderildi.")

    except Exception as e:
        print(f"[UPLOADER - HATA] İstemci işlemleri sirasinda hata: {e}")
        Bu blok sayesinde, o anki müşteride bir hata çiksa bile sunucu hatayi ekrana yazar, o müşteriyle olan defteri kapatir ve dükkani açik tutarak bir sonraki müşteriye hizmet vermeye kesintisiz devam eder.
    finally:
        client_socket.close()

def start_uploader():   
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.AF_INET: Bu sunucunun IPv4 (yani 192.168.1.5 gibi standart internet adresleri) kullanacagini belirtir
    socket.SOCK_STREAM: sunucu TCP protokoluyle caliscak
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    SO_REUSEADDR, 1: sunucu programini test ederken kapatip hemen ardindan tekrar açmak istediğinde, işletim sistemi genellikle dur port daha temizlenmedi der. bu kod direkt vermesini saglar. zaman kaydi yok
    
    server_socket.bind(('', 6001))
    '': Bu bilgisayara ait olan tüm IP adreslerini dinle. 6001: port no
    server_socket.listen(5)
    5: Bu sayi sunucunun kapisindaki "bekleme salonu" kapasitesidir. en fazla 5 musteri bekleyebilir
    print("[UPLOADER] TCP Dosya yükleme servisi hazir, bağlantilar bekleniyor (Port: 6001)...")
    
    while True:
        client_socket, client_address = server_socket.accept()
        accept() (kabul et) komutu çaliştigi an, bilgisayar duraklar ve beklemeye geçer. Ta ki dişaridan bir istemci (müşteri) 6001 numarali kapiyi çalana kadar.
Kapi çalindigi anda accept() uyanir, müşteriyi içeri alir ve bize iki değerli malzeme verir:
client_socket: Müşteriyle konuşacagimiz özel telefon hatti
client_address: Müşterinin IP adresi.
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        baska isciye veriyo. parantez ici iscinin gorevi
        client_thread.start()
"""