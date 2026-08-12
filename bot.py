import os
import re
import glob
import telebot
import instaloader
import yt_dlp
import threading
import imageio_ffmpeg
from flask import Flask

# ---------------- SOZLAMALAR ----------------
TOKEN = os.environ.get("TELEGRAM_TOKEN")
IG_USERNAME = os.environ.get("IG_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD")

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

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


# ---------------- /start ----------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Salom! Menga Instagram video, rasm yoki story havolasini yuboring, "
        "men yuklab beraman 📥\n\n"
        "Yoki xohlagan qo'shiq nomini yozing, men uni topib MP3 qilib beraman 🎵"
    )


# ---------------- Yordamchi funksiyalar ----------------
def shortcode_topish(url):
    m = re.search(r"/(p|reel|tv)/([A-Za-z0-9_-]+)", url)
    return m.group(2) if m else None


def eski_fayllarni_tozalash():
    for f in glob.glob("post/*"):
        os.remove(f)
    for f in glob.glob("post_*.*"):
        os.remove(f)
    for f in glob.glob("qoshiq_*.*"):
        os.remove(f)


def story_yukla(url):
    ydl_opts = {
        'outtmpl': 'post_%(autonumber)s.%(ext)s',
        'cookiefile': 'cookies.txt',
        'ffmpeg_location': FFMPEG_PATH,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return sorted(glob.glob("post_*.*"))


# ---------------- Har qanday matnli xabarni yo'naltirish ----------------
@bot.message_handler(func=lambda message: True)
def xabar_royxatdan_otish(message):
    url = message.text.strip()

    if "instagram.com" in url:
        instagram_yukla(message, url)
    else:
        qoshiq_yukla(message, url)


# ---------------- Qo'shiq qidirish va MP3 qilib berish ----------------
def qoshiq_yukla(message, qidiruv_matni):
    kutish_xabar = bot.reply_to(message, "Qo'shiq qidirilmoqda, biroz kuting... 🎵")
    try:
        eski_fayllarni_tozalash()

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'qoshiq_%(autonumber)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'default_search': 'ytsearch1',
            'quiet': True,
            'ffmpeg_location': FFMPEG_PATH,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(qidiruv_matni, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            sarlavha = info.get('title', qidiruv_matni)

        fayllar = sorted(glob.glob("qoshiq_*.mp3"))
        if not fayllar:
            raise Exception("Qo'shiq topilmadi")

        with open(fayllar[-1], 'rb') as f:
            bot.send_audio(message.chat.id, f, title=sarlavha, caption="@Insta_Downloader8_bot")

        eski_fayllarni_tozalash()
        bot.edit_message_text("✅", chat_id=message.chat.id, message_id=kutish_xabar.message_id)

    except Exception as e:
        bot.edit_message_text(
            "Kechirasiz, bu qo'shiqni topib bo'lmadi. Boshqa nom bilan urinib ko'ring.",
            chat_id=message.chat.id,
            message_id=kutish_xabar.message_id
        )
        print(f"Qo'shiq xatolik: {e}")


# ---------------- Instagram yuklash ----------------
def instagram_yukla(message, url):
    kutish_xabar = bot.reply_to(message, "Yuklanmoqda, biroz kuting... ⏳")

    try:
        eski_fayllarni_tozalash()

        if "/stories/" in url:
            fayllar = story_yukla(url)
        else:
            shortcode = shortcode_topish(url)
            if not shortcode:
                raise Exception("Havoladan post topilmadi")

            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target="post")

            video_fayllar = sorted(glob.glob("post/*.mp4"))
            rasm_fayllar = sorted(glob.glob("post/*.jpg"))
            fayllar = video_fayllar if video_fayllar else rasm_fayllar

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
            "Kechirasiz, yuklab bo'lmadi. Havola to'g'riligini tekshiring yoki post/story shaxsiy bo'lishi mumkin.",
            chat_id=message.chat.id,
            message_id=kutish_xabar.message_id
        )
        print(f"Xatolik: {e}")


# ---------------- Botni ishga tushirish ----------------
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
