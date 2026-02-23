import feedparser, smtplib, time, os
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.seslisonhaber@blogger.com"
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LOG_DOSYASI = "haber_hafiza.txt"

# SADECE İSTEDİĞİN 2 KAYNAK
RSS_KAYNAKLARI = [
    "https://www.rudaw.net/turkish/rss",
    "https://www.sondakika.com/rss/"
]

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def blogda_yayinla(baslik, icerik, link, resim):
    try:
        prompt = f"Haber: {baslik} - {icerik}\n\nBu haberi profesyonel bir spiker diliyle 3 paragraf özgünleştir. Sona 3 anahtar kelime etiket ekle."
        response = model.generate_content(prompt)
        ai_metni = response.text
        
        msg = MIMEMultipart()
        msg['From'] = GMAIL_ADRES
        msg['To'] = BLOGGER_MAIL
        msg['Subject'] = baslik
        
        body = f'<img src="{resim}" style="width:100%; border-radius:10px;"><br><h2>{baslik}</h2><p>{ai_metni}</p><br><a href="{link}">Haberin Kaynağı</a>'
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(GMAIL_ADRES, GMAIL_SIFRE)
            s.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string())
        return True
    except Exception as e:
        print(f"Hata: {e}")
        return False

# --- ANA DÖNGÜ ---
if not os.path.exists(LOG_DOSYASI): open(LOG_DOSYASI, "w").close()
with open(LOG_DOSYASI, "r", encoding="utf-8") as f: hafiza = f.read()

for kaynak in RSS_KAYNAKLARI:
    print(f"Tarama yapılıyor: {kaynak}")
    feed = feedparser.parse(kaynak)
    for entry in feed.entries[:3]:
        if entry.link not in hafiza:
            # Resim çekme mantığı
            resim = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"
            if 'media_content' in entry: resim = entry.media_content[0]['url']
            elif 'links' in entry:
                for l in entry.links:
                    if 'image' in l.get('type', ''): resim = l.href
            
            if blogda_yayinla(entry.title, entry.get('summary', ''), entry.link, resim):
                with open(LOG_DOSYASI, "a", encoding="utf-8") as f: f.write(f"{entry.link}\n")
                print(f"YAYINLANDI: {entry.title}")
                time.sleep(15)
                break
