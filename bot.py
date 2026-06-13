import rubika
import sqlite3
import time
from datetime import datetime

# ================= TOKEN =================
TOKEN = "BFIHAE0AIVMMOWFQRKFNLEACICPBUIZQGPRHLOMYCGZWDMSZASRVSEBFMUSLYUUG"
bot = rubika.Bot(TOKEN)

# ================= DATABASE =================
conn = sqlite3.connect("modirino.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    group_id TEXT PRIMARY KEY,
    anti_spam INTEGER DEFAULT 0,
    welcome INTEGER DEFAULT 0,
    lock_link INTEGER DEFAULT 0,
    lock_media INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS mutes (
    user_id TEXT,
    group_id TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS warns (
    user_id TEXT,
    group_id TEXT,
    count INTEGER DEFAULT 0,
    PRIMARY KEY(user_id, group_id)
)
""")

conn.commit()

# ================= HELPERS =================
def is_admin(group_id, user_id):
    try:
        admins = bot.get_group_admins(group_id)
        return user_id in admins
    except:
        return False

def get_setting(group_id, key):
    cursor.execute(f"SELECT {key} FROM settings WHERE group_id=?", (group_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

def ensure_group(group_id):
    cursor.execute("INSERT OR IGNORE INTO settings(group_id) VALUES(?)", (group_id,))
    conn.commit()

# ================= MESSAGE LOOP =================
print("Bot is running...")

last_msg_time = {}

while True:
    try:
        updates = bot.get_updates()

        if not updates:
            time.sleep(0.5)
            continue

        for update in updates:
            msg = update.get("message", None)
            if not msg:
                continue

            text = msg.get("text") or ""
            group_id = msg.get("group_guid")
            user_id = msg.get("author_object_guid")
            message_id = msg.get("message_id")

            if not group_id:
                continue

            ensure_group(group_id)

            # ================= COMMANDS =================

            if text == "/start":
                bot.sendMessage(group_id,
                    "⚡ سلام!\nربات مدیرینو فعال است.",
                    message_id
                )

            elif text == "/help":
                bot.sendMessage(group_id,
                    "📚 راهنما:\n/mute\n/unmute\n/warn\n/settings",
                    message_id
                )

            elif text.startswith("/mute"):
                if is_admin(group_id, user_id):
                    reply = msg.get("reply_message_id")
                    if reply:
                        target = msg.get("reply_to_author_object_guid")
                        cursor.execute("INSERT INTO mutes VALUES(?,?)", (target, group_id))
                        conn.commit()
                        bot.sendMessage(group_id, "🔇 کاربر mute شد", message_id)

            elif text.startswith("/unmute"):
                if is_admin(group_id, user_id):
                    reply = msg.get("reply_to_author_object_guid")
                    cursor.execute("DELETE FROM mutes WHERE user_id=? AND group_id=?",
                                   (reply, group_id))
                    conn.commit()
                    bot.sendMessage(group_id, "🔊 کاربر unmute شد", message_id)

            elif text.startswith("/warn"):
                if is_admin(group_id, user_id):
                    target = msg.get("reply_to_author_object_guid")

                    cursor.execute("""
                        INSERT INTO warns VALUES(?,?,1)
                        ON CONFLICT(user_id,group_id)
                        DO UPDATE SET count=count+1
                    """, (target, group_id))
                    conn.commit()

                    cursor.execute("SELECT count FROM warns WHERE user_id=? AND group_id=?",
                                   (target, group_id))
                    count = cursor.fetchone()[0]

                    bot.sendMessage(group_id, f"⚠️ اخطار {count}/3", message_id)

                    if count >= 3:
                        cursor.execute("INSERT INTO mutes VALUES(?,?)", (target, group_id))
                        conn.commit()
                        bot.sendMessage(group_id, "🔇 کاربر بن شد", message_id)

            # ================= ANTI SPAM =================
            now = time.time()
            key = (group_id, user_id)

            if key in last_msg_time:
                if now - last_msg_time[key] < 2:
                    try:
                        bot.deleteMessage(group_id, message_id)
                    except:
                        pass

            last_msg_time[key] = now

            # ================= MUTE CHECK =================
            cursor.execute("SELECT * FROM mutes WHERE user_id=? AND group_id=?",
                           (user_id, group_id))
            if cursor.fetchone():
                try:
                    bot.deleteMessage(group_id, message_id)
                except:
                    pass

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
