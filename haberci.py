import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "senin_haber_blogu_mailin@blogger.com" 

KAYNAKLAR = [
    {"ad": "NTV Son Dakika", "url": "https://www.ntv.com.tr/son-dakika.rss"},
    {"ad": "Hürriyet", "url": "https://www.hurriyet.com.tr/rss/anasayfa"},
    {"ad": "Milliyet", "url": "https://www.milliyet.com.tr/rss/rss-liste/"}
]

LOG_DOSYASI = "haber_hafiza.txt"

def link_paylasildi_mi(link):
    if not os.path.exists(LOG_DOSYASI): return False
    with open(LOG_DOSYASI, "r") as f: return link in f.read()

def linki_kaydet(link):
    with open(LOG_DOSYASI, "a") as f: f.write(link + "\n")

def blogda_yayinla(baslik, icerik, kaynak_adi, link=""):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    
    # HABER ETİKETLERİ: Başlığa göre otomatik etiket seçimi
    etiketler = "#Haber #Gündem"
    if "siyaset" in baslik.lower(): etiketler += " #Siyaset"
    if "ekonomi" in baslik.lower() or "dolar" in baslik.lower(): etiketler += " #Ekonomi"
    if "spor" in baslik.lower(): etiketler += " #Spor"
    
    msg['Subject'] = f"{baslik} {etiketler} #{kaynak_adi.replace(' ', '')}"
    
    html_icerik = f"<h2>📰 {baslik}</h2><p>{icerik}</p><br><a href='{link}'>Haberin Devamı...</a><br>Kaynak: {kaynak_adi}"
    msg.attach(MIMEText(html_icerik, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(GMAIL_ADRES, GMAIL_SIFRE)
        server.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string()); server.quit()
        return True
    except: return False

print("--- HABER BOTU ETIKETLI CALISIYOR ---")
for kaynak in KAYNAKLAR:
    feed = feedparser.parse(kaynak['url'])
    for entry in feed.entries[:5]:
        if not link_paylasildi_mi(entry.link):
            if blogda_yayinla(entry.title, entry.get('summary', ''), kaynak['ad'], entry.link):
                print(f"✓ Haber Paylasildi: {entry.title[:40]}")
                linki_kaydet(entry.link)
                time.sleep(5)
