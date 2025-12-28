import os
import sys
import requests
import logging
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler

# =====================================================
# KONFIGURATION
# =====================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY", "")
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
# BACKEND FUNKTIONEN
# =====================================================
def get_backend(endpoint):
    try:
        response = requests.get(
            f"{BACKEND_URL}{endpoint}",
            headers={"X-API-Key": BACKEND_API_KEY},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Backend Fehler {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Verbindungsfehler: {e}")
        return None

def post_backend(endpoint):
    try:
        response = requests.post(
            f"{BACKEND_URL}{endpoint}",
            headers={"X-API-Key": BACKEND_API_KEY},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Scan Fehler {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Scan Verbindungsfehler: {e}")
        return None

# =====================================================
# TELEGRAM BEFEHLE (EINFACH & FUNKTIONIEREND)
# =====================================================
def start(bot, update):
    update.message.reply_text(
        "🤖 *ValueEdge Bot*\n\n"
        "Verfügbare Befehle:\n"
        "/start - Diese Hilfe\n"
        "/scan - Neuen Scan starten\n"
        "/bets - Value Bets anzeigen\n"
        "/stats - Statistiken\n"
        "/health - Systemstatus\n\n"
        "Bot ist bereit! 🚀",
        parse_mode='Markdown'
    )

def scan(bot, update):
    update.message.reply_text("🔄 Starte Scan...")
    result = post_backend("/scan")
    
    if result:
        bets_found = result.get("total_value_bets", 0)
        if bets_found > 0:
            update.message.reply_text(
                f"✅ *Scan fertig!*\n\n"
                f"🏆 **{bets_found} Value Bets** gefunden\n"
                f"⏱️ Dauer: {result.get('duration_seconds', 0):.1f}s\n\n"
                "Tippe /bets um sie zu sehen!",
                parse_mode='Markdown'
            )
        else:
            update.message.reply_text(
                "🤷 *Keine Value Bets gefunden*\n"
                "Markt ist effizient heute.",
                parse_mode='Markdown'
            )
    else:
        update.message.reply_text("❌ Scan fehlgeschlagen")

def bets(bot, update):
    update.message.reply_text("📊 Lade Value Bets...")
    data = get_backend("/feed?limit=5")
    
    if data and data.get("bets"):
        bets_list = data["bets"]
        message = "🎯 *Aktuelle Value Bets:*\n\n"
        
        for bet in bets_list:
            match = bet.get("match", "???")
            edge = bet.get("edge", 0)
            pick = bet.get("pick", "")
            
            if pick == "HOME":
                pick_text = "Heimsieg"
            elif pick == "AWAY":
                pick_text = "Auswärtssieg"
            else:
                pick_text = "Unentschieden"
            
            message += f"• *{match}*\n"
            message += f"  🎯 {pick_text} (+{edge}%)\n"
            message += f"  ---\n"
        
        message += f"\nTotal: {len(bets_list)} Value Bets"
        update.message.reply_text(message, parse_mode='Markdown')
    else:
        update.message.reply_text(
            "📭 *Keine Value Bets verfügbar*\n"
            "Tippe /scan um neue zu suchen.",
            parse_mode='Markdown'
        )

def stats(bot, update):
    data = get_backend("/health")
    
    if data:
        message = (
            "📊 *System Status*\n\n"
            f"• Datenbank: {data.get('database', '❓')}\n"
            f"• Odds API: {data.get('odds_api', '❓')}\n"
            f"• Letzte Prüfung: {data.get('timestamp', '')[:19]}"
        )
        update.message.reply_text(message, parse_mode='Markdown')
    else:
        update.message.reply_text("❌ Konnte Status nicht laden")

def health(bot, update):
    data = get_backend("/health")
    
    if data and data.get("database") == "OK" and data.get("odds_api") == "OK":
        update.message.reply_text("✅ *Alles OK!*", parse_mode='Markdown')
    else:
        update.message.reply_text("⚠️ *Probleme gefunden*", parse_mode='Markdown')

# =====================================================
# BOT STARTEN (EINFACHSTE VERSION)
# =====================================================
def main():
    try:
        if not TELEGRAM_BOT_TOKEN:
            print("❌ FEHLER: TELEGRAM_BOT_TOKEN nicht gesetzt!")
            sys.exit(1)
        
        # Updater erstellen (OHNE use_context - für ältere Versionen)
        updater = Updater(TELEGRAM_BOT_TOKEN)
        
        # Befehle hinzufügen
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("scan", scan))
        dp.add_handler(CommandHandler("bets", bets))
        dp.add_handler(CommandHandler("stats", stats))
        dp.add_handler(CommandHandler("health", health))
        
        print("🤖 Telegram Bot wird gestartet...")
        print("✅ Python Version: 3.11")
        print("✅ Telegram Bot Version: 13.15")
        print("🚀 Bot läuft! Drücke Ctrl+C zum Beenden.")
        
        # Bot starten
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Bot Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()