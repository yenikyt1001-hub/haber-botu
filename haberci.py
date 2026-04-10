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
                print(f"İşleniyor: {haber.title}")
                
                # --- Resim Bulma ---
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

                # --- Gemini Metin ve Etiket Üretimi ---
                try:
                    # Gemini'ye formatı zorla dikte ediyoruz
                    prompt = (f"Haber Başlığı: {haber.title}\nİçerik: {haber.summary}\n\n"
                              "GÖREV:\n"
                              "1. Haberi profesyonel spiker diliyle, akıcı ve özgün şekilde yeniden yaz.\n"
                              "2. Bu haberle ilgili en az 10 popüler etiketi aralarında boşluk bırakarak başına # koyarak yaz.\n"
                              "ÖNEMLİ: Haberi yazdıktan sonra etiketleri EN ALT satıra ekle.")
                    
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    tam_metin = res.text.strip()
                    
                    # Etiketleri metnin içinden ayıkla
                    satirlar = tam_metin.split('\n')
                    dinamik_etiketler = ""
                    icerik_satirlari = []
                    
                    for satir in satirlar:
                        if "#" in satir:
                            dinamik_etiketler += " " + satir
                        else:
                            icerik_satirlari.append(satir)
                    
                    if not dinamik_etiketler.strip():
                        dinamik_etiketler = "#haber #sondakika #guncel #turkiye #gazete"
                    
                    temiz_icerik = "\n".join(icerik_satirlari).strip()
                    toplam_etiketler = f"{OZEL_ETIKETLER} {dinamik_etiketler.strip()}"
                    toplam_etiketler = " ".join(dict.fromkeys(toplam_etiketler.split())) # Tekrar eden etiketleri siler

                except Exception as e:
                    print(f"Gemini Hatası: {e}")
                    continue

                # --- Mail Gönderimi ---
                msg = MIMEMultipart()
                msg['Subject'] = f"{haber.title} {toplam_etiketler}"
                
                # HTML içeriğini düzenliyoruz
                # Ters eğik çizgi hatası olmaması için html_metin değişkeni:
                html_metin = temiz_icerik.replace('\n', '<br>')
                
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <div>{html_metin}</div>
                    <br><br>
                    <hr>
                    <strong>Kaynak:</strong> <a href="{haber.link}">{haber.link}</a>
                    <br><br>
                    <div style="color: #555; font-size: 12px; border-top: 1px solid #eee; pt: 10px;">
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
                    print(f"Başarıyla Yayınlandı: {haber.title}")
                except Exception as e:
                    print(f"Mail Gönderim Hatası: {e}")
                
                time.sleep(5)

if __name__ == "__main__":
    baslat()
