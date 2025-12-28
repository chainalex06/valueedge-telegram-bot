# bot.py - ValueEdge Telegram Bot (SCAN WORKING VERSION)
import os
import requests
import logging
import time
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =====================================================
# KONFIGURATION
# =====================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
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
# BACKEND FUNKTIONEN
# =====================================================
def get_backend(endpoint, timeout=15):
    """Hole Daten vom Backend mit GET"""
    try:
        full_url = f"{BACKEND_URL}{endpoint}"
        logger.info(f"📡 GET {full_url}")
        
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(full_url, headers=headers, timeout=timeout)
        logger.info(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"❌ Fehler {response.status_code}: {response.text[:100]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Timeout nach {timeout}s")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Verbindungsfehler: Backend nicht erreichbar")
        return None
    except Exception as e:
        logger.error(f"⚠️ Unerwartet: {str(e)}")
        return None

def post_backend(endpoint, timeout=30):
    """Sende Daten an Backend mit POST"""
    try:
        full_url = f"{BACKEND_URL}{endpoint}"
        logger.info(f"📡 POST {full_url}")
        
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(full_url, headers=headers, timeout=timeout)
        logger.info(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"❌ Fehler {response.status_code}: {response.text[:100]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Timeout nach {timeout}s")
        return None
    except Exception as e:
        logger.error(f"⚠️ Fehler: {str(e)}")
        return None

# =====================================================
# SCAN FUNKTION (SPEZIELL FÜR /scan)
# =====================================================
def trigger_scan():
    """
    WICHTIG: Dein Backend erwartet GET für /scan!
    Deine main.py zeigt: @app.get("/scan") nicht @app.post("/scan")
    """
    logger.info("🚀 Starte Scan über GET /scan")
    return get_backend("/scan", timeout=60)  # Längeres Timeout für Scan

