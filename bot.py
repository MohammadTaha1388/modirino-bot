import asyncio
import rubika
from rubika import Bot, handlers, models
import sqlite3
from datetime import datetime, timedelta

# ==================== تنظیمات ====================
TOKEN = "BFIHAE0MONHOPZYJJJDGUMWMINGJZXUUQIPKKKJAGGUIMAFPVBKJBZNOJBQGWJTG"
BOT_NAME = "مدیرینو"

# ==================== دیتابیس ====================
conn = sqlite3.connect("modirino.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS warns (
    user_id TEXT,
    group_id TEXT,
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
    user_id TEXT,
    group_id TEXT,
    muted_until TEXT,
    PRIMARY KEY (user_id, group_id)
)
""")
conn.commit()

# ==================== بات اصلی ====================
bot = Bot(TOKEN)

def is_admin(group_id, user_id):
    try:
        admins = bot.get_group_admins(group_id)
        return user_id in admins
    except:
        return False

def get_setting(group_id, key):
    cursor.execute(f"SELECT {key} FROM settings WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

# ==================== دستورات ====================

@bot.handler(handlers.MessageHandler(filters=handlers.Command("start")))
async def start(message: models.Message):
    await message.reply("""⚡ سلام مدیر عزیز!

به مرکز مدیریت گروه و کانال خوش آمدید.

اینجا همه‌چیز برای نظم، امنیت و کنترل کامل آماده‌ست.

📌 برای دیدن راهنما: /help""")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("help")))
async def help_cmd(message: models.Message):
    await message.reply("""📚 **راهنمای مدیرینو**

👤 **مدیریت کاربران:**
• /mute (ریپلای) - بی‌صدا کردن کاربر
• /unmute (ریپلای) - رفع بی‌صدا
• /warn (ریپلای) - اخطار به کاربر
• /delwarn (ریپلای) - حذف اخطارها
• /admins - نمایش لیست مدیران

🔒 **تنظیمات گروه:**
• /settings - تنظیمات مدیریت
• /lock link|media|sticker - قفل کردن
• /unlock link|media|sticker - باز کردن
• /anti_spam on|off - ضداسپم
• /welcome on|off - خوش‌آمدگویی
• /rules - نمایش قوانین""")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("settings")))
async def settings(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ فقط ادمین‌ها میتوانند تنظیمات را ببینند.")
    
    anti_spam = get_setting(message.group_id, "anti_spam")
    welcome = get_setting(message.group_id, "welcome")
    lock_link = get_setting(message.group_id, "lock_link")
    lock_media = get_setting(message.group_id, "lock_media")
    
    await message.reply(f"""⚙️ **تنظیمات فعلی گروه:**

🔇 ضداسپم: {'✅ فعال' if anti_spam else '❌ غیرفعال'}
👋 خوش‌آمدگویی: {'✅ فعال' if welcome else '❌ غیرفعال'}
🔗 قفل لینک: {'🔒 فعال' if lock_link else '🔓 غیرفعال'}
🖼 قفل رسانه: {'🔒 فعال' if lock_media else '🔓 غیرفعال'}

