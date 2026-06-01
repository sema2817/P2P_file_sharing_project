import threading
ip_to_username = {}
username_to_ip = {}
content_dict = {}
dict_lock = threading.Lock()

"""
merkezi veri havuzu, tum bagimsiz parcalar bu hafiza alanini ortaklasa kullanir
kod agdaki diger bs leri gorur ve kimden hangin dosani alacagini bilir
    import threading
birden fazla isi ypamasini saglayan kutup   
    ip_to_username = {}
bos py sozlugu
    username_to_ip = {}
Mehmet'in ağdaki fiziksel adresini (IP'sini) bulup ona TCP bağlantisi açabilmesi için bu sözlüğü kullanir
    content_dict = {}
hangi dosya parcasinin(chunk) kimlerde old gosteren icerik haritasi
        Ayrica start_content_wiper fonksiyonu her 60 saniyede bir tam olarak bu sözlüğü sifirlar (.clear()).
    dict_lock = threading.Lock()
Arka planda çalisan discovery.py (Keşifçi) tam ağdan yeni bir paket alip yukardaki sözlüklere Mehmet'in bilgilerini yazmaya çalisirken (ayni milisaniyede), sen de menüden 1'e basip o sözlükleri ekrana listelemeye çalisirsan ya da wiper servisi o sözlüğü silmeye kalkarsa Python "Race Condition" (Yariş Durumu) hatasi verir ve program çöker. Çünkü birden fazla thread ayni hafiza kutusuna ayni anda dokunamaz.

Nasil Çözer? (Çözüm): threading.Lock() ifadesi yazilimsal bir asma kilit üretir
Keşifçi sözlüğe veri yazarken bu kilidi kapatir (kapiyi arkadan kilitler). O sirada menü veya wiper sözlüğe erişmek isterse kilitli kapiyii görür ve keşifçinin işinin bitmesini güvenli bir şekilde sirada bekler. Keşifçinin işi bitince kilit otomatik açilir ve siradaki thread içeri girer. Programin asla donmamasini ve çökmemesini sağlayan şey tam olarak bu kilittir
"""