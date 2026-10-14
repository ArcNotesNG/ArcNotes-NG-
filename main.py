import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8852392459:AAFIWW1WojDxs_apFw82hZgqP3otepujKKQ"
PAYSTACK_SECRET = "sk_live_35f4d452292fa1fcecd7b46c0e2db76a2905a0f4"

PRODUCTS = {
    "100l": {"name": "100 Level - All Notes", "price": 1000},
    "200l": {"name": "200 Level - All Notes", "price": 1000},
    "300l": {"name": "300 Level - All Notes", "price": 1000},
    "400l": {"name": "400 Level - All Notes", "price": 1000},
    "500l": {"name": "500 Level - All Notes", "price": 1000},
    "full": {"name": "FULL PACK (100L-500L)", "price": 4000},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = []
    for pid, p in PRODUCTS.items():
        kb.append([InlineKeyboardButton(f"{p['name']} - ₦{p['price']}", callback_data=f"buy_{pid}")])
    await update.message.reply_text("Welcome to ArcNotes NG! 📚\nAll Architecture Notes - ₦1,000 per level\n\nSelect level to buy:", reply_markup=InlineKeyboardMarkup(kb))

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pid = q.data.replace("buy_", "")
    context.user_data["pid"] = pid
    p = PRODUCTS[pid]
    await q.message.reply_text(f"You chose: {p['name']}\nPrice: ₦{p['price']}\n\nSend your EMAIL to get payment link:")

async def email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    pid = context.user_data.get("pid")
    if not pid:
        await update.message.reply_text("Type /start to select a level first")
        return
    p = PRODUCTS[pid]
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    data = {"email": email, "amount": p["price"]*100, "metadata": {"product": pid}}
    r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers).json()
    if r.get("status"):
        url = r["data"]["authorization_url"]
        ref = r["data"]["reference"]
        kb = [[InlineKeyboardButton("💳 PAY NOW", url=url)], [InlineKeyboardButton("✅ I Have Paid", callback_data=f"check_{ref}")]]
        await update.message.reply_text(f"Link for {p['name']} - ₦{p['price']}\nClick PAY NOW:", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(f"Error: {r.get('message')}")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ref = q.data.replace("check_", "")
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}", headers=headers).json()
    if r.get("data", {}).get("status") == "success":
        await q.message.reply_text(f"✅ Payment Confirmed! Reference: {ref}\nWe will send your notes ASAP.")
    else:
        await q.message.reply_text("Not paid yet. Pay first then click again.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
app.add_handler(CallbackQueryHandler(check, pattern="^check_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, email_handler))
app.run_polling()
