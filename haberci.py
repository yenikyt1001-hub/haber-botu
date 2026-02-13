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
BLOGGER_MAIL = "yenikyt1001.sesli@blogger.com" # Burayı kontrol et kral
YOUTUBE_LINK = "https://www.youtube.com/@KANAL_ADIN"

KAYNAK_URL = "https://www.ntv.com.tr/son-dakika.rss"
LOG_DOSYASI = "sesli_hafiza.txt"

def metni_ai_ozetle(metin):
    """Metni parçalayıp rastgele birleştirerek özgünleştirir"""
    cumleler = metin.split('.')
    if len(cumleler) > 2:
        # Haberin giriş ve gelişme kısmından rastgele cümleler seçip yer değiştirir
        ozet = f"{cumleler[0]}. {random.choice(cumleler[1:-1])}."
    else:
        ozet = metin
    return ozet

def baslik_ai_yap(baslik):
    durumlar = ["Hakkında Önemli Detaylar", "Gelişmesi Şaşırttı", "Haberinde Yeni Perde", "Gündeme Bomba Gibi Düştü"]
    return f"{baslik} {random.choice(durumlar)}"

def blogda_yayinla(baslik, icerik, link=""):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    
    yeni_baslik = baslik_ai_yap(baslik)
    msg['Subject'] = f"{yeni_baslik} #Sondakika #Haber"
    
    yeni_icerik = metni_ai_ozetle(icerik)
    
    html_icerik = f"""
    <div style="font-family: 'Trebuchet MS', sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 15px; background: #fff;">
        <h2 style="color: #2c3e50; line-height: 1.4;">🎙️ {yeni_baslik}</h2>
        <div style="font-size: 17px; color: #444; background: #fdfdfd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
            {yeni_icerik}
        </div>
        <p style="text-align: center;">
            <a href='{link}' style="color: #3498db; text-decoration: none; font-weight: bold;">Haberin Kaynağı ve Detayları</a>
        </p>
        <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px; text-align: center;">
            <p style="margin-bottom: 10px; font-weight: bold;">🎧 Bu haberi sesli dinlemek ve videolarımızı izlemek için:</p>
            <a href='{YOUTUBE_LINK}?sub_confirmation=1' style="display: inline-block; padding: 12px 30px; background: #ff0000; color: white; text-decoration: none; border-radius: 50px; font-weight: bold; box-shadow: 0 4px 10px rgba(255,0,0,0.3);">🔴 YOUTUBE'DA TAKİP ET</a>
        </div>
    </div>
    """
    msg.attach(MIMEText(html_icerik, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(GMAIL_ADRES, GMAIL_SIFRE)
        server.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string()); server.quit()
        return True
    except: return False

# --- ÇALIŞTIRMA ---
feed = feedparser.parse(KAYNAK_URL)
# BAN KORUMASI: Sadece en yeni 1 haberi al!
for entry in feed.entries[:1]:
    if not any(entry.link in open(LOG_DOSYASI).read() for _ in [1] if os.path.exists(LOG_DOSYASI)):
        if blogda_yayinla(entry.title, entry.get('summary', ''), entry.link):
            print(f"Başarılı: {entry.title}")
            with open(LOG_DOSYASI, "a") as f: f.write(entry.link + "\n")
