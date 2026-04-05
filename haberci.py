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

# --- AYARLAR ---
GEMINI_API_KEY = "AIzaSyDAU6jVnIRBxfqrDkF9oX22xD2Ebq6Rf4U"
GMAIL_ADRESIN = "yenikyt1001@gmail.com"
GMAIL_UYGULAMA_SIFRESI = "ttbe ahll meze euch"
BLOGGER_MAIL = "yenikyt1001.seslisonhaber@blogger.com"

# Senin istediğin özel sabit etiketler
OZEL_ETIKETLER = "#duhirosondakika #duhirogüncel #seslihaber #seslisondakika #sondakika"

RSS_URLS = [
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.trthaber.com/sondakika.rss",
    "https://www.sondakika.com/rss/son-dakika/"
]

def baslat():
    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options={'api_version': 'v1'}
    )
    
    log_dosyasi = "haber_hafiza.txt"
    if not os.path.exists(log_dosyasi):
        with open(log_dosyasi, "w") as f: f.write("")
    
    with open(log_dosyasi, "r") as f:
        yayinlananlar = f.read().splitlines()

    for url in RSS_URLS:
        besleme = feedparser.parse(url)
        for haber in besleme.entries[:1]:
            if haber.link not in yayinlananlar:
                print(f"İşlemde: {haber.title}")
                
                # 1. Orijinal Resmi Bulma ve İndirme
                resim_url = ""
                if 'media_content' in haber:
                    resim_url = haber.media_content[0]['url']
                elif 'links' in haber:
                    for link in haber.links:
                        if 'image' in link.get('type', ''):
                            resim_url = link.href
                
                # Eğer hala resim yoksa description içinde ara
                if not resim_url and 'description' in haber:
                    img_match = re.search(r'<img src="([^"]+)"', haber.description)
                    if img_match: resim_url = img_match.group(1)

                resim_data = None
                if resim_url:
                    try:
                        print(f"Resim indiriliyor: {resim_url}")
                        r = requests.get(resim_url, timeout=10)
                        if r.status_code == 200:
                            resim_data = r.content
                    except Exception as e:
                        print(f"Resim indirme hatası: {e}")

                # 2. Gemini ile Metin ve Dinamik Etiket Oluşturma
                try:
                    prompt = (f"Haber Başlığı: {haber.title}\nÖzet: {haber.summary}\n\n"
                             "GÖREV:\n1. Bu haberi spiker diliyle profesyonelce yeniden yaz.\n"
                             "2. Bu haberle ilgili en az 10 adet popüler etiketi aralarında boşluk bırakarak başına # koyarak yaz.")
                    
                    res_metin = client.models.generate_content(
                        model="gemini-1.5-flash", 
                        contents=prompt
                    )
                    
                    tam_metin = res_metin.text
                    satirlar = tam_metin.strip().split('\n')
                    
                    dinamik_etiketler = ""
                    for satir in reversed(satirlar):
                        if "#" in satir:
                            dinamik_etiketler = satir
                            break
                    
                    # Gemini etiket üretemezse yedekler
                    if not dinamik_etiketler:
                        dinamik_etiketler = "#haber #guncel #turkiye #medya"
                    
                    # TÜM ETIKETLERİ BİRLEŞTİR (Senin istediklerin + Gemini'nin buldukları)
                    toplam_etiketler = f"{OZEL_ETIKETLER} {dinamik_etiketler}"
                    temiz_icerik = tam_metin.replace(dinamik_etiketler, "").strip()
                    
                except Exception as e:
                    print(f"Metin hatası: {e}")
                    temiz_icerik = f"{haber.title}\n\n{haber.summary}"
                    toplam_etiketler = OZEL_ETIKETLER

                # 3. Mail Gönderimi
                try:
                    msg = MIMEMultipart()
                    msg['From'] = GMAIL_ADRESIN
                    msg['To'] = BLOGGER_MAIL
                    # Konu satırına tüm etiketleri ekliyoruz (Blogger buradan yakalar)
                    msg['Subject'] = f"{haber.title} {toplam_etiketler}"
                    
                    html_icerik = f"""
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
                    msg.attach(MIMEText(html_icerik, 'html'))
                    
                    if resim_data:
                        image = MIMEImage(resim_data, name="haber.jpg")
                        msg.attach(image)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                        server.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                    
                    with open(log_dosyasi, "a") as f:
                        f.write(haber.link + "\n")
                    print(f"BAŞARIYLA GÖNDERİLDİ: {haber.title}")
                    
                except Exception as e:
                    print(f"Mail hatası: {e}")
                
                time.sleep(10)

if __name__ == "__main__":
    baslat()
