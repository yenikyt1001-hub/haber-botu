import feedparser, smtplib, time, os
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.sesli@blogger.com"
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LOG_DOSYASI = "haber_hafiza.txt"

# EN KALİTELİ 3 KAYNAK
RSS_KAYNAKLARI = [
    "https://www.trthaber.com/manset_articles.rss",
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.ensonhaber.com/rss/ensonhaber.xml"
]

# GÜNCEL GEMINI BAĞLANTISI
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def ai_ile_isle(baslik, icerik):
    prompt = f"Bu haberi profesyonel spiker diliyle, 3 paragraf, tamamen özgün yaz. Sonuna 'ETİKETLER: ' ekleyip 3 anahtar kelime yaz. Haber: {baslik} - {icerik}"
    try:
        response = model.generate_content(prompt)
        raw = response.text
        if "ETİKETLER:" in raw:
            yeni_metin = raw.split("ETİKETLER:")[0].strip()
            etiketler = raw.split("ETİKETLER:")[1].strip()
        else:
            yeni_metin = raw.strip()
            etiketler = "Haber, SonDakika, Gündem"
        return yeni_metin, etiketler
    except Exception as e:
        print(f"AI Hatası: {e}")
        return icerik, "Haber, Gündem"

def blogda_yayinla(baslik, icerik, link, resim):
    ozgun_metin, etiketler = ai_ile_isle(baslik, icerik)
    msg = MIMEMultipart()
