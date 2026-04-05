import feedparser
import smtplib
import os
import time
import requests
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from google import genai

# --- GÜVENLİ AYARLAR (GitHub Secrets'tan Alır) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADRESIN = os.getenv("GMAIL_ADRESIN")
GMAIL_UYGULAMA_SIFRESI = os.getenv("GMAIL_UYGULAMA_SIFRESI")
BLOGGER_MAIL = os.getenv("BLOGGER_MAIL")

# Senin istediğin özel sabit etiketler
OZEL_ETIKETLER = "#duhirosondakika #duhirogüncel #seslihaber #seslisondakika #sondakika"
LOG_DOSYASI = "haber_hafiza.txt"

RSS_URLS = [
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.trthaber.com/sondakika.rss",
    "https://www.sondakika.com/rss/son-dakika/"
]

def baslat():
    if not GEMINI_API_KEY:
        print("HATA: GEMINI_API_KEY eksik!")
        return

    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1'})
    
    if not os.path.exists(LOG_DOSYASI):
        with open(LOG_DOSYASI, "w", encoding="utf-8") as f: f.write("")
    
    with open(LOG_DOSYASI, "r", encoding="utf-8") as f:
        yayinlananlar = f.read().splitlines()

    for url in RSS_URLS:
        besleme = feedparser.parse(url)
        for haber in besleme.entries[:2]:
            if haber.link not in yayinlananlar:
                print(f"İşlemde: {haber.title}")
                
                # Resim Çekme
                resim_data = None
                resim_url = ""
                if 'media_content' in haber: resim_url = haber.media_content[0]['url']
                elif 'description' in haber:
                    img_match = re.search(r'<img src="([^"]+)"', haber.description)
                    if img_match: resim_url = img_match.group(1)

                if resim_url:
                    try:
                        r = requests.get(resim_url, timeout=15)
                        if r.status_code == 200: resim_data = r.content
                    except: pass

                # Gemini Metin ve 10+ Etiket
                try:
                    prompt = (f"Haber: {haber.title}\nÖzet: {haber.summary}\n\n"
                             "GÖREV: Profesyonel spiker diliyle yeniden yaz. "
                             "En az 10 adet alakalı #etiket ekle.")
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    tam_metin = res.text
                    satirlar = tam_metin.strip().split('\n')
                    dinamik_etiketler = next((s for s in reversed(satirlar) if "#" in s), "#haber")
                    toplam_etiketler = f"{OZEL_ETIKETLER} {dinamik_etiketler}"
                    temiz_icerik = tam_metin.replace(dinamik_etiketler, "").strip()
                except: continue

                # Mail Gönderimi
                try:
                    msg = MIMEMultipart()
                    msg['From'] = GMAIL_ADRESIN
                    msg['To'] = BLOGGER_MAIL
                    msg['Subject'] = f"{haber.title} {toplam_etiketler}"
                    
                    body = f"{temiz_icerik.replace('\n', '<br>')}<br><br><strong>Kaynak:</strong> {haber.link}<br><br>{toplam_etiketler}"
                    msg.attach(MIMEText(body, 'html'))
                    
                    if resim_data:
                        msg.attach(MIMEImage(resim_data, name="haber.jpg"))
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                        s.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                        s.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                    
                    with open(LOG_DOSYASI, "a", encoding="utf-8") as f: f.write(haber.link + "\n")
                    print(f"Başarılı: {haber.title}")
                except Exception as e: print(f"Hata: {e}")
                time.sleep(5)

if __name__ == "__main__":
    baslat()
