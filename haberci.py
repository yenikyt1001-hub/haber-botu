import feedparser, smtplib, time, os, google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.sesli@blogger.com"
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LOG_DOSYASI = "haber_hafiza.txt"

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

def resim_bul(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''): return link.href
    return "https://via.placeholder.com/600x400.png?text=Haber+Gorseli"

def ai_ile_yaz(baslik, icerik):
    try:
        response = model.generate_content(f"Bu haberi spiker gibi akıcı yaz: {baslik} - {icerik}")
        return response.text
    except: return icerik

def blogda_yayinla(baslik, icerik, link, resim):
    msg = MIMEMultipart()
    msg['From'], msg['To'] = GMAIL_ADRES, BLOGGER_MAIL
    # Blogger etiketleri için başlık formatı
    msg['Subject'] = f"{baslik} , Son Dakika, Haber, Güncel"
    
    ai_metin = ai_ile_yaz(baslik, icerik)
    html = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto;">
        <img src="{resim}" style="width:100%; border-radius:10px;">
        <h2>{baslik}</h2>
        <p>{ai_metin}</p>
        <a href="{link}" style="color:#d32f2f; font-weight:bold;">Haberin devamı için tıklayın...</a>
        <hr>
        <p style="font-size:12px; color:#777;">Kaynak: NTV | Etiketler: Son Dakika, Haber</p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login(GMAIL_ADRES, GMAIL_SIFRE)
        s.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string()); s.quit()
        return True
    except: return False

if not os.path.exists(LOG_DOSYASI): open(LOG_DOSYASI, "w").close()
feed = feedparser.parse("https://www.ntv.com.tr/son-dakika.rss")
with open(LOG_DOSYASI, "r") as f: hafiza = f.read()

paylasilan = 0
for entry in feed.entries[:5]:
    if paylasilan >= 2: break
    if entry.link not in hafiza:
        if blogda_yayinla(entry.title, entry.get('summary', ''), entry.link, resim_bul(entry)):
            with open(LOG_DOSYASI, "a") as f: f.write(entry.link + "\n")
            paylasilan += 1
            time.sleep(10)
