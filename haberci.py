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

# Senin özel etiketlerin (Başında # olmadan, virgülle ayırıyoruz)
OZEL_ETIKETLER = "Sesli Son Dakika, Haber, Spor, Teknoloji, Magazin"
LOG_DOSYASI = "haber_hafiza.txt"

RSS_URLS = [
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.trthaber.com/sondakika.rss",
    "https://www.sondakika.com/rss/son-dakika/"
]

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
                # --- Resim İşlemleri ---
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

                # --- Gemini Metin Üretimi ---
                try:
                    prompt = (f"Haber: {haber.title}\n{haber.summary}\n\n"
                              "GÖREV: Spiker diliyle profesyonel bir haber yaz. "
                              "Metnin sonuna bu haberle ilgili 5 tane anahtar kelimeyi virgülle ayırarak yaz (Başlarına # koyma).")
                    
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    tam_metin = res.text.strip()
                    
                    # Metni ve anahtar kelimeleri ayıkla
                    satirlar = tam_metin.split('\n')
                    dinamik_anahtar = satirlar[-1].replace("#", "") # Son satırı al, hashtag varsa temizle
                    temiz_icerik = "<br>".join(satirlar[:-1]) # Son satır hariç her şeyi içeriğe al
                    
                    # Etiketleri birleştir (Eski stildeki gibi düz metin)
                    son_etiketler = f"{OZEL_ETIKETLER}, {dinamik_anahtar}"
                except: continue

                # --- Mail Hazırlığı (İstediğin Görsel Tasarım) ---
                msg = MIMEMultipart()
                msg['Subject'] = haber.title # Blogger etiketleri için gerekirse buraya hashtag eklenebilir
                
                # Orijinal Kaynağın Adını Al (ntv.com.tr vb.)
                kaynak_adi = haber.link.split('/')[2].replace('www.', '')

                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div>{temiz_icerik}</div>
                    <br><br>
                    <a href="{haber.link}" style="color: #0056b3; font-weight: bold; text-decoration: none;">Haberin devamı için tıklayın...</a>
                    <br><br>
                    <hr style="border: 0; border-top: 1px solid #ccc;">
                    <div style="font-size: 13px; color: #666;">
                        <strong>Kaynak:</strong> <a href="{haber.link}" style="color: #0056b3;">{kaynak_adi.capitalize()}</a> | 
                        <strong>Etiketler:</strong> {son_etiketler}
                    </div>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(body, 'html'))
                if resim_data:
                    msg.attach(MIMEImage(resim_data, name="haber.jpg"))
                
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                    s.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                    s.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                
                with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
                    f.write(haber.link + "\n")
                print(f"Yayınlandı: {haber.title}")
                time.sleep(5)

if __name__ == "__main__":
    baslat()
