import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.telefonicerik@blogger.com"

LOG_DOSYASI = "paylasilanlar.txt"

def link_paylasildi_mi(link):
    if not os.path.exists(LOG_DOSYASI): return False
    with open(LOG_DOSYASI, "r") as f: return link in f.read()

def linki_kaydet(link):
    with open(LOG_DOSYASI, "a") as f: f.write(link + "\n")

def blogda_yayinla(baslik, icerik, kaynak_adi, link=""):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    
    # --- AKILLI TELEFON ETIKETLERI ---
    etiketler = "#Teknoloji #AkıllıTelefon #Mobil"
    baslik_lower = baslik.lower()
    
    if "iphone" in baslik_lower or "apple" in baslik_lower: etiketler += " #Apple #iPhone"
    if "samsung" in baslik_lower: etiketler += " #Samsung #Galaxy"
    if "xiaomi" in baslik_lower or "redmi" in baslik_lower: etiketler += " #Xiaomi"
    if "fiyat" in baslik_lower or "indirim" in baslik_lower: etiketler += " #FiyatHaberleri"
    if "inceleme" in baslik_lower: etiketler += " #İnceleme"
    
    # Konu satırına etiketleri ekliyoruz
    msg['Subject'] = f"{baslik} {etiketler}"
    
    html_icerik = f"<h2>📱 {baslik}</h2><p>{icerik}</p><br><a href='{link}'>Haberin Detayları...</a><br>Kaynak: {kaynak_adi}"
    msg.attach(MIMEText(html_icerik, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(GMAIL_ADRES, GMAIL_SIFRE)
        server.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string()); server.quit()
        return True
    except: return False

print("--- TELEFON BOTU ETIKETLI CALISIYOR ---")
KAYNAKLAR = [
    {"ad": "DonanımHaber Mobil", "url": "https://www.donanimhaber.com/rss/tum/akilli-telefonlar"},
    {"ad": "Webtekno", "url": "https://www.webtekno.com/rss.xml"},
    {"ad": "ShiftDelete", "url": "https://shiftdelete.net/feed"}
]

keywords = ["telefon", "akıllı", "smartphone", "iphone", "samsung", "xiaomi", "redmi", "fiyat", "tanıtıldı", "inceleme"]

for kaynak in KAYNAKLAR:
    feed = feedparser.parse(kaynak['url'])
    for entry in feed.entries[:10]:
        metin = (entry.title + entry.get('summary', '')).lower()
        if any(kw in metin for kw in keywords):
            if not link_paylasildi_mi(entry.link):
                if blogda_yayinla(entry.title, entry.get('summary', ''), kaynak['ad'], entry.link):
                    print(f"✓ Telefon Haberi Paylasildi: {entry.title[:40]}")
                    linki_kaydet(entry.link)
                    time.sleep(5)
