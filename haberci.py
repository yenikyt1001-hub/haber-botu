import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
import random

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
# Buraya haber bloğunun özel mail adresini yaz kanka:
BLOGGER_MAIL = "buraya_ilgili_mail@blogger.com" 

KAYNAKLAR = [
    {"ad": "NTV Son Dakika", "url": "https://www.ntv.com.tr/son-dakika.rss"},
    {"ad": "Hürriyet", "url": "https://www.hurriyet.com.tr/rss/anasayfa"},
    {"ad": "Milliyet", "url": "https://www.milliyet.com.tr/rss/rss-liste/"}
]

LOG_DOSYASI = "haber_hafiza.txt"

# --- AKILLI BAŞLIK ÜRETİCİ ---
def haber_basligi_duzenle(eski_baslik):
    on_ekler = ["FLAŞ:", "SON DAKİKA:", "Sıcak Gelişme:", "📌", "Önemli Haber:"]
    son_ekler = ["(Detaylar)", "- İşte Gelişmeler", "Haberin Ayrıntıları Burada!", "Gündem Sarsıldı!"]
    
    temiz = eski_baslik.strip()
    secim = random.randint(1, 4)
    
    if secim == 1: return f"{random.choice(on_ekler)} {temiz}"
    if secim == 2: return f"{temiz} {random.choice(son_ekler)}"
    if secim == 3: return f"Gündem: {temiz}"
    return temiz.upper()

def link_paylasildi_mi(link):
    if not os.path.exists(LOG_DOSYASI): return False
    with open(LOG_DOSYASI, "r") as f: return link in f.read()

def linki_kaydet(link):
    with open(LOG_DOSYASI, "a") as f: f.write(link + "\n")

def blogda_yayinla(baslik, icerik, kaynak_adi, link=""):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    
    # --- AKILLI ETİKET SİSTEMİ ---
    etiketler = "#Haber #Gündem"
    baslik_lower = baslik.lower()
    if "spor" in baslik_lower: etiketler += " #Spor"
    if "ekonomi" in baslik_lower or "dolar" in baslik_lower: etiketler += " #Ekonomi"
    if "siyaset" in baslik_lower: etiketler += " #Siyaset"
    if "teknoloji" in baslik_lower: etiketler += " #Teknoloji"
    
    # Yeni Akıllı Başlık
    yeni_baslik = haber_basligi_duzenle(baslik)
    
    # Konu satırı: [Yeni Başlık] [Etiketler] #[Kaynak]
    msg['Subject'] = f"{yeni_baslik} {etiketler} #{kaynak_adi.replace(' ', '')}"
    
    html_icerik = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2 style="color: #d32f2f;">📰 {yeni_baslik}</h2>
        <div style="padding: 10px; background: #f9f9f9; border-left: 5px solid #d32f2f;">
            {icerik}
        </div>
        <br>
        <a href='{link}' style="display: inline-block; padding: 10px 20px; background: #d32f2f; color: white; text-decoration: none; border-radius: 5px;">HABERİN DEVAMI İÇİN TIKLAYIN</a>
        <p style="font-size: 12px; color: #666; margin-top: 20px;">Kaynak: {kaynak_adi}</p>
    </div>
    """
    
    msg.attach(MIMEText(html_icerik, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(GMAIL_ADRES, GMAIL_SIFRE)
        server.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string()); server.quit()
        return True
    except: return False

print("--- HABER BOTU AKILLI VE ETIKETLI BASLATILDI ---")
for kaynak in KAYNAKLAR:
    try:
        feed = feedparser.parse(kaynak['url'])
        for entry in feed.entries[:5]:
            if not link_paylasildi_mi(entry.link):
                if blogda_yayinla(entry.title, entry.get('summary', ''), kaynak['ad'], entry.link):
                    print(f"✓ Paylasildi: {entry.title[:40]}...")
                    linki_kaydet(entry.link)
                    time.sleep(5)
    except Exception as e:
        print(f"Hata ({kaynak['ad']}): {e}")
