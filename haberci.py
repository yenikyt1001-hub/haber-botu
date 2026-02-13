import feedparser, smtplib, time, os, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.sesli@blogger.com"
LOG_DOSYASI = "haber_hafiza.txt"

def blogda_yayinla(baslik, icerik, kaynak_link):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    
    # 💡 KRİTİK DEĞİŞİKLİK: Blogger etiketleri konu satırında virgülle ayrılmış 
    # ve sonuna boşluk bırakılmış şekilde bekler.
    msg['Subject'] = f"{baslik} , Son Dakika, Haber, Güncel"
    
    html = f"""
    <div style="font-family:sans-serif; line-height:1.6; color:#333;">
        <h2 style="color:#222; border-bottom:2px solid #eee; padding-bottom:10px;">🎙️ {baslik}</h2>
        <p style="font-size:16px;">{icerik}</p>
        <br>
        <div style="background:#f0f0f0; padding:15px; border-radius:5px; border-left:6px solid #d32f2f;">
            <strong style="color:#d32f2f;">📌 Haberin Kaynağı:</strong><br>
            <a href="{kaynak_link}" style="text-decoration:none; color:#1a73e8; word-break:break-all;">{kaynak_link}</a>
        </div>
        <br>
        <p style="color:#999; font-size:12px; border-top:1px solid #eee; pt:10px;">
            Sesli Haber Otomasyonu tarafından paylaşıldı.
        </p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login(GMAIL_ADRES, GMAIL_SIFRE)
        s.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string()); s.quit()
        return True
    except: return False

if not os.path.exists(LOG_DOSYASI): open(LOG_DOSYASI, "w").close()

paylasilan = 0
feed = feedparser.parse("https://www.ntv.com.tr/son-dakika.rss")
with open(LOG_DOSYASI, "r") as f: hafiza = f.read()

for entry in feed.entries[:5]:
    if paylasilan >= 2: break
    if entry.link not in hafiza:
        if blogda_yayinla(entry.title, entry.get('summary', ''), entry.link):
            with open(LOG_DOSYASI, "a") as f: f.write(entry.link + "\n")
            paylasilan += 1
            print(f"Başarılı: {entry.title}")
            time.sleep(5)
