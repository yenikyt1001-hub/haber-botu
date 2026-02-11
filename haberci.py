import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os  # Gizli kasa (Secrets) için eklendi

# --- KİŞİSEL BİLGİLERİN ---
GMAIL_ADRES = "yenikyt1001@gmail.com"
# Şifreyi açık yazmıyoruz, GitHub Secrets üzerinden alıyoruz
GMAIL_SIFRE = os.environ.get('GMAIL_SIFRE') 
BLOGGER_MAIL = "yenikyt1001.haberbotum@blogger.com"

# --- ZENGİNLEŞTİRİLMİŞ KAYNAKLAR ---
KAYNAKLAR = [
    {"ad": "NTV Haber", "url": "https://rss.app/rss-feed/google-news-rss-feed", "tip": "haber"},
    {"ad": "Son Dakika", "url": "https://www.sondakika.com/rss/", "tip": "haber"},
    {"ad": "BeinSports", "url": "https://beinsports.com.tr/rss/ana-sayfa", "tip": "haber"},
    {"ad": "Fanatik", "url": "https://www.fanatik.com.tr/rss", "tip": "haber"},
    {"ad": "Webtekno", "url": "https://www.webtekno.com/rss.xml", "tip": "haber"},
    {"ad": "ShiftDelete", "url": "https://shiftdelete.net/feed", "tip": "haber"},
    {"ad": "Magazin Haberleri", "url": "https://www.haberler.com/rss/magazin/", "tip": "haber"},
    {"ad": "NTV YouTube", "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCO6pSq98U8A_9vT0x-9u_qQ", "tip": "video"},
    {"ad": "Haber Global YouTube", "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCm86nC_Yf_vOshS_p8W_tBw", "tip": "video"}
]

def blogda_yayinla(baslik, icerik, kaynak_adi, tip, link="", resim_url=""):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADRES
    msg['To'] = BLOGGER_MAIL
    msg['Subject'] = baslik
    
    kelimeler = baslik.split()
    otomatik_etiketler = ", ".join([k for k in kelimeler if len(k) > 4][:5])
    sabit_etiketler = "Sesli Son Dakika, Haber, Spor, Teknoloji, Magazin"
    tum_etiketler = f"{sabit_etiketler}, {otomatik_etiketler}"

    gorsel_html = ""
    if resim_url:
        gorsel_html = f'<div style="text-align: center; margin-bottom: 20px;"><img src="{resim_url}" style="width: 100%; max-width: 700px; border-radius: 8px;"></div>'

    if tip == "video":
        video_id = link.split('v=')[-1] if 'v=' in link else link.split('/')[-1]
        kapak_resmi = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        html_icerik = f"""
        <div style="font-family: Arial, sans-serif;">
            <h2 style="color: #c00;">📺 {baslik}</h2>
            <div style="text-align: center; margin: 20px 0;"><a href='{link}'><img src='{kapak_resmi}' style='width: 100%; max-width: 600px; border-radius: 10px;'></a></div>
            <p>{icerik}</p>
            <p style="text-align: center;"><a href='{link}' style='color:white; background-color:red; padding:12px 25px; text-decoration:none; border-radius:5px; font-weight:bold;'>VİDEOYU İZLE</a></p>
            <br><hr>
            <p style="color: #777; font-size: 13px;"><strong>Kaynak:</strong> <a href='{link}'>{kaynak_adi}</a> | <strong>Etiketler:</strong> {tum_etiketler}</p>
        </div>
        """
    else:
        html_icerik = f"""
        <div style="font-family: Arial, sans-serif;">
            <h2>{baslik}</h2>
            {gorsel_html}
            <p>{icerik}</p>
            <p><a href='{link}' style='color: #0066cc; font-weight: bold;'>Haberin devamı için tıklayın...</a></p>
            <br><hr>
            <p style="color: #777; font-size: 13px;"><strong>Kaynak:</strong> <a href='{link}'>{kaynak_adi}</a> | <strong>Etiketler:</strong> {tum_etiketler}</p>
        </div>
        """

    msg.attach(MIMEText(html_icerik, 'html'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_ADRES, GMAIL_SIFRE)
        server.sendmail(GMAIL_ADRES, BLOGGER_MAIL, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return False

print("--- SESLİ SON DAKİKA: DEV PORTAL MODU BAŞLADI ---")
haber_sayaci = 0
toplam_hedef = 50 

for kaynak in KAYNAKLAR:
    if haber_sayaci >= toplam_hedef: break
    print(f"\n{kaynak['ad']} taranıyor...")
    feed = feedparser.parse(kaynak['url'])
    for entry in feed.entries[:3]:
        if haber_sayaci >= toplam_hedef: break
        resim_url = ""
        if 'media_content' in entry: resim_url = entry.media_content[0]['url']
        elif 'links' in entry:
            for l in entry.links:
                if 'image' in l.get('type', ''): resim_url = l.get('href', '')
        
        if blogda_yayinla(entry.title, entry.get('summary', ''), kaynak['ad'], kaynak['tip'], entry.link, resim_url):
            print(f"✓ [{haber_sayaci + 1}] Gönderildi: {entry.title[:50]}...")
            haber_sayaci += 1
            time.sleep(5)

print(f"\nİşlem bitti kral! {haber_sayaci} yeni içerik portala eklendi.")