# bot.py - ULTIMATE TOKEN CLEAN FIX
import os
import re
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =====================================================
# ULTIMATE TOKEN CLEANER
# =====================================================
def super_clean_token(raw_token):
    """Entfernt ALLE unsichtbaren und problematischen Zeichen"""
    if not raw_token:
        return None
    
    # 1. Entferne alle nicht-ASCII Zeichen
    ascii_only = ''.join(char for char in raw_token if ord(char) < 128)
    
    # 2. Entferne alle Steuerzeichen (non-printable)
    printable = ''.join(char for char in ascii_only if char.isprintable())
    
    # 3. Entferne Leerzeichen am Anfang/Ende und Zeilenumbrüche
    cleaned = printable.strip()
    
    # 4. Ersetze multiple Leerzeichen durch eins
    cleaned = re.sub(r'\s+', '', cleaned)
    
    # 5. Prüfe Format: sollte sein "1234567890:ABCdefGHIjklMnOprSTUvwxYZ"
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', cleaned):
        print(f"⚠️ WARNUNG: Token nach Bereinigung sieht falsch aus: {cleaned[:15]}...")
        return None
    
    return cleaned

# =====================================================
# KONFIGURATION MIT SUPER-CLEANING
# =====================================================
RAW_TOKEN_FROM_ENV = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_TOKEN = super_clean_token(RAW_TOKEN_FROM_ENV)
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
def get_backend(endpoint, timeout=30):
    try:
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        
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
# TELEGRAM COMMANDS (EINFACHER)
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ValueEdge Bot - TOKEN FIX*\n\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Neuen Scan starten\n"
        "✅ /bets - Value Bets anzeigen\n"
        "✅ /stats - System Status\n"
        "✅ /test - Test ob Bot funktioniert",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔄 Scan startet...")
    
    result = get_backend("/scan", timeout=90)
    
    if result is None:
        await msg.edit_text("❌ Backend nicht erreichbar")
    elif 'error' in result:
        await msg.edit_text(f"❌ Fehler: {result['error']}")
    elif 'total_value_bets' in result:
        bets = result.get('total_value_bets', 0)
        await msg.edit_text(f"✅ {bets} Value Bets gefunden")
    else:
        await msg.edit_text("✅ Scan durchgeführt")

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/feed?limit=5")
    
    if result and 'bets' in result and result['bets']:
        bets_list = result['bets']
        message = "🎯 *Value Bets:*\n\n"
        for bet in bets_list[:5]:
            message += f"• {bet.get('match', '?')} (+{bet.get('edge', 0)}%)\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("📭 Keine Value Bets. Starte /scan")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if result:
        message = f"📊 *Status:*\nDB: {result.get('database', '?')}\nAPI: {result.get('odds_api', '?')}"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Status nicht verfügbar")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot ist online und funktioniert!")

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("=" * 60)
    print("🔐 BOT START - TOKEN CLEANING ACTIVE")
    print("=" * 60)
    
    # Token-Diagnose
    print(f"RAW Token aus ENV (erste 20 Zeichen): '{RAW_TOKEN_FROM_ENV[:20]}'")
    print(f"RAW Token Länge: {len(RAW_TOKEN_FROM_ENV)}")
    print(f"Gereinigter Token (erste 15 Zeichen): '{TELEGRAM_BOT_TOKEN[:15] if TELEGRAM_BOT_TOKEN else 'None'}'")
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ KRITISCH: Token ist leer oder konnte nicht gereinigt werden!")
        print("   Bitte in Railway prüfen und manuell neu eingeben.")
        return
    
    print(f"✅ Token erfolgreich gereinigt: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"✅ Backend: {BACKEND_URL}")
    print("=" * 60)
    
    # Bot starten
    try:
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("scan", scan))
        app.add_handler(CommandHandler("bets", bets))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("test", test))
        
        print("✅ Bot wird gestartet...")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Bot konnte nicht gestartet werden: {e}")
        print("Mögliche Ursachen:")
        print("1. Token ist falsch (mit @BotFather prüfen)")
        print("2. Token hat unsichtbare Zeichen (manuell neu eingeben)")
        print("3. Netzwerkproblem")

if __name__ == "__main__":
    main()