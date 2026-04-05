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

# Sabitler
OZEL_ETIKETLER = "#duhirosondakika #duhirogüncel #seslihaber #seslisondakika #sondakika"
LOG_DOSYASI = "haber_hafiza.txt"

RSS_URLS = [
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.trthaber.com/sondakika.rss",
    "https://www.sondakika.com/rss/son-dakika/"
]

def baslat():
    # API Key kontrolü
    if not GEMINI_API_KEY:
        print("HATA: GEMINI_API_KEY bulunamadı!")
        return

    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options={'api_version': 'v1'}
    )
    
    # Hafıza dosyasını kontrol et
    if not os.path.exists(LOG_DOSYASI):
        with open(LOG_DOSYASI, "w", encoding="utf-8") as f: f.write("")
    
    with open(LOG_DOSYASI, "r", encoding="utf-8") as f:
        yayinlananlar = f.read().splitlines()

    for url in RSS_URLS:
        besleme = feedparser.parse(url)
        # Her kaynaktan en son 2 habere bak
        for haber in besleme.entries[:2]:
            if haber.link not in yayinlananlar:
                print(f"Yeni haber bulundu: {haber.title}")
                
                # 1. Orijinal Resmi Çek
                resim_data = None
                resim_url = ""
                if 'media_content' in haber:
                    resim_url = haber.media_content[0]['url']
                elif 'description' in haber:
                    img_match = re.search(r'<img src="([^"]+)"', haber.description)
                    if img_match: resim_url = img_match.group(1)

                if resim_url:
                    try:
                        r = requests.get(resim_url, timeout=15)
                        if r.status_code == 200:
                            resim_data = r.content
                    except: pass

                # 2. Gemini Metin ve 10+ Etiket
                try:
                    prompt = (f"Haber Başlığı: {haber.title}\nÖzet: {haber.summary}\n\n"
                             "GÖREV: Bu haberi spiker diliyle profesyonelce yeniden yaz. "
                             "En az 10 adet alakalı etiketi başına # koyarak ekle.")
                    
                    res_metin = client.models.generate_content(
                        model="gemini-1.5-flash", 
                        contents=prompt
                    )
                    tam_metin = res_metin.text
                    
                    # Etiketleri ayır ve temizle
                    satirlar = tam_metin.strip().split('\n')
                    dinamik_etiketler = next((s for s in reversed(satirlar) if "#" in s), "#haber #sondakika")
                    temiz_icerik = tam_metin.replace(dinamik_etiketler, "").strip()
                    toplam_etiketler = f"{OZEL_ETIKETLER} {dinamik_etiketler}"
                    
                except Exception as e:
                    print(f"Gemini hatası: {e}")
                    continue

                # 3. Mail Gönderimi
                try:
                    msg = MIMEMultipart()
                    msg['From'] = GMAIL_ADRESIN
                    msg['To'] = BLOGGER_MAIL
                    msg['Subject'] = f"{haber.title} {toplam_etiketler}"
                    
                    html_body = f"""
                    <html>
                    <body>
                        <p>{temiz_icerik.replace('\n', '<br>')}</p>
                        <br>
                        <p><strong>Kaynak:</strong> <a href="{haber.link}">{haber.link}</a></p>
                        <br>
                        <p style="color:gray; font-size:12px;">{toplam_etiketler}</p>
                    </body>
                    </html>
                    """
                    msg.attach(MIMEText(html_body, 'html'))
                    
                    if resim_data:
                        image = MIMEImage(resim_data, name="haber.jpg")
                        msg.attach(image)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                        server.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                    
                    # Başarılıysa hafızaya ekle
                    with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
                        f.write(haber.link + "\n")
                    print(f"Yayınlandı: {haber.title}")
                    
                except Exception as e:
                    print(f"Mail gönderilemedi: {e}")
                
                time.sleep(5)

if __name__ == "__main__":
    baslat()
