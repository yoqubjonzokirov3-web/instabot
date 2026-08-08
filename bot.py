import os
import re
import glob
import telebot
import instaloader
import threading
from flask import Flask

TOKEN = os.environ.get("TELEGRAM_TOKEN")
IG_USERNAME = os.environ.get("IG_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

L = instaloader.Instaloader(
    dirname_pattern="post",
    filename_pattern="{shortcode}_{mediaid}",
    save_metadata=False,
    download_comments=False,
    post_metadata_txt_pattern=""
)

try:
    L.login(IG_USERNAME, IG_PASSWORD)
    print("Instagram login muvaffaqiyatli")
except Exception as e:
    print(f"Instagram login xatolik: {e}")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Menga Instagram video yoki rasm havolasini yuboring, men yuklab beraman 📥")

def shortcode_topish(url):
    m = re.search(r"/(p|reel|tv)/([A-Za-z0-9_-]+)", url)
    return m.group(2) if m else None

def eski_fayllarni_tozalash():
    for f in glob.glob("post/*"):
        os.remove(f)

@bot.message_handler(func=lambda message: True)
def video_yukla(message):
    url = message.text.strip()
    
    if "instagram.com" not in url:
        bot.reply_to(message, "Iltimos, to'g'ri Instagram havolasini yuboring.")
        return
    
    kutish_xabar = bot.reply_to(message, "Video yuklanmoqda, biroz kuting... ⏳")
    
    try:
        shortcode = shortcode_topish(url)
        if not shortcode:
            raise Exception("Havoladan post topilmadi")
        
        eski_fayllarni_tozalash()
        
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target="post")
        
        fayllar = sorted(glob.glob("post/*.jpg")) + sorted(glob.glob("post/*.mp4"))
        
        if not fayllar:
            raise Exception("Fayl topilmadi")
        
        for fayl in fayllar:
            kengaytma = fayl.split('.')[-1].lower()
            with open(fayl, 'rb') as f:
                if kengaytma == 'mp4':
                    bot.send_video(message.chat.id, f, caption="@Insta_Downloader8_bot")
                else:
                    bot.send_photo(message.chat.id, f, caption="@Insta_Downloader8_bot")
        
        eski_fayllarni_tozalash()
        
        bot.edit_message_text("✅", chat_id=message.chat.id, message_id=kutish_xabar.message_id)
        
    except Exception as e:
        bot.edit_message_text(
            "Kechirasiz, yuklab bo'lmadi. Havola to'g'riligini tekshiring yoki post shaxsiy (private) bo'lishi mumkin.",
            chat_id=message.chat.id,
            message_id=kutish_xabar.message_id
        )
        print(f"Xatolik: {e}")

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Polling xatolik: {e}")

@app.route('/')
def home():
    return "Bot ishlayapti!"

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=10000)
