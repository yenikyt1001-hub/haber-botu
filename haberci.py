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
    return "https://via.placeholder.com/600x400.png?text=Guncel+Haber"

def ai_haber_ve_etiket(baslik, icerik):
    # AI'dan hem haberi yazmasını hem de 3-4 tane etiket bulmasını istiyoruz
    prompt = f"""Aşağıdaki haberi spiker gibi akıcı yaz ve sonuna uygun 3-4 adet etiket ekle.
    Format şu olsun: 
    METİN: [buraya haber metni]
    ETİKETLER: [buraya aralarında virgül olan etiketler]
    
    Haber: {baslik} - {icerik}"""
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        # Metni ve etiketleri birbirinden ayırıyoruz
        ai_metin = raw_text.split("ETİKETLER:")[0].replace("METİN:", "").strip()
        etiketler = raw_text.split("ETİKETLER:")[1].strip()
        return ai_metin, etiketler
    except:
        return icerik, "Gündem, Haber, Son Dakika"

def blogda_yayinla(baslik, icerik, link, resim):
    ai_metin, dinamik_etiketler = ai_haber_ve_etiket(baslik, icerik)
    
    msg = MIMEMultipart()
    msg['From'], msg['To'] = GMAIL_ADRES, BLOGGER_MAIL
    # Blogger'ın etiketleri görmesi için konu satırı: Başlık , Etiket1, Etiket2
    msg['Subject'] = f"{baslik} , {dinamik_etiketler}"
    
    html = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:15px; border-radius:10px;">
        <img src="{resim}" style="width:100%; border-radius:8px; margin-bottom:15px;">
        <h2 style="color:#222;">{baslik}</h2>
        <p style="font-size:16px; color:#444; line-height:1.6;">{ai_metin}</p>
        <div style="margin-top:20px; text-align:center;">
            <a href="{link}" style="background:#d32f2f; color:#fff; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">HABERİN TAMAMI</a>
        </div>
        <hr style="margin-top:30px; border:0; border-top:1px solid #eee;">
        <p style="font-size:12px; color:#999;"><b>Etiketler:</b> {dinamik_etiketler}</p>
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