# =====================================================
# TELEGRAM COMMAND HANDLERS
# =====================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start - Hilfe anzeigen"""
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 *ValueEdge Bot - SCAN AKTIV*\n\n"
        f"Hallo {user.first_name}!\n\n"
        f"✅ /start - Diese Hilfe\n"
        f"✅ /scan - Starte Scan (GET-Methode)\n"
        f"✅ /bets - Zeige Value Bets\n"
        f"✅ /stats - System Status\n"
        f"✅ /health - Verbindungstest\n"
        f"✅ /test - Soforttest\n\n"
        f"*Backend:* {BACKEND_URL}\n"
        f"*Methode:* GET für /scan",
        parse_mode='Markdown'
    )

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/scan - Starte Scan mit GET"""
    # Sofortige Bestätigung
    await update.message.reply_text(
        "🔍 *Scan wird gestartet...*\n"
        "Bitte warten (30-60 Sekunden)...",
        parse_mode='Markdown'
    )
    
    # Statusnachricht
    status_msg = await update.message.reply_text("🔄 Kontaktiere Backend...")
    
    # WICHTIG: Verwende GET für /scan
    result = trigger_scan()
    
    if result is None:
        await status_msg.edit_text(
            "❌ *Backend nicht erreichbar!*\n\n"
            "Mögliche Ursachen:\n"
            "1. Backend ist offline\n"
            "2. Falscher API-Key in Railway\n"
            "3. Netzwerkproblem\n\n"
            f"Prüfe: {BACKEND_URL}/health",
            parse_mode='Markdown'
        )
        return
    
    if 'error' in result:
        await status_msg.edit_text(
            f"❌ *Scan fehlgeschlagen*\n\n"
            f"Fehler: {result['error']}\n\n"
            f"Prüfe Backend Logs.",
            parse_mode='Markdown'
        )
        return
    
    # Erfolgreicher Scan
    bets_count = result.get('total_value_bets', 0)
    duration = result.get('duration_seconds', 0)
    leagues = result.get('leagues_scanned', 0)
    
    if bets_count > 0:
        await status_msg.edit_text(
            f"🎉 *SCAN ERFOLGREICH!*\n\n"
            f"✅ Gefunden: *{bets_count}* Value Bets\n"
            f"⏱️ Dauer: *{duration:.1f}* Sekunden\n"
            f"🏆 Ligen: *{leagues}*\n\n"
            f"Tippe /bets zum Anzeigen!",
            parse_mode='Markdown'
        )
    else:
        await status_msg.edit_text(
            f"✅ *Scan abgeschlossen*\n\n"
            f"• Gefunden: *0* Value Bets\n"
            f"• Dauer: *{duration:.1f}s*\n"
            f"• Ligen: *{leagues}*\n\n"
            f"Keine guten Value Bets gefunden.",
            parse_mode='Markdown'
        )

async def bets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/bets - Zeige Value Bets"""
    await update.message.reply_text("📋 Lade Value Bets...")
    
    data = get_backend("/feed?limit=5")
    
    if data and data.get('bets'):
        bets = data['bets']
        message = "🎯 *Letzte Value Bets:*\n\n"
        
        for i, bet in enumerate(bets[:5], 1):
            match = bet.get('match', 'Unbekannt')
            edge = bet.get('edge', 0)
            pick = bet.get('pick', '')
            odds = bet.get(f'odds_{pick.lower()}', 0)
            
            message += (
                f"{i}. *{match}*\n"
                f"   ⚡ {pick} @ {odds:.2f}\n"
                f"   📈 Edge: +{edge}%\n"
                f"   🏆 {bet.get('league', '')}\n\n"
            )
        
        message += f"*Gesamt:* {len(bets)} Value Bets in DB"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "📭 *Keine Value Bets verfügbar*\n\n"
            "Starte /scan um neue zu finden!",
            parse_mode='Markdown'
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats - System Status"""
    await update.message.reply_text("📊 Prüfe System...")
    
    data = get_backend("/health")
    
    if data:
        db_status = "✅" if data.get('database') == 'OK' else "❌"
        api_status = "✅" if data.get('odds_api') == 'OK' else "❌"
        
        message = (
            f"*System Status*\n\n"
            f"• Datenbank: {db_status}\n"
            f"• Odds API: {api_status}\n"
            f"• API Key: ✅\n"
            f"• Zeit: {data.get('timestamp', 'N/A')}\n\n"
            f"*Backend:* {BACKEND_URL}\n"
            f"*Scan-Methode:* GET"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Kann Status nicht abrufen.")

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/health - Verbindungstest"""
    await update.message.reply_text("🩺 Prüfe Backend...")
    
    data = get_backend("/health")
    
    if data:
        if data.get('database') == 'OK' and data.get('odds_api') == 'OK':
            await update.message.reply_text(
                "✅ *Alles in Ordnung!*\n"
                "Backend erreichbar und alle Systeme online.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ *Probleme*\n"
                f"Datenbank: {data.get('database')}\n"
                f"API: {data.get('odds_api')}",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text("❌ Backend nicht erreichbar.")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/test - Soforttest"""
    await update.message.reply_text(
        "✅ Bot online\n"
        "✅ Commands geladen\n"
        "✅ Backend: " + BACKEND_URL + "\n"
        "✅ /scan verwendet GET-Methode",
        parse_mode='Markdown'
    )

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    """Starte den Bot"""
    
    print("=" * 50)
    print("🤖 ValueEdge Bot - SCAN AKTIV")
    print("=" * 50)
    print(f"Bot Token: {'✅' if TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"Backend Key: {'✅' if BACKEND_API_KEY else '❌'}")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 50)
    print("Wichtig: /scan verwendet GET-Methode!")
    print("=" * 50)
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ FEHLER: Telegram Token fehlt!")
        return
    
    # Application erstellen
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands hinzufügen
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("bets", bets_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("health", health_command))
    app.add_handler(CommandHandler("test", test_command))
    
    print("✅ Bot gestartet")
    print("📡 Warte auf Befehle...")
    
    # Polling starten
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()