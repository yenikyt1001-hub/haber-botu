import feedparser, smtplib, os, time, requests, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from google import genai

# Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADRESIN = os.getenv("GMAIL_ADRESIN")
GMAIL_UYGULAMA_SIFRESI = os.getenv("GMAIL_UYGULAMA_SIFRESI")
BLOGGER_MAIL = os.getenv("BLOGGER_MAIL")

# Senin sabit etiketlerin (Görseldeki gibi düz metin)
OZEL_ETIKETLER = "Sesli Son Dakika, Haber, Güncel, Türkiye"
LOG_DOSYASI = "haber_hafiza.txt"

RSS_URLS = ["https://www.ntv.com.tr/son-dakika.rss", "https://www.trthaber.com/sondakika.rss", "https://www.sondakika.com/rss/son-dakika/"]

def baslat():
    if not GEMINI_API_KEY: return
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1'})
    
    if not os.path.exists(LOG_DOSYASI):
        with open(LOG_DOSYASI, "w", encoding="utf-8") as f: f.write("")
    
    with open(LOG_DOSYASI, "r", encoding="utf-8") as f:
        yayinlananlar = f.read().splitlines()

    for url in RSS_URLS:
        besleme = feedparser.parse(url)
        for haber in besleme.entries[:2]:
            if haber.link not in yayinlananlar:
                # --- Resim Ayarları ---
                resim_url = ""
                if 'media_content' in haber: resim_url = haber.media_content[0]['url']
                elif 'description' in haber:
                    img_match = re.search(r'<img src="([^"]+)"', haber.description)
                    if img_match: resim_url = img_match.group(1)

                resim_data = None
                if resim_url:
                    try:
                        r = requests.get(resim_url, timeout=10)
                        if r.status_code == 200: resim_data = r.content
                    except: pass

                # --- Gemini: Sadece Haber Metni Üret ---
                try:
                    prompt = (f"Haber: {haber.title}\n{haber.summary}\n\n"
                              "GÖREV: Bu haberi spiker diliyle profesyonelce yaz. "
                              "SADECE haber metnini ver. Metin sonunda asla hashtag (#) veya etiket kullanma.")
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    temiz_icerik = res.text.strip().replace('\n', '<br>')
                    
                    # Gemini'nin ekleyebileceği hashtagleri temizle (Garanti olsun)
                    temiz_icerik = re.sub(r'#\w+', '', temiz_icerik) 
                except: continue

                # --- Kaynak ve Etiket Tasarımı (Birebir Eski Stil) ---
                kaynak_adi = haber.link.split('/')[2].replace('www.', '').split('.')[0].capitalize()
                
                # Blogger etiket kutusu için başlığa görünmez hashtag ekleyelim (Opsiyonel)
                konu_basligi = f"{haber.title}"

                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
                    <div>{temiz_icerik}</div>
                    <br>
                    <a href="{haber.link}" style="color: #0056b3; font-weight: bold; text-decoration: none;">Haberin devamı için tıklayın...</a>
                    <br><br>
                    <hr style="border: 0; border-top: 1px solid #ccc;">
                    <div style="font-size: 13px; color: #555;">
                        <span style="color: #777; font-weight: bold;">Kaynak:</span> 
                        <a href="{haber.link}" style="color: #0056b3; text-decoration: none;">{kaynak_adi}</a> | 
                        <span style="color: #777; font-weight: bold;">Etiketler:</span> {OZEL_ETIKETLER}, {haber.title[:20]}
                    </div>
                </body>
                </html>
                """
                
                msg = MIMEMultipart()
                msg['Subject'] = konu_basligi
                msg.attach(MIMEText(body, 'html'))
                if resim_data: msg.attach(MIMEImage(resim_data, name="haber.jpg"))
                
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                    s.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                    s.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                
                with open(LOG_DOSYASI, "a", encoding="utf-8") as f: f.write(haber.link + "\n")
                print(f"Yayınlandı: {haber.title}")
                time.sleep(5)

if __name__ == "__main__":
    baslat()
