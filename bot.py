import os
import sys
import requests
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

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
# TELEGRAM BEFEHLE (KORREKTE SIGNATUR)
# =====================================================
def start(update: Update, context: CallbackContext):
    """Start-Befehl /start"""
    update.message.reply_text(
        "🤖 *ValueEdge Scanner Bot*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📋 *Verfügbare Befehle:*\n"
        "• /start – Diese Hilfe anzeigen\n"
        "• /scan – Neuen Value Scan starten\n"
        "• /bets – Aktuelle Value Bets anzeigen\n"
        "• /stats – System Statistiken\n"
        "• /health – Systemstatus prüfen\n\n"
        "🚀 *Bereit für Value Bets!*\n"
        "Tippe /scan um loszulegen!",
        parse_mode='Markdown'
    )

def scan(update: Update, context: CallbackContext):
    """Scan starten /scan"""
    update.message.reply_text("🔄 *Scan wird gestartet...*\nBitte warten (30-60 Sekunden)...", parse_mode='Markdown')
    
    result = post_backend("/scan")
    
    if result:
        bets_found = result.get("total_value_bets", 0)
        if bets_found > 0:
            update.message.reply_text(
                f"✅ *Scan abgeschlossen!*\n\n"
                f"🏆 **{bets_found} Value Bets** gefunden\n"
                f"⏱️ Dauer: {result.get('duration_seconds', 0):.1f}s\n\n"
                "📊 *Details:*\n"
                f"• Premier League: {len([b for b in result.get('results', []) if b.get('league') == 'Premier League'])} Bets\n"
                f"• Bundesliga: {len([b for b in result.get('results', []) if b.get('league') == 'Bundesliga'])} Bets\n\n"
                "Tippe /bets um sie anzuzeigen!",
                parse_mode='Markdown'
            )
        else:
            update.message.reply_text(
                "🤷 *Keine Value Bets gefunden*\n\n"
                "Das ist normal! Der Markt ist heute effizient.\n"
                "Versuche es in 6 Stunden erneut.\n\n"
                "📈 *Tipp:* Scanne mehr Ligen für bessere Chancen!",
                parse_mode='Markdown'
            )
    else:
        update.message.reply_text("❌ *Scan fehlgeschlagen*\nBackend nicht erreichbar.", parse_mode='Markdown')

def bets(update: Update, context: CallbackContext):
    """Value Bets anzeigen /bets"""
    update.message.reply_text("📊 *Lade Value Bets...*", parse_mode='Markdown')
    data = get_backend("/feed?limit=5")
    
    if data and data.get("bets"):
        bets_list = data["bets"]
        message = "🎯 *Aktuelle Value Bets:*\n\n"
        
        for bet in bets_list:
            match = bet.get("match", "???")
            edge = bet.get("edge", 0)
            pick = bet.get("pick", "")
            
            if pick == "HOME":
                pick_text = "🏠 Heimsieg"
            elif pick == "AWAY":
                pick_text = "✈️ Auswärtssieg"
            else:
                pick_text = "⚖️ Unentschieden"
            
            # Berechne faire Quote
            odds = bet.get("odds_home" if pick == "HOME" else "odds_away" if pick == "AWAY" else "odds_draw", 0)
            fair_odds = round(odds / (1 + edge/100), 2)
            
            message += f"• *{match}*\n"
            message += f"  {pick_text} @{odds}\n"
            message += f"  📈 Edge: +{edge}%\n"
            message += f"  ⚖️ Faire Quote: {fair_odds}\n"
            message += f"  ─────\n"
        
        message += f"\n📊 *Insgesamt:* {len(bets_list)} Value Bets verfügbar\n"
        message += "🔍 Tippe /scan für neue Value Bets!"
        
        update.message.reply_text(message, parse_mode='Markdown')
    else:
        update.message.reply_text(
            "📭 *Keine Value Bets verfügbar*\n\n"
            "Starte einen Scan mit /scan\n"
            "oder probiere es später nochmal!",
            parse_mode='Markdown'
        )

def stats(update: Update, context: CallbackContext):
    """Statistiken /stats"""
    update.message.reply_text("📈 *Lade Statistiken...*", parse_mode='Markdown')
    data = get_backend("/health")
    
    if data:
        message = (
            "📊 *System Status*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"• 🗄️ *Datenbank:* {data.get('database', '❓')}\n"
            f"• 🔗 *Odds API:* {data.get('odds_api', '❓')}\n"
            f"• 🔐 *API Key:* {data.get('backend_api_key_set', '❓')}\n"
            f"• 🕐 *Letzte Prüfung:* {data.get('timestamp', '')[:19]}\n\n"
            "🌐 *Backend:* https://value-bet-backend-production.up.railway.app"
        )
        update.message.reply_text(message, parse_mode='Markdown')
    else:
        update.message.reply_text("❌ Konnte Status nicht laden.", parse_mode='Markdown')

def health(update: Update, context: CallbackContext):
    """Health Check /health"""
    data = get_backend("/health")
    
    if data and data.get("database") == "OK" and data.get("odds_api") == "OK":
        update.message.reply_text("✅ *Alles OK!* 🚀", parse_mode='Markdown')
    else:
        update.message.reply_text("⚠️ *Probleme gefunden*", parse_mode='Markdown')

# =====================================================
# BOT STARTEN (MIT FIX FÜR CONFLICT)
# =====================================================
def main():
    try:
        if not TELEGRAM_BOT_TOKEN:
            print("❌ FEHLER: TELEGRAM_BOT_TOKEN nicht gesetzt!")
            sys.exit(1)
        
        # Updater mit Konfiguration gegen Conflict
        updater = Updater(
            TELEGRAM_BOT_TOKEN, 
            use_context=True,
            request_kwargs={
                'read_timeout': 10,
                'connect_timeout': 10
            }
        )
        
        # Dispatcher holen
        dispatcher = updater.dispatcher
        
        # Befehle hinzufügen
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("scan", scan))
        dispatcher.add_handler(CommandHandler("bets", bets))
        dispatcher.add_handler(CommandHandler("stats", stats))
        dispatcher.add_handler(CommandHandler("health", health))
        
        print("🤖 Telegram Bot wird gestartet...")
        print("✅ Python Version: 3.11")
        print("✅ Telegram Bot Version: 13.15")
        print("✅ use_context=True aktiviert")
        print("✅ Conflict-Fix aktiviert")
        print("🚀 Bot läuft! Drücke Ctrl+C zum Beenden.")
        
        # Bot starten
        updater.start_polling(
            drop_pending_updates=True,  # Alte Updates ignorieren
            timeout=10,
            poll_interval=0.5
        )
        updater.idle()
        
    except Exception as e:
        logger.error(f"Bot Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()