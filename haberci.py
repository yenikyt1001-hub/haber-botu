import feedparser, smtplib, os, time, requests, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from google import genai

# Secrets'tan verileri al
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADRESIN = os.getenv("GMAIL_ADRESIN")
GMAIL_UYGULAMA_SIFRESI = os.getenv("GMAIL_UYGULAMA_SIFRESI")
BLOGGER_MAIL = os.getenv("BLOGGER_MAIL")

OZEL_ETIKETLER = "#duhirosondakika #duhirogüncel #seslihaber #seslisondakika #sondakika"
LOG_DOSYASI = "haber_hafiza.txt" # Sadece dosya adı kalsın

RSS_URLS = ["https://www.ntv.com.tr/son-dakika.rss", "https://www.trthaber.com/sondakika.rss"]

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
                # Resim bul
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

                # Gemini metin
                try:
                    prompt = f"Haber: {haber.title}\n{haber.summary}\n\nSpiker diliyle yaz, 10 #etiket ekle."
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    tam_metin = res.text
                    # Etiketleri ayır
                    satirlar = tam_metin.strip().split('\n')
                    dinamik_etiketler = next((s for s in reversed(satirlar) if "#" in s), "#haber")
                    toplam_etiketler = f"{OZEL_ETIKETLER} {dinamik_etiketler}"
                except: continue

                # Mail
                msg = MIMEMultipart()
                msg['Subject'] = f"{haber.title} {toplam_etiketler}"
                body = f"{tam_metin.replace(dinamik_etiketler, '')}<br><br>Kaynak: {haber.link}<br><br>{toplam_etiketler}"
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
