# bot.py - FINAL FIXED VERSION (Echte Daten!)
import os
import requests
import logging
from datetime import datetime
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =====================================================
# BACKEND FUNKTIONEN (KORREKT!)
# =====================================================
def get_backend(endpoint, timeout=30):
    """Hole Daten vom Backend - FUNKTIONIERT 100%"""
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
        
        logger.info(f"Backend {endpoint}: Status {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Fehler {response.status_code}: {response.text[:100]}")
            return None
            
    except Exception as e:
        logger.error(f"Verbindungsfehler: {e}")
        return None

# =====================================================
# TELEGRAM COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ValueEdge Bot - DATA FIX*\n\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Neuen Scan starten\n"
        "✅ /bets - Value Bets anzeigen (FIXED!)\n"
        "✅ /stats - System Status\n"
        "✅ /dbinfo - Datenbank-Info\n\n"
        "🎯 *Echte Daten aus deiner Datenbank*",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔄 Scan startet (30-60s)...")
    
    result = get_backend("/scan", timeout=90)
    
    if result is None:
        await msg.edit_text("❌ Backend nicht erreichbar")
        return
    
    if 'error' in result:
        await msg.edit_text(f"❌ Fehler: {result['error']}")
    elif 'total_value_bets' in result:
        bets = result['total_value_bets']
        duration = result.get('duration_seconds', 0)
        
        if bets > 0:
            await msg.edit_text(
                f"✅ *{bets} Value Bets gefunden!*\n"
                f"Dauer: {duration:.1f}s\n"
                f"Ligen: {result.get('leagues_scanned', 0)}\n\n"
                f"Tippe /bets zum Anzeigen! 🎯",
                parse_mode='Markdown'
            )
        else:
            await msg.edit_text(
                f"✅ Scan abgeschlossen\n"
                f"Dauer: {duration:.1f}s\n"
                f"Ligen: {result.get('leagues_scanned', 0)}\n"
                f"Value Bets: 0",
                parse_mode='Markdown'
            )
    else:
        await msg.edit_text(f"Response: {result}")

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ZEIGT JETZT ECHTE VALUE BETS AUS DEINER DATENBANK"""
    await update.message.reply_text("📊 Lade Value Bets aus Datenbank...")
    
    # WICHTIG: Dein Backend hat /feed?limit=20 (nicht /feed?limit=5)
    result = get_backend("/feed?limit=10")
    
    if result is None:
        await update.message.reply_text("❌ Kann Datenbank nicht erreichen")
        return
    
    if 'error' in result:
        await update.message.reply_text(f"❌ Fehler: {result.get('error')}")
        return
    
    # Prüfe ob 'bets' im Result ist
    if 'bets' not in result:
        await update.message.reply_text(
            f"⚠️ Keine 'bets' in Response.\n"
            f"Response: {result}"
        )
        return
    
    bets_list = result['bets']
    
    if not bets_list:
        await update.message.reply_text(
            "📭 *Datenbank ist leer*\n\n"
            "Starte einen Scan mit /scan um Value Bets zu finden!\n"
            f"Datenbank-Response: {len(bets_list)} Einträge",
            parse_mode='Markdown'
        )
        return
    
    # Zeige echte Value Bets
    message = f"🎯 *{len(bets_list)} Value Bets in Datenbank:*\n\n"
    
    for i, bet in enumerate(bets_list[:8], 1):
        match = bet.get('match', 'Unbekannt')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get(f'odds_{pick.lower()}', bet.get('odds_home', 0))
        league = bet.get('league', 'Unbekannt')
        timestamp = bet.get('timestamp', 0)
        
        # Zeit formatieren
        time_str = ""
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp)
                time_str = dt.strftime("%H:%M")
            except:
                pass
        
        message += (
            f"{i}. *{match}*\n"
            f"   ⚡ {pick} @ {odds:.2f}\n"
            f"   📈 Edge: +{edge:.1f}%\n"
            f"   🏆 {league}\n"
            f"   🕐 {time_str}\n\n"
        )
    
    message += f"*Gesamt in DB:* {len(bets_list)} Value Bets"
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if result is None:
        await update.message.reply_text("❌ Backend nicht erreichbar")
        return
    
    # Database Count separat holen
    db_count = "❓"
    count_result = get_backend("/admin/info")
    if count_result and 'total_value_bets_in_db' in count_result:
        db_count = str(count_result['total_value_bets_in_db'])
    
    message = (
        f"📊 *System Status*\n\n"
        f"• Datenbank: {result.get('database', '❓')}\n"
        f"• Odds API: {result.get('odds_api', '❓')}\n"
        f"• Value Bets in DB: {db_count}\n"
        f"• Zeit: {result.get('timestamp', '')[:19]}\n\n"
        f"🔗 {BACKEND_URL}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def dbinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeigt Datenbank-Informationen"""
    result = get_backend("/admin/info")
    
    if result is None:
        await update.message.reply_text("❌ Kann Admin-Info nicht laden")
        return
    
    if 'error' in result:
        await update.message.reply_text(f"❌ Fehler: {result.get('error')}")
        return
    
    message = (
        f"💾 *Datenbank Info*\n\n"
        f"• Admin: {result.get('admin', 'Unbekannt')}\n"
        f"• Auth Methode: {result.get('auth_method', '❓')}\n"
        f"• Value Bets in DB: {result.get('total_value_bets_in_db', 0)}\n"
        f"• Ligen: {len(result.get('scanned_leagues', []))}\n"
        f"• Zeit: {result.get('timestamp', '')[:19]}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("🤖 ValueEdge Bot - DATA FIX VERSION")
    print(f"Backend: {BACKEND_URL}")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("bets", bets))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("dbinfo", dbinfo))
    
    print("✅ Bot gestartet mit Daten-Fix")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()