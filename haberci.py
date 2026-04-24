import feedparser, smtplib, os, time, requests, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADRESIN = os.getenv("GMAIL_ADRESIN")
GMAIL_UYGULAMA_SIFRESI = os.getenv("GMAIL_UYGULAMA_SIFRESI")
BLOGGER_MAIL = os.getenv("BLOGGER_MAIL")

# Ayarlar
OZEL_ETIKETLER = "Sesli Son Dakika, Haber, Güncel, Türkiye"
LOG_DOSYASI = "haber_hafiza.txt"

# Güncellenmiş RSS Listesi
RSS_URLS = [
    "https://www.trthaber.com/manset_rss.xml",
    "https://www.cumhuriyet.com.tr/rss",
    "http://www.hurriyet.com.tr/rss/gundem",
    "https://www.sozcu.com.tr/feeds-rss-category-sozcu",
    "https://www.sabah.com.tr/rss/anasayfa.xml",
    "https://www.milliyet.com.tr/rss/rssnew/manset.xml",
    "http://feeds.feedburner.com/ensonhaber",
    "https://www.haberler.com/rss/manset.xml",
    "https://www.aa.com.tr/tr/rss/default?cat=guncel",
    "https://www.ntv.com.tr/gundem.rss"
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def baslat():
    if not all([GEMINI_API_KEY, GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI, BLOGGER_MAIL]):
        print("Hata: Gerekli çevre değişkenleri bulunamadı.")
        return

    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1'})
    
    if not os.path.exists(LOG_DOSYASI):
        open(LOG_DOSYASI, "w", encoding="utf-8").close()
    
    with open(LOG_DOSYASI, "r", encoding="utf-8") as f:
        yayinlananlar = set(f.read().splitlines())

    for url in RSS_URLS:
        try:
            print(f"Okunuyor: {url}")
            # Bazı RSS'ler User-Agent gerektirdiği için requests ile çekiyoruz
            resp = requests.get(url, headers=HEADERS, timeout=10)
            besleme = feedparser.parse(resp.content)
            
            for haber in besleme.entries[:2]: # Her kaynaktan en yeni 2 haberi al
                link = haber.link
                if link not in yayinlananlar:
                    # --- Resim Yakalama ---
                    resim_url = ""
                    if 'media_content' in haber: resim_url = haber.media_content[0]['url']
                    elif 'description' in haber:
                        img_match = re.search(r'<img [^>]*src="([^"]+)"', haber.description)
                        if img_match: resim_url = img_match.group(1)

                    # --- Gemini İçerik ---
                    prompt = (f"Haber: {haber.title}\nÖzet: {haber.summary if 'summary' in haber else haber.title}\n\n"
                              "GÖREV: Bu haberi spiker tonunda, profesyonel bir blog yazısı olarak yaz. "
                              "Sadece metni ver, etiket veya hashtag kullanma.")
                    
                    try:
                        res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                        temiz_icerik = res.text.strip().replace('\n', '<br>')
                    except: continue

                    # --- Blogger Formatı ---
                    kaynak_adi = url.split('.')[1].upper()
                    mail_konusu = f"{haber.title} [{OZEL_ETIKETLER}, {kaynak_adi}]"

                    body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif;">
                        {f'<img src="{resim_url}" style="width:100%; border-radius:10px;"><br>' if resim_url else ''}
                        <div style="font-size: 16px; margin-top: 15px;">{temiz_icerik}</div>
                        <br><hr>
                        <p style="font-size: 12px;">Kaynak: <a href="{link}">{kaynak_adi}</a></p>
                    </body>
                    </html>
                    """

                    # --- Mail Gönderimi ---
                    msg = MIMEMultipart()
                    msg['Subject'] = mail_konusu
                    msg.attach(MIMEText(body, 'html'))
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                        s.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                        s.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                    
                    with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
                        f.write(link + "\n")
                    
                    print(f"Yayınlandı: {haber.title}")
                    time.sleep(8) # Blogger koruması için bekleme

        except Exception as e:
            print(f"URL hatası ({url}): {e}")
            continue

if __name__ == "__main__":
    baslat()
