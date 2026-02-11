import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.androidoyun@blogger.com"

LOG_DOSYASI = "oyun_hafiza.txt"

def link_paylasildi_mi(link):
    if not os.path.exists(LOG_DOSYASI): return False
    with open(LOG_DOSYASI, "r") as f: return link in f.read()

def linki_kaydet(link):
    with open(LOG_DOSYASI, "a") as f: f.write(link + "\n")

def blogda_yayinla(baslik, link, resim_url):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    
    # Konu başlığının sonuna etiketleri ekledim kanka (#EtiketAdı şeklinde)
    msg['Subject'] = f"{baslik} #Android #Oyun #Hileli" 
    
    html_icerik = f"""
    <div style="font-family: sans-serif; text-align: center; border: 2px solid #4CAF50; padding: 15px; border-radius: 10px;">
        <img src="{resim_url}" style="width: 100%; border-radius: 5px; margin-bottom: 15px;">
        <h2 style="color: #2e7d32;">{baslik}</h2>
        <p>Android Oyun Club'dan güncel hileli mod sürümü!</p>
        <br>
        <a href='{link}' style="background: #4CAF50; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">OYUNU İNDİRMEK İÇİN TIKLAYIN</a>
        <p style="font-size: 11px; color: #888; margin-top: 20px;">Keyifli oyunlar dileriz.</p>
    </div>
    """
    msg.attach(MIMEText(html_icerik, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(GMAIL_ADRES, GMAIL_SIFRE)
        server.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string()); server.quit()
        return True
    except: return False

print("--- OYUN BOTU CALISIYOR (ETIKETLI) ---")
headers = {"User-Agent": "Mozilla/5.0"}
try:
    res = requests.get("https://androidoyun.club/", headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")
    posts = soup.find_all("div", class_="post-item", limit=5)

    for post in posts:
        a_tag = post.find("h2").find("a")
        title = a_tag.text.strip()
        link = a_tag["href"]
        img = post.find("img")["src"]

        if not link_paylasildi_mi(link):
            if blogda_yayinla(title, link, img):
                print(f"✓ Paylasildi: {title}")
                linki_kaydet(link)
                time.sleep(5)
        else:
            print(f"x Zaten var, atlandi: {title}")
except Exception as e:
    print(f"Hata: {e}")
