import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os
import random

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.androidoyun@blogger.com"
YOUTUBE_LINK = "https://www.youtube.com/@KANAL_ADIN" # Buraya kendi kanal linkini yapıştır!

LOG_DOSYASI = "oyun_hafiza.txt"

def link_paylasildi_mi(link):
    if not os.path.exists(LOG_DOSYASI): return False
    with open(LOG_DOSYASI, "r") as f: return link in f.read()

def linki_kaydet(link):
    with open(LOG_DOSYASI, "a") as f: f.write(link + "\n")

def blogda_yayinla(baslik, link, resim_url, etiketler):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    
    # Otomatik Etiketleme
    etiket_str = " ".join([f"#{e.replace(' ', '')}" for e in etiketler])
    msg['Subject'] = f"{baslik} {etiket_str} #Android #Oyun #Hileli" 
    
    # --- YENİ TASARIM VE YOUTUBE BUTONU ---
    html_icerik = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; text-align: center; border: 2px solid #4CAF50; padding: 20px; border-radius: 15px; background-color: #fcfdfc;">
        <img src="{resim_url}" style="width: 100%; max-width: 600px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 20px;">
        
        <h2 style="color: #2e7d32; margin-bottom: 10px;">🎮 {baslik}</h2>
        <p style="color: #555; font-size: 16px;">Android Oyun Club'dan güncel hileli mod sürümü yayında!</p>
        
        <div style="margin: 25px 0;">
            <a href='{link}' style="background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 18px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">🚀 OYUNU İNDİRMEK İÇİN TIKLAYIN</a>
        </div>

        <div style="background: #fff5f5; border: 1px dashed #ff0000; padding: 15px; border-radius: 10px; margin-top: 20px;">
            <p style="font-weight: bold; color: #333; margin-bottom: 10px;">📺 Bu Oyunun Videoları YouTube Kanalımızda!</p>
            <a href='{YOUTUBE_LINK}?sub_confirmation=1' style="display: inline-block; padding: 12px 25px; background: #ff0000; color: white; text-decoration: none; border-radius: 50px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">🔴 KANALA ABONE OL</a>
        </div>

        <p style="font-size: 12px; color: #888; margin-top: 25px;">Keyifli oyunlar dileriz. Bizi takip etmeye devam edin!</p>
    </div>
    """
    
    msg.attach(MIMEText(html_icerik, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(GMAIL_ADRES, GMAIL_SIFRE)
        server.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string());
