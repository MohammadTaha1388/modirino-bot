from rubika import Client, handlers, models
import sqlite3
from datetime import datetime
from flask import Flask, request
import threading

# ==================== تنظیمات ====================
TOKEN = "BFIHAE0AVXJPREPDFDVLJCFQCUWZHRKDRMTBHBPUQLWXSAIDYMOTNQPOCHPQEUCF"  # توکن 
BOT_NAME = "مدیرینو"

# ==================== Flask Web Server ====================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Modirino Bot is running!"

# ==================== دیتابیس ====================
conn = sqlite3.connect("modirino.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS warns (
    user_id TEXT, group_id TEXT,
    count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, group_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    group_id TEXT PRIMARY KEY,
    anti_spam INTEGER DEFAULT 0,
    welcome INTEGER DEFAULT 0,
    lock_link INTEGER DEFAULT 0,
    lock_media INTEGER DEFAULT 0,
    welcome_text TEXT DEFAULT 'سلام {name} عزیز! به گروه خوش آمدی 🌹'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS mutes (
    user_id TEXT, group_id TEXT,
    muted_until TEXT,
    PRIMARY KEY (user_id, group_id)
)
""")
conn.commit()

# ==================== بات اصلی ====================
app = Client(BOT_NAME)
bot = app.create_bot(TOKEN)

def is_admin(group_id, user_id):
    try:
        admins = app.get_group_admins(group_id)
        return user_id in admins
    except:
        return False

def get_setting(group_id, key):
    cursor.execute(f"SELECT {key} FROM settings WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

# ==================== هندلرهای دستورات ====================

@bot.handler(handlers.MessageHandler(filters=handlers.Command("start")))
async def start(message: models.Message):
    await message.reply("""⚡ سلام مدیر عزیز!
به مرکز مدیریت گروه و کانال خوش آمدید.
اینجا همه‌چیز برای نظم، امنیت و کنترل کامل آماده‌ست.""")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("help")))
async def help_cmd(message: models.Message):
    await message.reply("""📚 راهنمای مدیرینو:
/mute - بی‌صدا کردن کاربر
/unmute - رفع بی‌صدا
/warn - اخطار به کاربر
/delwarn - حذف اخطارها
/admins - لیست مدیران
/settings - تنظیمات
/lock [link|media|sticker] - قفل کردن
/unlock [link|media|sticker] - باز کردن
/anti_spam [on|off] - ضداسپم
/welcome [on|off] - خوش‌آمدگویی
/rules - قوانین""")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("mute")))
async def mute_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    if not message.reply_to:
        return await message.reply("❌ روی پیام کاربر ریپلای کنید")
    user_id = message.reply_to.author_id
    cursor.execute("INSERT OR REPLACE INTO mutes VALUES (?, ?, ?)",
                   (user_id, message.group_id, "permanent"))
    conn.commit()
    await message.reply_to.delete()
    await message.reply("🔇 کاربر بی‌صدا شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("unmute")))
async def unmute_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    if not message.reply_to:
        return await message.reply("❌ روی پیام کاربر ریپلای کنید")
    user_id = message.reply_to.author_id
    cursor.execute("DELETE FROM mutes WHERE user_id = ? AND group_id = ?",
                   (user_id, message.group_id))
    conn.commit()
    await message.reply("🔊 کاربر آزاد شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("warn")))
async def warn_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    if not message.reply_to:
        return await message.reply("❌ روی پیام کاربر ریپلای کنید")
    user_id = message.reply_to.author_id
    cursor.execute("""
        INSERT INTO warns VALUES (?, ?, 1)
        ON CONFLICT(user_id, group_id) DO UPDATE SET count = count + 1
    """, (user_id, message.group_id))
    conn.commit()
    cursor.execute("SELECT count FROM warns WHERE user_id = ? AND group_id = ?",
                   (user_id, message.group_id))
    count = cursor.fetchone()[0]
    await message.reply(f"⚠️ اخطار {count}/3")
    if count >= 3:
        cursor.execute("INSERT OR REPLACE INTO mutes VALUES (?, ?, ?)",
                       (user_id, message.group_id, "permanent"))
        conn.commit()
        await message.reply("🔇 کاربر به دلیل ۳ اخطار بی‌صدا شد!")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("delwarn")))
async def delwarn_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    if not message.reply_to:
        return await message.reply("❌ روی پیام کاربر ریپلای کنید")
    user_id = message.reply_to.author_id
    cursor.execute("DELETE FROM warns WHERE user_id = ? AND group_id = ?",
                   (user_id, message.group_id))
    conn.commit()
    await message.reply("✅ اخطارها حذف شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("admins")))
async def admins_cmd(message: models.Message):
    try:
        admins = app.get_group_admins(message.group_id)
        text = "👑 لیست مدیران:\n\n"
        for admin in admins:
            text += f"• {admin}\n"
        await message.reply(text)
    except:
        await message.reply("❌ خطا در دریافت لیست")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("settings")))
async def settings(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ فقط ادمین‌ها!")
    anti_spam = get_setting(message.group_id, "anti_spam")
    welcome = get_setting(message.group_id, "welcome")
    lock_link = get_setting(message.group_id, "lock_link")
    await message.reply(f"""⚙️ تنظیمات:
🔇 ضداسپم: {'✅' if anti_spam else '❌'}
👋 خوش‌آمدگویی: {'✅' if welcome else '❌'}
🔗 قفل لینک: {'🔒' if lock_link else '🔓'}""")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("lock")))
async def lock_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ مشخص کن: link, media, sticker")
    lock_type = args[1].lower()
    if lock_type in ["link", "media", "sticker"]:
        cursor.execute(f"UPDATE settings SET lock_{lock_type} = 1 WHERE group_id = ?",
                       (message.group_id,))
        conn.commit()
        await message.reply(f"🔒 قفل {lock_type} فعال شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("unlock")))
async def unlock_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ مشخص کن: link, media, sticker")
    lock_type = args[1].lower()
    if lock_type in ["link", "media", "sticker"]:
        cursor.execute(f"UPDATE settings SET lock_{lock_type} = 0 WHERE group_id = ?",
                       (message.group_id,))
        conn.commit()
        await message.reply(f"🔓 قفل {lock_type} غیرفعال شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("anti_spam")))
async def anti_spam_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ["on", "off"]:
        return await message.reply("❌ on یا off")
    state = 1 if args[1].lower() == "on" else 0
    cursor.execute("UPDATE settings SET anti_spam = ? WHERE group_id = ?",
                   (state, message.group_id))
    conn.commit()
    await message.reply(f"🔇 ضداسپم {'✅' if state else '❌'}")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("welcome")))
async def welcome_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ["on", "off"]:
        return await message.reply("❌ on یا off")
    state = 1 if args[1].lower() == "on" else 0
    cursor.execute("UPDATE settings SET welcome = ? WHERE group_id = ?",
                   (state, message.group_id))
    conn.commit()
    await message.reply(f"👋 خوش‌آمدگویی {'✅' if state else '❌'}")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("rules")))
async def rules_cmd(message: models.Message):
    await message.reply("""📜 قوانین:
1️⃣ احترام به همه اعضا
2️⃣ محتوای نامناسب ممنوع
3️⃣ اسپم و تبلیغات ممنوع
4️⃣ بحث سیاسی ممنوع""")

# ==================== ضداسپم ====================
spam_tracker = {}

@bot.handler(handlers.MessageHandler())
async def message_handler(message: models.Message):
    if not message.group_id:
        return
    
    # قفل لینک
    if get_setting(message.group_id, "lock_link"):
        if any(x in message.text for x in ["http://", "https://", "t.me/", "rubika.ir/"]):
            if not is_admin(message.group_id, message.author_id):
                await message.delete()
                return
    
    # ضداسپم
    if get_setting(message.group_id, "anti_spam"):
        if not is_admin(message.group_id, message.author_id):
            user_id = message.author_id
            now = datetime.now()
            if user_id in spam_tracker:
                if (now - spam_tracker[user_id]).total_seconds() < 2:
                    await message.delete()
                    return
            spam_tracker[user_id] = now
    
    # mute
    cursor.execute("SELECT muted_until FROM mutes WHERE user_id = ? AND group_id = ?",
                   (message.author_id, message.group_id))
    if cursor.fetchone() and not is_admin(message.group_id, message.author_id):
        await message.delete()
        return

# ==================== اجرا ====================
def run_bot():
    print(f"🤖 {BOT_NAME} در حال اجرا...")
    app.run()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    web_app.run(host="0.0.0.0", port=8080)