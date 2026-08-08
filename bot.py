import os
import glob
import telebot
import yt_dlp
import threading
from flask import Flask

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Menga Instagram video yoki rasm havolasini yuboring, men yuklab beraman 📥")

def yuklab_olish(url):
    for f in glob.glob("post_*.*"):
        os.remove(f)
    
    try:
        ydl_opts = {
            'outtmpl': 'post_%(autonumber)s.%(ext)s',
            'format': 'best',
            'cookiefile': 'cookies.txt',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception:
        # Video format topilmasa, rasm sifatida qayta urinib ko'ramiz
        ydl_opts = {
            'outtmpl': 'post_%(autonumber)s.%(ext)s',
            'cookiefile': 'cookies.txt',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    
    return sorted(glob.glob("post_*.*"))

@bot.message_handler(func=lambda message: True)
def video_yukla(message):
    url = message.text.strip()
    
    if "instagram.com" not in url:
        bot.reply_to(message, "Iltimos, to'g'ri Instagram havolasini yuboring.")
        return
    
    kutish_xabar = bot.reply_to(message, "Video yuklanmoqda, biroz kuting... ⏳")
    
    try:
        fayllar = yuklab_olish(url)
        
        if not fayllar:
            raise Exception("Fayl topilmadi")
        
        for fayl in fayllar:
            kengaytma = fayl.split('.')[-1].lower()
            with open(fayl, 'rb') as f:
                if kengaytma in ['jpg', 'jpeg', 'png', 'webp']:
                    bot.send_photo(message.chat.id, f, caption="@Insta_Downloader8_bot")
                else:
                    bot.send_video(message.chat.id, f, caption="@Insta_Downloader8_bot")
            os.remove(fayl)
        
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
