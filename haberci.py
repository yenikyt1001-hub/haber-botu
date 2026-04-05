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

# Senin özel etiketlerin
OZEL_ETIKETLER = "#duhirosondakika #duhirogüncel #seslihaber #seslisondakika #sondakika"
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
                # 1. Resim Bul
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

                # 2. Gemini Metin ve Etiket Üretimi
                try:
                    prompt = (f"Haber: {haber.title}\n{haber.summary}\n\n"
                             "GÖREV: Spiker diliyle profesyonelce yaz. "
                             "Haberle ilgili en az 5 adet popüler etiketi aralarında boşluk bırakarak başına # koyarak en alt satıra ekle.")
                    
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    tam_metin = res.text
                    
                    # Etiketleri ayıklama (En alttaki # içeren satırı bulur)
                    satirlar = [s for s in tam_metin.strip().split('\n') if s.strip()]
                    dinamik_etiketler = ""
                    for satir in reversed(satirlar):
                        if "#" in satir:
                            dinamik_etiketler = satir
                            break
                    
                    if not dinamik_etiketler: dinamik_etiketler = "#haber #sondakika #guncel"
                    
                    # Senin etiketlerinle birleştir
                    toplam_etiketler = f"{OZEL_ETIKETLER} {dinamik_etiketler}"
                    temiz_icerik = tam_metin.replace(dinamik_etiketler, "").strip()
                except: continue

                # 3. Mail Hazırla ve Gönder
                msg = MIMEMultipart()
                msg['From'] = GMAIL_ADRESIN
                msg['To'] = BLOGGER_MAIL
                # Konuya tüm etiketleri basıyoruz
                msg['Subject'] = f"{haber.title} {toplam_etiketler}"
                
                body = f"""
                <html>
                <body>
                    <p>{temiz_icerik.replace('\n', '<br>')}</p>
                    <br>
                    <strong>Kaynak:</strong> <a href="{haber.link}">{haber.link}</a>
                    <br><br>
                    <p style="color:gray;">{toplam_etiketler}</p>
                </body>
                </html>
                """
                msg.attach(MIMEText(body, 'html'))
                if resim_data: msg.attach(MIMEImage(resim_data, name="haber.jpg"))
                
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                    s.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                    s.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                
                with open(LOG_DOSYASI, "a", encoding="utf-8") as f: f.write(haber.link + "\n")
                print(f"Başarıyla Yayınlandı: {haber.title}")
                time.sleep(5)

if __name__ == "__main__":
    baslat()
