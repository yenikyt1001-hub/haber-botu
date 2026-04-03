import feedparser
import google.genai as genai
from google.genai import types
import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# --- AYARLAR ---
GEMINI_API_KEY = "AIzaSyDAU6jVnIRBxfqrDkF9oX22xD2Ebq6Rf4U" # Kendi keyini yazmayı unutma kral!
GMAIL_ADRESIN = "yenikyt1001@gmail.com"
GMAIL_UYGULAMA_SIFRESI = "ttbe ahll meze euch"
BLOGGER_MAIL = "yenikyt1001.seslisonhaber@blogger.com"

RSS_URLS = [
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.trthaber.com/sondakika.rss",
    "https://www.sondakika.com/rss/son-dakika/"
]

def baslat():
    # Istemciyi fonksiyon icinde baslatmak daha güvenlidir
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    log_dosyasi = "haber_hafiza.txt"
    if not os.path.exists(log_dosyasi):
        with open(log_dosyasi, "w") as f: f.write("")
    with open(log_dosyasi, "r") as f:
        yayinlananlar = f.read().splitlines()

    for url in RSS_URLS:
        besleme = feedparser.parse(url)
        for haber in besleme.entries[:1]:
            if haber.link not in yayinlananlar:
                print(f"Islemde: {haber.title}")
                
                # Özgünleştirme ve Resim Promptu
                p = f"Haber: {haber.title}\n{haber.summary}\n\nBu haberi profesyonelce yeniden yaz, en sona 5 etiket ekle."
                res_metin = client.models.generate_content(model="gemini-1.5-flash", contents=p)
                
                img_p = f"Professional cinematic news photo for: {haber.title}"
                
                # Resim Oluşturma
                resim_data = None
                try:
                    res_img = client.models.generate_image(
                        model="imagen-3",
                        prompt=img_p,
                        config=types.GenerateImageConfig(aspect_ratio="16:9")
                    )
                    resim_data = res_img.generated_images[0].image_bytes
                except:
                    print("Resim olusturulamadi, metin gonderiliyor.")

                # Mail Gönderimi
                msg = MIMEMultipart()
                msg['From'] = GMAIL_ADRESIN
                msg['To'] = BLOGGER_MAIL
                msg['Subject'] = haber.title
                msg.attach(MIMEText(res_metin.text, 'plain'))
                
                if resim_data:
                    image = MIMEImage(resim_data, name="haber.jpg")
                    msg.attach(image)
                
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                    server.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                
                with open(log_dosyasi, "a") as f:
                    f.write(haber.link + "\n")
                print("Blogger'a gonderildi!")
                time.sleep(5)

if __name__ == "__main__":
    baslat()
