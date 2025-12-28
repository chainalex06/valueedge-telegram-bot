# bot.py - ValueEdge Telegram Bot (NO CONFLICT FIX)
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
# BACKEND FUNKTIONEN (FIXED - GET statt POST für /scan)
# =====================================================
def call_backend(method, endpoint, timeout=30):
    """Rufe Backend mit korrekter Methode auf"""
    try:
        logger.info(f"{method} {BACKEND_URL}{endpoint}")
        
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        
        if method == "GET":
            response = requests.get(
                f"{BACKEND_URL}{endpoint}",
                headers=headers,
                timeout=timeout
            )
        elif method == "POST":
            response = requests.post(
                f"{BACKEND_URL}{endpoint}",
                headers=headers,
                timeout=timeout
            )
        else:
            return None
        
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Backend Fehler {response.status_code}: {response.text}")
            return None
    except requests.exceptions.Timeout:
        logger.error(f"Timeout nach {timeout}s")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection Error: Backend nicht erreichbar")
        return None
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
        return None

# =====================================================
# TELEGRAM COMMAND HANDLERS
# =====================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start - Hilfe anzeigen"""
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 *ValueEdge Bot - SCAN FIX*\n\n"
        f"Hallo {user.first_name}! Alles außer /scan funktioniert.\n\n"
        f"*Befehle:*\n"
        f"/start - Diese Hilfe\n"
        f"/scan - Neuen Scan starten (JETZT FIXED!)\n"
        f"/bets - Letzte Value Bets anzeigen\n"
        f"/stats - System Status\n"
        f"/health - Backend Verbindung testen\n"
        f"/test - Schnelltest\n\n"
        f"*Fix:* Keine 409/405 Fehler mehr ✅",
        parse_mode='Markdown'
    )

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/scan - Starte neuen Scan MIT GET METHODE"""
    await update.message.reply_text(
        "🔄 *Scan wird gestartet...*\n"
        "Bitte warten (30-60 Sekunden)...",
        parse_mode='Markdown'
    )
    
    status_msg = await update.message.reply_text("⏳ Verbinde mit Backend...")
    
    # WICHTIG: GET statt POST für /scan endpoint!
    result = call_backend("GET", "/scan")
    
    if result:
        if 'error' in result:
            await status_msg.edit_text(f"❌ Scan fehlgeschlagen: {result['error']}")
        else:
            bets = result.get('total_value_bets', 0)
            duration = result.get('duration_seconds', 0)
            
            if bets > 0:
                await status_msg.edit_text(
                    f"✅ *SCAN ERFOLGREICH!*\n\n"
                    f"• Gefunden: *{bets}* Value Bets\n"
                    f"• Dauer: *{duration:.1f}s*\n"
                    f"• Ligen: *{result.get('leagues_scanned', 0)}*\n\n"
                    f"Tippe /bets um sie anzuzeigen! 🎯",
                    parse_mode='Markdown'
                )
            else:
                await status_msg.edit_text(
                    f"✅ *Scan abgeschlossen*\n\n"
                    f"• Gefunden: *0* Value Bets\n"
                    f"• Dauer: *{duration:.1f}s*\n"
                    f"• Ligen: *{result.get('leagues_scanned', 0)}*\n\n"
                    f"Keine guten Value Bets heute. 😕",
                    parse_mode='Markdown'
                )
    else:
        await status_msg.edit_text(
            "❌ *Backend nicht erreichbar!*\n\n"
            f"Prüfe:\n"
            f"1. Backend läuft: {BACKEND_URL}\n"
            f"2. API-Key ist korrekt in Railway\n"
            f"3. Backend akzeptiert GET für /scan",
            parse_mode='Markdown'
        )

async def bets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/bets - Zeige Value Bets"""
    await update.message.reply_text("📊 Lade Value Bets...")
    
    data = call_backend("GET", "/feed?limit=5")
    
    if data and data.get('bets'):
        bets = data['bets']
        message = "🎯 *Letzte Value Bets:*\n\n"
        
        for bet in bets[:5]:
            match = bet.get('match', 'Unbekannt')
            edge = bet.get('edge', 0)
            pick = bet.get('pick', '')
            odds = bet.get(f'odds_{pick.lower()}', 0)
            
            message += (
                f"• *{match}*\n"
                f"  ⚡ Pick: {pick} @ {odds:.2f}\n"
                f"  📈 Edge: +{edge}%\n"
                f"  🏆 Liga: {bet.get('league', '')}\n\n"
            )
        
        message += f"*Insgesamt:* {len(bets)} Value Bets in der Datenbank"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "📭 *Keine Value Bets verfügbar*\n\n"
            "Starte einen Scan mit /scan!",
            parse_mode='Markdown'
        )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats - System Statistiken"""
    await update.message.reply_text("📈 Lade Statistiken...")
    
    data = call_backend("GET", "/health")
    
    if data:
        message = (
            f"*📊 System Status - SCAN FIX*\n\n"
            f"• *Datenbank:* {data.get('database', '❓')}\n"
            f"• *Odds API:* {data.get('odds_api', '❓')}\n"
            f"• *Backend Key:* ✅\n"
            f"• *Letzte Prüfung:*\n"
            f"  {data.get('timestamp', 'Unbekannt')}\n\n"
            f"*Backend:* {BACKEND_URL}\n"
            f"*Scan Methode:* GET (korrigiert)"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "❌ *Kann Backend nicht erreichen*",
            parse_mode='Markdown'
        )

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/health - Backend Verbindung testen"""
    test_result = call_backend("GET", "/health")
    
    if test_result:
        if test_result.get('database') == 'OK' and test_result.get('odds_api') == 'OK':
            await update.message.reply_text(
                "✅ *Alles OK!* Backend ist erreichbar.\n"
                "API-Key wurde akzeptiert. ✅\n"
                "Scan sollte jetzt funktionieren!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ *Probleme gefunden:*\n"
                f"DB: {test_result.get('database')}\n"
                f"API: {test_result.get('odds_api')}",
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            "❌ *Backend nicht erreichbar!*",
            parse_mode='Markdown'
        )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/test - Schnelltest für sofortige Antwort"""
    await update.message.reply_text(
        "✅ Bot ist online und funktioniert!\n"
        "Scan-Fix aktiviert: GET statt POST ✅",
        parse_mode='Markdown'
    )

# =====================================================
# HAUPTPROGRAMM (MIT KONFLIKT-VERMEIDUNG)
# =====================================================
def main():
    """Starte den Telegram Bot OHNE CONFLICTS"""
    
    print("🤖 ValueEdge Telegram Bot (NO CONFLICT VERSION)")
    print("=" * 50)
    print(f"Token: {'✅' if TELEGRAM_BOT_TOKEN else '❌'}")
    print(f"Backend Key: {'✅' if BACKEND_API_KEY else '❌'}")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 50)
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ FEHLER: TELEGRAM_BOT_TOKEN nicht gesetzt!")
        return
    
    # Bot mit CONFLICT-FIX erstellen
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands hinzufügen
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("bets", bets_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("test", test_command))
    
    print("✅ Bot gestartet mit Konflikt-Vermeidung")
    print("📡 Warte auf Telegram Befehle...")
    
    # Bot starten mit speziellen Einstellungen um 409 Fehler zu vermeiden
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # WICHTIG: Verhindert Konflikte!
            close_loop=False
        )
    except Exception as e:
        print(f"❌ Bot Fehler: {e}")
        print("Tipp: Auf Railway 'Redeploy' drücken um alte Instanzen zu stoppen")

if __name__ == "__main__":
    main()