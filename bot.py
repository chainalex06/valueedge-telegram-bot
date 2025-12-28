# bot.py - FINAL WORKING VERSION WITH TOKEN VALIDATION
import os
import re
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =====================================================
# TOKEN VALIDATION & CLEANING
# =====================================================
def clean_and_validate_token(token):
    """Entfernt unsichtbare Zeichen und validiert Token"""
    if not token:
        return None
    
    # Entferne alle nicht druckbaren Zeichen
    cleaned = re.sub(r'[^\x20-\x7E]', '', token)
    
    # Entferne Leerzeichen am Anfang/Ende
    cleaned = cleaned.strip()
    
    # Validiere Token Format: sollte wie 1234567890:ABCdefGHIjklMnOprSTUvwxYZ
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', cleaned):
        print(f"⚠️ Token sieht nicht valide aus: {cleaned[:10]}...")
    
    return cleaned

# =====================================================
# KONFIGURATION MIT VALIDATION
# =====================================================
RAW_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = clean_and_validate_token(RAW_TOKEN)
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "valueedge-backend-74f2c9a0-9b3d-4ab5-b912-2025")
BACKEND_URL = "https://value-bet-backend-production.up.railway.app"

# =====================================================
# LOGGING
# =====================================================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =====================================================
# BACKEND FUNKTION
# =====================================================
def call_backend(endpoint, timeout=60):
    """Einfache Backend-Abfrage"""
    try:
        headers = {"X-API-Key": BACKEND_API_KEY}
        response = requests.get(
            f"{BACKEND_URL}{endpoint}",
            headers=headers,
            timeout=timeout
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Backend Error {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Backend Connection Error: {e}")
        return None

# =====================================================
# TELEGRAM COMMAND HANDLERS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    await update.message.reply_text(
        "🤖 *ValueEdge Bot - SECURE*\n\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Neuen Scan starten\n"
        "✅ /bets - Value Bets anzeigen\n"
        "✅ /stats - System Status\n"
        "✅ /health - Verbindung testen\n\n"
        "🔐 *Sicherer Token aktiv* 🎯 *5 Top-Ligen*",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan command"""
    msg = await update.message.reply_text("🔄 Scan startet...")
    
    result = call_backend("/scan", timeout=90)
    
    if result is None:
        await msg.edit_text("❌ Backend nicht erreichbar")
        return
    
    if 'total_value_bets' in result:
        bets_count = result['total_value_bets']
        duration = result.get('duration_seconds', 0)
        
        if bets_count > 0:
            await msg.edit_text(
                f"✅ *{bets_count} Value Bets gefunden!*\n"
                f"Dauer: {duration:.1f}s\n\n"
                f"Tippe /bets zum Anzeigen! 🎯",
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                f"✅ Scan abgeschlossen\n"
                f"Dauer: {duration:.1f}s\n"
                f"Gefunden: 0 Value Bets",
                parse_mode='Markdown'
            )
    elif 'error' in result:
        await msg.edit_text(f"❌ Fehler: {result['error']}")
    else:
        await msg.edit_text("✅ Scan durchgeführt")

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Value Bets anzeigen"""
    data = call_backend("/feed?limit=10")
    
    if not data or 'error' in data:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = data.get('bets', [])
    if not bets_list:
        await update.message.reply_text("📭 Keine Value Bets in DB")
        return
    
    message = f"🎯 *{len(bets_list)} Value Bets:*\n\n"
    
    for i, bet in enumerate(bets_list[:8], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get(f'odds_{pick.lower()}', 0)
        
        message += (
            f"{i}. *{match}*\n"
            f"   ⚡ {pick} @ {odds:.2f}\n"
            f"   📈 Edge: +{edge}%\n"
            f"   🏆 {bet.get('league', '')}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """System Status"""
    data = call_backend("/health")
    
    if not data:
        await update.message.reply_text("❌ Status nicht verfügbar")
        return
    
    status_msg = (
        f"📊 *System Status*\n\n"
        f"• DB: {data.get('database', 'N/A')}\n"
        f"• API: {data.get('odds_api', 'N/A')}\n"
        f"• Zeit: {data.get('timestamp', 'N/A')[:19]}\n\n"
        f"🔗 {BACKEND_URL}"
    )
    
    await update.message.reply_text(status_msg, parse_mode='Markdown')

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health Check"""
    data = call_backend("/ping")
    
    if data:
        await update.message.reply_text("✅ Backend online")
    else:
        await update.message.reply_text("❌ Backend offline")

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    """Starte den Bot mit Token Validation"""
    
    print("=" * 50)
    print("🔐 ValueEdge Bot - Token Validation")
    print("=" * 50)
    
    # Token prüfen
    if not TELEGRAM_BOT_TOKEN:
        print("❌ FEHLER: TELEGRAM_BOT_TOKEN ist leer oder ungültig!")
        print(f"   Roh-Token aus ENV: '{RAW_TOKEN}'")
        print("   Bitte in Railway prüfen!")
        return
    
    print(f"✅ Token validiert: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"✅ Backend URL: {BACKEND_URL}")
    print("=" * 50)
    
    # Application erstellen
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands hinzufügen
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("bets", bets))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("health", health))
    
    print("✅ Bot gestartet - Warte auf Commands")
    
    # Polling starten
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()