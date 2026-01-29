from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.request import HTTPXRequest
import asyncio, json, os, time, traceback

TOKEN = "8255986825:AAHROWxd3Wa2DOVu5_Wvo3IwQu3sMokEQBE"
DATA_FILE = "data.json"
START_MONEY = 2000

# =====================
# فروشگاه کامل طبق لیست شما
# =====================
SHOP = {
    # کارخانه‌ها
    "کارخانه اقتصاد": {"price": 10000, "income": 1000},
    "کارخانه مبادله": {"price": 500, "income": 0},
    "کارگاه اقتصادی": {"price": 1000, "income": 100},

    # موشک‌ها
    "موشک ضعیف": {"price": 40, "damage": 2},
    "موشک متوسط": {"price": 60, "damage": 3},
    "موشک قوی": {"price": 80, "damage": 5},
    "موشک هایپر سونیک": {"price": 140, "damage": 5},
    "موشک بالستیک": {"price": 160, "damage": 10},

    # پدافند
    "پدافند ضعیف": {"price": 1000, "defense": 10},
    "پدافند متوسط": {"price": 2000, "defense": 20},
    "پدافند قوی": {"price": 4000, "defense": 35},
    "لانچر": {"price": 1200},

    # نیروی زمینی
    "تانک عادی": {"price": 400, "damage": 400},
    "ارتش 1000 نفره": {"price": 800},

    # جنگنده‌ها
    "جنگنده B15": {"price": 800, "damage": 10, "level": "ضعیف", "missiles": 10},
    "جت جنگنده B2": {"price": 1000, "damage": 20, "level": "معمولی", "missiles": 20},
    "جنگنده B16": {"price": 1500, "damage": 50, "level": "قوی", "missiles": 50},

    # هواپیماها
    "هواپیما رئیس جمهور": {"price": 3000},
    "هواپیما عادی": {"price": 1000, "capacity": 5000},

    # کشتی‌ها
    "کشتی حمل نیرو": {"price": 2000, "damage": 5},
    "کشتی حمل کالا": {"price": 4000},

    # ویژه
    "بمب اتم": {"price": 30000},

    # پایگاه‌ها
    "پایگاه نظامی": {"price": 500},
    "پایگاه دریایی": {"price": 500},
    "پایگاه هوایی": {"price": 500},
}

# =====================
# ذخیره / بارگذاری دیتا
# =====================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            print("⚠️ مشکل در بارگذاری دیتا، دیتا از اول ساخته میشه")
    return {}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠️ مشکل ذخیره دیتا:", e)

users = load_data()

def get_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "money": START_MONEY,
            "items": {"کارخانه اقتصاد": 1}  # فقط 1 کارخانه اقتصاد از اول
        }
        save_data()
    return users[uid]

# =====================
# Handlers
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"🎮 بازی شروع شد!\n💰 پول: {user['money']}\n🏭 کارخانه اقتصاد: {user['items'].get('کارخانه اقتصاد',0)}\n\n"
        "/shop فروشگاه\n/profile پروفایل\n\n✍ برای خرید دست جمعی: اسم آیتم + تعداد\nمثال: کارگاه اقتصادی 5"
    )

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🛒 فروشگاه:\n\n"
    for k,v in SHOP.items():
        text += f"• {k} ➜ {v['price']} پول\n"
    text += "\n✍ اسم آیتم + تعداد را بفرست تا بخری (مثال: کارگاه اقتصادی 5)"
    await update.message.reply_text(text)

# =====================
# خرید دست جمعی اصلاح شده
# =====================
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    text = update.message.text.strip()

    parts = text.split()
    if not parts:
        return

    # بررسی اینکه آخرین بخش عدد باشه
    if parts[-1].isdigit():
        count = int(parts[-1])
        if count < 1: count = 1
        item = " ".join(parts[:-1])
    else:
        count = 1
        item = " ".join(parts)

    if item not in SHOP:
        await update.message.reply_text("❌ آیتم موجود نیست")
        return

    price = SHOP[item]["price"] * count
    if user["money"] < price:
        await update.message.reply_text(f"❌ پول کافی نیست برای خرید {count} عدد {item}")
        return

    user["money"] -= price
    user["items"][item] = user["items"].get(item, 0) + count
    save_data()

    await update.message.reply_text(f"✅ {count} عدد {item} خریدی\n💰 پول باقی‌مانده: {user['money']}")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    text = f"👤 پروفایل\n💰 پول: {user['money']}\n\n🏭 دارایی‌ها:\n"
    for k,v in user["items"].items():
        text += f"{k}: {v}\n"
    await update.message.reply_text(text)

# =====================
# درآمد نیم ساعته
# =====================
async def income_loop():
    while True:
        try:
            await asyncio.sleep(1800)  # هر نیم ساعت
            for u in users.values():
                income = 0
                for item,count in u["items"].items():
                    income += SHOP.get(item,{}).get("income",0)*count
                u["money"] += income
            save_data()
        except Exception as e:
            print("⚠️ مشکل در حلقه درآمد:", e)
            traceback.print_exc()
            await asyncio.sleep(10)

async def post_init(app):
    app.create_task(income_loop())

# =====================
# MAIN LOOP پایدار + HTTPXRequest
# =====================
def main():
    while True:
        try:
            request = HTTPXRequest(
                connect_timeout=30,
                read_timeout=30,
                write_timeout=30,
                pool_timeout=30
            )

            app = Application.builder()\
                .token(TOKEN)\
                .request(request)\
                .post_init(post_init)\
                .build()

            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("shop", shop))
            app.add_handler(CommandHandler("profile", profile))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buy))

            print("🤖 Bot running...")
            app.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
                close_loop=False
            )

        except Exception as e:
            print("⚠️ ربات قطع شد! تلاش مجدد در ۵ ثانیه...")
            print(e)
            time.sleep(5)

if __name__ == "__main__":
    main()