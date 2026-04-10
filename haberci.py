import feedparser, smtplib, os, time, requests, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from google import genai

# Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADRESIN = os.getenv("GMAIL_ADRESIN")
GMAIL_UYGULAMA_SIFRESI = os.getenv("GMAIL_UYGULAMA_SIFRESI")
BLOGGER_MAIL = os.getenv("BLOGGER_MAIL")

# Sabit Özel Etiketlerin
OZEL_ETIKETLER = "#duhirosondakika #duhirogüncel #seslihaber #seslisondakika #sondakika"
LOG_DOSYASI = "haber_hafiza.txt"

RSS_URLS = ["https://www.ntv.com.tr/son-dakika.rss", "https://www.trthaber.com/sondakika.rss", "https://www.sondakika.com/rss/son-dakika/"]

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
                # --- Resim Çek ---
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

                # --- Gemini Metin ve Detaylı Etiketleme ---
                try:
                    prompt = (f"Haber: {haber.title}\n{haber.summary}\n\n"
                              "GÖREV: Spiker diliyle, heyecanlı ve detaylı bir haber metni yaz. "
                              "Metnin en sonuna, haberle ilgili en az 10 adet popüler etiketi aralarında boşluk bırakarak ekle.")
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    tam_metin = res.text.strip()
                    
                    # Etiketleri ve metni birbirinden ayırıyoruz
                    satirlar = tam_metin.split('\n')
                    dinamik_etiketler = ""
                    temiz_metin_listesi = []
                    
                    for s in satirlar:
                        if "#" in s:
                            dinamik_etiketler += " " + s
                        else:
                            temiz_metin_listesi.append(s)
                    
                    # Eğer Gemini etiket üretmezse boş kalmasın
                    if not dinamik_etiketler.strip():
                        dinamik_etiketler = "#haber #sondakika #guncel #turkiye"

                    # Senin özel etiketlerinle birleştir ve temizle
                    toplam_etiketler = f"{OZEL_ETIKETLER} {dinamik_etiketler.strip()}"
                    toplam_etiketler = " ".join(dict.fromkeys(toplam_etiketler.split()))
                    
                    # HTML için satır sonlarını düzenle (f-string hatası almamak için dışarıda)
                    html_icerik = "<br>".join(temiz_metin_listesi)
                except: continue

                # --- Mail Gönderimi (Zengin Tasarım) ---
                msg = MIMEMultipart()
                msg['From'] = GMAIL_ADRESIN
                msg['To'] = BLOGGER_MAIL
                # Başlığa etiketleri ekliyoruz (Blogger bunları etiket olarak algılar)
                msg['Subject'] = f"{haber.title} {toplam_etiketler}"
                
                body = f"""
                <html>
                <body style="font-family: 'Trebuchet MS', sans-serif; color: #333;">
                    <div style="font-size: 16px; line-height: 1.6;">
                        {html_icerik}
                    </div>
                    <br><br>
                    <div style="background: #f9f9f9; padding: 15px; border-left: 5px solid #0056b3;">
                        <strong>📌 Haber Kaynağı:</strong> <a href="{haber.link}" style="color: #0056b3; text-decoration: none;">{haber.link}</a>
                    </div>
                    <br>
                    <div style="color: #777; font-size: 14px; border-top: 1px solid #eee; padding-top: 10px;">
                        <strong>Etiketler:</strong><br>
                        {toplam_etiketler}
                    </div>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(body, 'html'))
                if resim_data:
                    msg.attach(MIMEImage(resim_data, name="haber.jpg"))
                
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                        s.login(GMAIL_ADRESIN, GMAIL_UYGULAMA_SIFRESI)
                        s.sendmail(GMAIL_ADRESIN, BLOGGER_MAIL, msg.as_string())
                    
                    with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
                        f.write(haber.link + "\n")
                    print(f"Yayınlandı: {haber.title}")
                except Exception as e:
                    print(f"Hata oluştu: {e}")
                
                time.sleep(5)

if __name__ == "__main__":
    baslat()
