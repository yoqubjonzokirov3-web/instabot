import os
import telebot
import yt_dlp
import threading
from flask import Flask

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Salom! Menga Instagram video havolasini yuboring, men yuklab beraman 📥")

@bot.message_handler(func=lambda message: True)
def video_yukla(message):
    url = message.text.strip()
    
    if "instagram.com" not in url:
        bot.reply_to(message, "Iltimos, to'g'ri Instagram havolasini yuboring.")
        return
    
    bot.reply_to(message, "Video yuklanmoqda, biroz kuting... ⏳")
    
    try:
        ydl_opts = {
            'outtmpl': 'video.mp4',
            'format': 'best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        with open('video.mp4', 'rb') as video:
            bot.send_video(message.chat.id, video)
        
        os.remove('video.mp4')
        
    except Exception as e:
        bot.reply_to(message, "Kechirasiz, videoni yuklab bo'lmadi. Havola to'g'riligini tekshiring yoki video shaxsiy (private) bo'lishi mumkin.")
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
