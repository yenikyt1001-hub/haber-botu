import feedparser, smtplib, os, time, requests, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# Secrets (Bunları GitHub'da 'Secrets' kısmına eklemeyi unutma!)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADRESIN = os.getenv("GMAIL_ADRESIN")
GMAIL_UYGULAMA_SIFRESI = os.getenv("GMAIL_UYGULAMA_SIFRESI")
BLOGGER_MAIL = os.getenv("BLOGGER_MAIL")

# Ayarlar
OZEL_ETIKETLER = "Haber, Güncel, Türkiye, Son Dakika" # Görseldeki gibi düz metin
LOG_DOSYASI = "haber_hafiza.txt"

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
        print("Hata: Eksik yapılandırma (secrets).")
        return

    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1'})
    
    if not os.path.exists(LOG_DOSYASI): open(LOG_DOSYASI, "w", encoding="utf-8").close()
    
    with open(LOG_DOSYASI, "r", encoding="utf-8") as f:
        yayinlananlar = set(f.read().splitlines())

    for url in RSS_URLS:
        try:
            print(f"Okunuyor: {url}")
            resp = requests.get(url, headers=HEADERS, timeout=10)
            besleme = feedparser.parse(resp.content)
            
            # Kaynak adını temizle (Örn: ntv, trthaber, sozcu)
            kaynak_ham = url.split('.')[1] if "http" in url else "Haber"
            kaynak_adi = kaynak_ham.replace('com', '').replace('tr', '').strip('-').upper()

            for haber in besleme.entries[:1]: # Her 30 dk'da bir her kaynaktan 1 haber (Spam koruması)
                if haber.link not in yayinlananlar:
                    # Resim bulma
                    resim_url = ""
                    if 'media_content' in haber: resim_url = haber.media_content[0]['url']
                    elif 'description' in haber:
                        img_match = re.search(r'<img [^>]*src="([^"]+)"', haber.description)
                        if img_match: resim_url = img_match.group(1)

                    # Gemini Prompt - Olayı sadece profesyonel bir blog yazısı olarak yaz
                    prompt = (f"Haber Başlığı: {haber.title}\n"
                              f"Haber Özeti: {haber.summary if 'summary' in haber else haber.title}\n\n"
                              "GÖREV: Bu haberi bir spiker tonunda, profesyonel bir blog yazısı olarak yeniden yaz. "
                              "Asla kaynak belirtme, hashtag kullanma. Sadece metni ver.")
                    
                    try:
                        res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                        temiz_icerik = res.text.strip().replace('\n', '<br>')
                    except:
                        print("Gemini içerik üretemedi.")
                        continue

                    # Blogger Mail İçeriği (Görseldeki gibi modern tasarım)
                    # Konuya etiketleri ekle [etiket1, etiket2]
                    mail_konusu = f"{haber.title} [{OZEL_ETIKETLER}]"
                    
                    body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                            
                            {f'<div style="text-align:center; margin-bottom: 25px;"><img src="{resim_url}" style="width:100%; max-width:600px; border-radius:8px; border: 1px solid #ddd;"></div>' if resim_url else ''}
                            
                            <h1 style="color: #333; font-size: 24px; font-weight: bold; margin-bottom: 15px;">{haber.title}</h1>
                            
                            <div style="color: #555; font-size: 16px; line-height: 1.8; margin-bottom: 30px;">
                                {temiz_icerik}
                            </div>
                            
                            <div style="text-align: center; margin-bottom: 20px;">
                                <a href="{haber.link}" style="background-color: #d93025; color: #ffffff; text-decoration: none; padding: 12px 30px; font-size: 16px; font-weight: bold; border-radius: 5px; display: inline-block; transition: background-color 0.3s; border: 1px solid #c02a21;">
                                    HABERİN TAMAMI
                                </a>
                            </div>
                            
                            <hr style="border: 0; border-top: 1px solid #eee; margin-bottom: 15px;">
                            <div style="font-size: 12px; color: #888; text-align: center;">
                                <strong>Kaynak:</strong> {kaynak_adi} | 
                                <strong>Yayın Tarihi:</strong> {time.strftime('%d.%m.%Y %H:%M')}
                            </div>
                        </div>
                    </body>
                    </html>
                    """

                    # Mail Gönderimi
                    msg = MIMEMultipart()
                    msg['Subject'] = mail_konusu
                    msg.attach(MIMEText(body, 'html'))
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                        s.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                        s.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                    
                    with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
                        f.write(haber.link + "\n")
                    
                    print(f"Yayınlandı: {haber.title} ({kaynak_adi})")
                    time.sleep(15) # Blogger ve Gmail spam koruması

        except Exception as e:
            print(f"URL hatası ({url}): {e}")

if __name__ == "__main__":
    baslat()
