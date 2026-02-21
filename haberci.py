import feedparser, smtplib, time, os, google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.sesli@blogger.com"
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LOG_DOSYASI = "haber_hafiza.txt"

RSS_KAYNAKLARI = [
    "https://www.ensonhaber.com/rss/ensonhaber.xml",
    "https://www.hurriyet.com.tr/rss/anasayfa",
    "https://www.trthaber.com/manset_articles.rss",
    "https://www.ntv.com.tr/son-dakika.rss",
    "https://www.sozcu.com.tr/rss/son-dakika.xml",
    "https://www.sabah.com.tr/rss/anasayfa.xml",
    "https://www.haberturk.com/rss",
    "https://www.milliyet.com.tr/rss/rssnew/gundemrss.xml",
    "https://www.cumhuriyet.com.tr/rss",
    "https://www.mynet.com/haber/rss/kategori/guncel"
]

# Modeli güncelledik (1.5-flash daha hızlı ve sorunsuz)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def resim_bul_veya_olustur(entry, baslik):
    resim = None
    if 'media_content' in entry: resim = entry.media_content[0]['url']
    elif 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''): resim = link.href
    if not resim:
        resim = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=600"
    return resim

def ai_ile_isle(baslik, icerik):
    prompt = f"Aşağıdaki haberi profesyonel spiker diliyle, en az 3 paragraf, özgün ve ilgi çekici yaz. Sonuna 'ETİKETLER: ' ekleyip 3 anahtar kelime yaz. Haber: {baslik} - {icerik}"
    try:
        response = model.generate_content(prompt)
        raw = response.text
        if "ETİKETLER:" in raw:
            yeni_metin = raw.split("ETİKETLER:")[0].strip()
            etiketler = raw.split("ETİKETLER:")[1].strip()
        else:
            yeni_metin = raw.strip()
            etiketler = "Güncel, Haber, SonDakika"
        return yeni_metin, etiketler
    except Exception as e:
        print(f"AI Hatası: {e}")
        return icerik, "Haber, Gündem"

def blogda_yayinla(baslik, icerik, link, resim):
    ozgun_metin, dinamik_etiketler = ai_ile_isle(baslik, icerik)
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    msg['Subject'] = f"{baslik} , {dinamik_etiketler}"
    
    html = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:15px; border-radius:12px;">
        <img src="{resim}" style="width:100%; border-radius:10px; margin-bottom:15px;">
        <h2 style="color:#222;">{baslik}</h2>
        <div style="font-size:16px; color:#444; line-height:1.7;">{ozgun_metin}</div>
        <div style="text-align:center; margin-top:20px;">
            <a href="{link}" style="background:#e31e24; color:#fff; padding:12px 25px; text-decoration:none; border-radius:6px;">KAYNAĞA GİT</a>
        </div>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(GMAIL_ADRES, GMAIL_SIFRE)
            s.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string())
        return True
    except:
        return False

# --- ANA DÖNGÜ ---
if not os.path.exists(LOG_DOSYASI): open(LOG_DOSYASI, "w").close()
with open(LOG_DOSYASI, "r", encoding="utf-8") as f: hafiza = f.read()

for i, kaynak in enumerate(RSS_KAYNAKLARI):
    print(f"Kaynak kontrol ediliyor: {kaynak}")
    feed = feedparser.parse(kaynak)
    for entry in feed.entries[:5]:
        if entry.link not in hafiza and entry.title not in hafiza:
            resim = resim_bul_veya_olustur(entry, entry.title)
            if blogda_yayinla(entry.title, entry.get('summary', ''), entry.link, resim):
                with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
                    f.write(f"{entry.link}\n")
                print(f"Paylaşıldı: {entry.title}")
                time.sleep(30) # 5 dakika değil, 30 saniye bekle (Hızlı bitsin)
                break
