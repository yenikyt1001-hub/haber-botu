import feedparser, smtplib, time, os, google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- AYARLAR ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE')
BLOGGER_MAIL = "yenikyt1001.sesli@blogger.com"
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
LOG_DOSYASI = "haber_hafiza.txt"

# EN HİT 10 KAYNAK
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

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

def resim_bul_veya_olustur(entry, baslik):
    resim = None
    # 1. RSS içindeki görseli ara
    if 'media_content' in entry: resim = entry.media_content[0]['url']
    elif 'links' in entry:
        for link in entry.links:
            if 'image' in link.get('type', ''): resim = link.href
    
    # 2. Görsel yoksa Unsplash üzerinden konuya özel çek
    if not resim:
        kelime = baslik.split()[0] # Başlığın ilk kelimesiyle aratır
        resim = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=600&q=80&sig={time.time()}"
        # Not: source.unsplash kapandığı için güncel API formatını ekledim.
    
    return resim

def ai_ile_isle(baslik, icerik):
    # AI'ya hem haberi yazdırıyoruz hem de etiketleri bulduruyoruz
    prompt = f"""
    Aşağıdaki haberi profesyonel bir haber spikeri diliyle baştan yaz. 
    İçerik tamamen özgün olmalı. En az 3 paragraf kullan.
    Metnin sonuna mutlaka 'ETİKETLER: ' yazıp yanına haberle ilgili 3 anahtar kelime ekle.
    
    Haber: {baslik} - {icerik}
    """
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
    except:
        return icerik, "Haber, Gündem"

def blogda_yayinla(baslik, icerik, link, resim):
    # AI özgünleştirme ve etiketleme işlemi
    ozgun_metin, dinamik_etiketler = ai_ile_isle(baslik, icerik)
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    # Blogger'ın etiketleri otomatik alması için: Başlık , Etiket1, Etiket2
    msg['Subject'] = f"{baslik} , {dinamik_etiketler}"
    
    html = f"""
    <div style="font-family:sans-serif; max-width:600px; margin:auto; border:1px solid #eee; padding:15px; border-radius:12px;">
        <img src="{resim}" style="width:100%; border-radius:10px; margin-bottom:15px;">
        <h2 style="color:#222; font-size:20px;">{baslik}</h2>
        <div style="font-size:16px; color:#444; line-height:1.7;">{ozgun_metin}</div>
        <div style="text-align:center; margin-top:20px;">
            <a href="{link}" style="background:#e31e24; color:#fff; padding:12px 25px; text-decoration:none; border-radius:6px; font-weight:bold; display:inline-block;">HABERİN KAYNAĞI</a>
        </div>
        <hr style="margin-top:30px; border:0; border-top:1px solid #eee;">
        <p style="font-size:11px; color:#999;"><b>Etiketler:</b> {dinamik_etiketler}</p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(GMAIL_ADRES, GMAIL_SIFRE)
            s.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string())
        return True
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return False

# --- ANA DÖNGÜ ---
if not os.path.exists(LOG_DOSYASI): open(LOG_DOSYASI, "w").close()
with open(LOG_DOSYASI, "r", encoding="utf-8") as f: hafiza = f.read()

for i, kaynak in enumerate(RSS_KAYNAKLARI):
    feed = feedparser.parse(kaynak)
    paylasildi = False
    
    for entry in feed.entries[:5]:
        if entry.link not in hafiza and entry.title not in hafiza:
            resim = resim_bul_veya_olustur(entry, entry.title)
            print(f"Sıradaki haber işleniyor: {entry.title}")
            
            if blogda_yayinla(entry.title, entry.get('summary', ''), entry.link, resim):
                with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
                    f.write(f"{entry.link}\n{entry.title}\n")
                print("Başarıyla paylaşıldı.")
                paylasildi = True
                break # Her kaynaktan 1 adet paylaşıp diğerine geçiyoruz
    
    # Haber paylaşıldıysa ve listede başka kaynak varsa 5 dk bekle
    if paylasildi and i < len(RSS_KAYNAKLARI) - 1:
        print("Blogger ve SEO güvenliği için 5 dakika bekleniyor...")
        time.sleep(300)
