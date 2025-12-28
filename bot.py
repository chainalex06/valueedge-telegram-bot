# bot.py - SIMPLER Telegram Bot (NO CONFLICT)
import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =====================================================
# KONFIGURATION
# =====================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "valueedge-backend-74f2c9a0-9b3d-4ab5-b912-2025")
BACKEND_URL = "https://value-bet-backend-production.up.railway.app"

# =====================================================
# LOGGING
# =====================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =====================================================
# EINFACHE BACKEND FUNKTION
# =====================================================
def call_backend(method, endpoint, timeout=60):
    try:
        headers = {"X-API-Key": BACKEND_API_KEY}
        url = f"{BACKEND_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        else:
            response = requests.post(url, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Backend {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        logger.error(f"Fehler: {e}")
        return None

# =====================================================
# TELEGRAM COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ValueEdge Bot - FINAL*\n\n"
        "✅ /start - Hilfe\n"
        "✅ /scan - Scan starten\n"
        "✅ /bets - Value Bets\n"
        "✅ /stats - Status\n"
        "✅ /health - Test\n\n"
        "*Fix:* Keine 409/403 Fehler mehr!",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔄 Scan startet...")
    
    result = call_backend("GET", "/scan")
    
    if result and 'error' not in result:
        bets = result.get('total_value_bets', 0)
        await msg.edit_text(f"✅ {bets} Value Bets gefunden! /bets")
    elif result and 'error' in result:
        await msg.edit_text(f"❌ {result['error']}")
    else:
        await msg.edit_text("❌ Backend nicht erreichbar")

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = call_backend("GET", "/feed?limit=5")
    
    if data and data.get('bets'):
        bets = data['bets']
        text = "🎯 *Value Bets:*\n\n"
        for bet in bets:
            text += f"• {bet.get('match')} (+{bet.get('edge')}%)\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text("📭 Keine Value Bets. /scan")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = call_backend("GET", "/health")
    
    if data:
        text = f"📊 Status:\nDB: {data.get('database')}\nAPI: {data.get('odds_api')}"
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("❌ Status nicht verfügbar")

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = call_backend("GET", "/ping")
    
    if data:
        await update.message.reply_text("✅ Backend online")
    else:
        await update.message.reply_text("❌ Backend offline")

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("🤖 SIMPLE BOT - NO CONFLICTS")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("bets", bets))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("health", health))
    
    print("✅ Bot startet...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()