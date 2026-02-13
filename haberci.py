import feedparser, smtplib, time, os, google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.sesli@blogger.com"
GEMINI_KEY = os.environ.get('GEMINI_API_KEY') # GitHub Secrets'tan alacak
LOG_DOSYASI = "haber_hafiza.txt"

# AI Yapılandırması
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

def resim_bul(entry):
    if 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''): return link.href
    if 'media_content' in entry: return entry.media_content[0]['url']
    return "https://via.placeholder.com/600x400.png?text=Haber+Detayi" # Resim yoksa boş dönmesin

def ai_ile_haberi_yaz(baslik, icerik):
    prompt = f"Aşağıdaki haberi bir haber spikeri ağzıyla, ilgi çekici ve özgün bir dille yeniden yaz. Sadece haber metnini ver:\n\nBaşlık: {baslik}\nİçerik: {icerik}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return icerik

def blogda_yayinla(baslik, icerik, link, resim_url):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    msg['Subject'] = f"{baslik} , Son Dakika, Haber, Güncel"
    
    ai_metin = ai_ile_haberi_yaz(baslik, icerik)
    
    html = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 15px;">
        <img src="{resim_url}" style="width: 100%; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #2c3e50; line-height: 1.3;">{baslik}</h2>
        <p style="font-size: 16px; color: #34495e; line-height: 1.8;">{ai_metin}</p>
        <div style="margin-top: 25px; padding: 15px; background-color: #f8f9fa; border-radius: 8px; text-align: center;">
            <a href="{link}" style="color: #e74c3c; font-weight: bold; text-decoration: none;">HABERİN DEVAMI İÇİN TIKLAYINIZ</a>
        </div>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #95a5a6;">
            <b>Kaynak:</b> NTV Haber | <b>Kategori:</b> Son Dakika
        </p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login(GMAIL_ADRES, GMAIL_SIFRE)
        s.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string()); s.quit()
        return True
    except Exception as e:
        print(f"Hata: {e}")
        return False

# --- ANA DÖNGÜ ---
if not os.path.exists(LOG_DOSYASI): open(LOG_DOSYASI, "w").close()

paylasilan = 0
feed = feedparser.parse("https://www.ntv.com.tr/son-dakika.rss")
with open(LOG_DOSYASI, "r") as f: hafiza = f.read()

for entry in feed.entries[:5]:
    if paylasilan >= 2: break
    if entry.link not in hafiza:
        img_url = resim_bul(entry)
        if blogda_yayinla(entry.title, entry.get('summary', ''), entry.link, img_url):
            with open(LOG_DOSYASI, "a") as f: f.write(entry.link + "\n")
            paylasilan += 1
            print(f"Başarılı: {entry.title}")
            time.sleep(10)
