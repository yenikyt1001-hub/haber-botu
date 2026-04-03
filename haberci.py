import feedparser
import google.genai as genai # Bu satiri degistirdim
from google.genai import types
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# --- AYARLAR ---
GEMINI_API_KEY = "BURAYA_API_KEY_GELECEK" 
GMAIL_ADRESIN = "yenikyt1001@gmail.com"
GMAIL_UYGULAMA_SIFRESI = "ttbe ahll meze euch"
BLOGGER_MAIL = "yenikyt1001.seslisonhaber@blogger.com"

RSS_URLS = [
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.trthaber.com/sondakika.rss",
    "https://www.sondakika.com/rss/son-dakika/"
]

# Istemciyi baslat
client = genai.Client(api_key=GEMINI_API_KEY)

def haberi_ozgunlestir(baslik, icerik):
    try:
        prompt = f"Haber: {baslik}\n{icerik}\n\nBu haberi profesyonelce yeniden yaz, en sona 5 etiket ekle."
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        
        img_prompt_req = f"Create a cinematic news image prompt for: {baslik}"
        img_res = client.models.generate_content(model="gemini-1.5-flash", contents=img_prompt_req)
        
        return response.text, img_res.text.strip()
    except Exception as e:
        print(f"Metin hatasi: {e}")
        return f"{baslik}\n\n{icerik}", "News background"

def resim_olustur(prompt):
    try:
        print("Resim olusturuluyor...")
        response = client.models.generate_image(
            model="imagen-3",
            prompt=prompt,
            config=types.GenerateImageConfig(
                aspect_ratio="16:9",
                safety_filter_level="BLOCK_ONLY_HIGH"
            )
        )
        return response.generated_images[0].image_bytes
    except Exception as e:
        print(f"Resim hatasi: {e}")
        return None

def mail_gonder(baslik, icerik, resim_bytes):
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADRESIN
        msg['To'] = BLOGGER_MAIL
        msg['Subject'] = baslik
        msg.attach(MIMEText(icerik, 'plain'))
        
        if resim_bytes:
            image = MIMEImage(resim_bytes, name="haber.jpg")
            msg.attach(image)
            
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
            server.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
        print("E-posta gönderildi.")
    except Exception as e:
        print(f"Mail hatasi: {e}")

def baslat():
    log_dosyasi = "haber_hafiza.txt"
    if not os.path.exists(log_dosyasi):
        with open(log_dosyasi, "w") as f: f.write("")
    with open(log_dosyasi, "r") as f:
        yayinlananlar = f.read().splitlines()

    for url in RSS_URLS:
        besleme = feedparser.parse(url)
        for haber in besleme.entries[:1]:
            if haber.link not in yayinlananlar:
                print(f"Isleniyor: {haber.title}")
                metin, img_p = haberi_ozgunlestir(haber.title, haber.summary)
                r_bytes = resim_olustur(img_p)
                mail_gonder(haber.title, metin, r_bytes)
                with open(log_dosyasi, "a") as f:
                    f.write(haber.link + "\n")
                time.sleep(5)

if __name__ == "__main__":
    baslat()
