import feedparser, smtplib, time, os, google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.sesli@blogger.com"
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LOG_DOSYASI = "haber_hafiza.txt"

# EN KALİTELİ 3 KAYNAK
RSS_KAYNAKLARI = [
    "https://www.trthaber.com/manset_articles.rss",
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.ensonhaber.com/rss/ensonhaber.xml"
]

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def ai_ile_isle(baslik, icerik):
    prompt = f"Bu haberi profesyonel spiker diliyle, 3 paragraf, tamamen özgün yaz. Sonuna 'ETİKETLER: ' ekleyip 3 anahtar kelime yaz. Haber: {baslik} - {icerik}"
    try:
        response = model.generate_content(prompt)
        raw = response.text
        if "ETİKETLER:" in raw:
            yeni_metin = raw.split("ETİKETLER:")[0].strip()
            etiketler = raw.split("ETİKETLER:")[1].strip()
        else:
            yeni_metin = raw.strip(); etiketler = "Haber, SonDakika, Gündem"
        return yeni_metin, etiketler
    except:
        return icerik, "Haber, Gündem"

def blogda_yayinla(baslik, icerik, link, resim):
    ozgun_metin, etiketler = ai_ile_isle(baslik, icerik)
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    msg['Subject'] = f"{baslik} , {etiketler}"
    
    html = f"""<div style="font-family:sans-serif; max-width:600px; margin:auto; padding:15px; border:1px solid #eee; border-radius:12px;">
        <img src="{resim}" style="width:100%; border-radius:10px;">
        <h2>{baslik}</h2>
        <div style="line-height:1.7;">{ozgun_metin}</div>
        <div style="text-align:center; margin-top:20px;">
            <a href="{link}" style="background:#e31e24; color:#fff; padding:10px 20px; text-decoration:none; border-radius:6px;">HABER KAYNAĞI</a>
        </div>
    </div>"""
    
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(GMAIL_ADRES, GMAIL_SIFRE)
            s.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string())
        return True
    except: return False

# --- ANA DÖNGÜ ---
if not os.path.exists(LOG_DOSYASI): open(LOG_DOSYASI, "w").close()
with open(LOG_DOSYASI, "r", encoding="utf-8") as f: hafiza = f.read()

for i, kaynak in enumerate(RSS_KAYNAKLARI):
    feed = feedparser.parse(kaynak)
    for entry in feed.entries[:3]: # Her kaynaktan en yeni 3 habere bak
        if entry.link not in hafiza:
            resim = entry.media_content[0]['url'] if 'media_content' in entry else "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"
            if blogda_yayinla(entry.title, entry.get('summary', ''), entry.link, resim):
                with open(LOG_DOSYASI, "a", encoding="utf-8") as f: f.write(f"{entry.link}\n")
                print(f"Paylaşıldı: {entry.title}")
                time.sleep(30) 
                break # Kaynak başına 1 haber paylaş ve diğer kaynağa geç