برای تغییر از دستورات /lock و /unlock و /anti_spam و /welcome استفاده کنید.""")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("admins")))
async def admins_cmd(message: models.Message):
    try:
        admins = bot.get_group_admins(message.group_id)
        text = "👑 **لیست مدیران گروه:**\n\n"
        for admin in admins:
            text += f"• {admin}\n"
        await message.reply(text)
    except:
        await message.reply("❌ خطا در دریافت لیست مدیران")

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
    await message.reply(f"🔇 کاربر بی‌صدا شد")

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
    await message.reply(f"🔊 کاربر آزاد شد")

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
    
    await message.reply(f"⚠️ اخطار {count}/3 به کاربر داده شد")
    
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
    await message.reply("✅ تمام اخطارهای کاربر حذف شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("lock")))
async def lock_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ نوع قفل را مشخص کنید: link, media, sticker")
    
    lock_type = args[1].lower()
    if lock_type == "link":
        cursor.execute("UPDATE settings SET lock_link = 1 WHERE group_id = ?", (message.group_id,))
    elif lock_type == "media":
        cursor.execute("UPDATE settings SET lock_media = 1 WHERE group_id = ?", (message.group_id,))
    elif lock_type == "sticker":
        cursor.execute("UPDATE settings SET lock_sticker = 1 WHERE group_id = ?", (message.group_id,))
    else:
        return await message.reply("❌ نوع قفل نامعتبر. گزینه‌ها: link, media, sticker")
    
    conn.commit()
    await message.reply(f"🔒 قفل {lock_type} فعال شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("unlock")))
async def unlock_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ نوع قفل را مشخص کنید: link, media, sticker")
    
    lock_type = args[1].lower()
    if lock_type == "link":
        cursor.execute("UPDATE settings SET lock_link = 0 WHERE group_id = ?", (message.group_id,))
    elif lock_type == "media":
        cursor.execute("UPDATE settings SET lock_media = 0 WHERE group_id = ?", (message.group_id,))
    elif lock_type == "sticker":
        cursor.execute("UPDATE settings SET lock_sticker = 0 WHERE group_id = ?", (message.group_id,))
    else:
        return await message.reply("❌ نوع قفل نامعتبر. گزینه‌ها: link, media, sticker")
    
    conn.commit()
    await message.reply(f"🔓 قفل {lock_type} غیرفعال شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("anti_spam")))
async def anti_spam_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ["on", "off"]:
        return await message.reply("❌ حالت را مشخص کنید: on یا off")
    
    state = 1 if args[1].lower() == "on" else 0
    cursor.execute("UPDATE settings SET anti_spam = ? WHERE group_id = ?",
                   (state, message.group_id))
    conn.commit()
    
    status = "فعال ✅" if state else "غیرفعال ❌"
    await message.reply(f"🔇 ضداسپم {status} شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("welcome")))
async def welcome_cmd(message: models.Message):
    if not is_admin(message.group_id, message.author_id):
        return await message.reply("⛔ دسترسی ندارید!")
    
    args = message.text.split()
    if len(args) < 2 or args[1].lower() not in ["on", "off"]:
        return await message.reply("❌ حالت را مشخص کنید: on یا off")
    
    state = 1 if args[1].lower() == "on" else 0
    cursor.execute("UPDATE settings SET welcome = ? WHERE group_id = ?",
                   (state, message.group_id))
    conn.commit()
    
    status = "فعال ✅" if state else "غیرفعال ❌"
    await message.reply(f"👋 خوش‌آمدگویی {status} شد")

@bot.handler(handlers.MessageHandler(filters=handlers.Command("rules")))
async def rules_cmd(message: models.Message):
    await message.reply("""📜 **قوانین گروه:**

1️⃣ احترام به همه اعضا الزامیست
2️⃣ ارسال محتوای نامناسب ممنوع
3️⃣ اسپم و تبلیغات ممنوع
4️⃣ بحث‌های سیاسی ممنوع
5️⃣ از فوروارد غیرضروری خودداری کنید

⚠️ تخلف = اخطار > ۳ اخطار = بی‌صدا""")

# ==================== سیستم ضداسپم ====================
spam_tracker = {}

@bot.handler(handlers.MessageHandler())
async def anti_spam_check(message: models.Message):
    if not message.group_id:
        return
    
    if get_setting(message.group_id, "lock_link") and any(x in message.text for x in ["http://", "https://", "t.me/", "rubika.ir/"]):
        if not is_admin(message.group_id, message.author_id):
            await message.delete()
            return
    
    if get_setting(message.group_id, "anti_spam") and not is_admin(message.group_id, message.author_id):
        user_id = message.author_id
        now = datetime.now()
        
        if user_id in spam_tracker:
            last_msg_time = spam_tracker[user_id]
            if (now - last_msg_time).total_seconds() < 2:
                await message.delete()
                await message.reply(f"⚠️ کاربر گرامی، لطفاً اسپم نکنید!", reply_to_message_id=message.message_id)
                return
        
        spam_tracker[user_id] = now
    
    cursor.execute("SELECT muted_until FROM mutes WHERE user_id = ? AND group_id = ?",
                   (message.author_id, message.group_id))
    muted = cursor.fetchone()
    if muted and not is_admin(message.group_id, message.author_id):
        await message.delete()
        return

# ==================== خوش‌آمدگویی ====================
@bot.handler(handlers.EventHandler(filters=handlers.EventType.JOIN))
async def welcome_handler(event):
    group_id = event.group_id
    if get_setting(group_id, "welcome"):
        user_name = event.author_name or "کاربر"
        cursor.execute("SELECT welcome_text FROM settings WHERE group_id = ?", (group_id,))
        row = cursor.fetchone()
        text = row[0] if row else "سلام {name} عزیز! به گروه خوش آمدی 🌹"
        await bot.send_message(group_id, text.format(name=user_name))

# ==================== اجرای بات ====================
print(f"🤖 {BOT_NAME} در حال اجرا...")
print("✅ آماده دریافت دستورات!")
bot.run()