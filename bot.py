# bot.py - DIAGNOSE VERSION (für /bets Problem)
import os
import requests
import json
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
# LOGGING (DETAILED)
# =====================================================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =====================================================
# BACKEND FUNKTION MIT DIAGNOSE
# =====================================================
def call_backend_diagnose(endpoint, timeout=30):
    """Backend-Abfrage mit Diagnose-Informationen"""
    try:
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        
        url = f"{BACKEND_URL}{endpoint}"
        logger.info(f"🔍 Anfrage an: {url}")
        logger.info(f"🔑 API Key (erste 10 Zeichen): {BACKEND_API_KEY[:10]}...")
        
        response = requests.get(url, headers=headers, timeout=timeout)
        
        logger.info(f"📊 Status Code: {response.status_code}")
        logger.info(f"📝 Response Header: {dict(response.headers)}")
        logger.info(f"📦 Response (erste 500 Zeichen): {response.text[:500]}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"❌ Fehler: {response.status_code} - {response.text[:200]}")
            return {"error": f"Status {response.status_code}", "details": response.text[:200]}
            
    except Exception as e:
        logger.error(f"💥 Exception: {str(e)}")
        return {"error": str(e)}

# =====================================================
# TELEGRAM COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ValueEdge - DIAGNOSE MODE*\n\n"
        "🔧 Dieser Bot läuft im Diagnose-Modus\n"
        "📊 Probleme mit /bets werden analysiert\n\n"
        "Befehle:\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Neuen Scan starten\n"
        "✅ /bets - Value Bets + Diagnose\n"
        "✅ /test - API Verbindung testen\n"
        "✅ /debug - System-Informationen",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔄 Scan startet...")
    
    result = call_backend_diagnose("/scan", timeout=90)
    
    if not result:
        await msg.edit_text("❌ Keine Antwort vom Backend")
        return
    
    if 'error' in result:
        await msg.edit_text(f"❌ Fehler: {result['error']}")
    elif 'total_value_bets' in result:
        bets = result.get('total_value_bets', 0)
        await msg.edit_text(f"✅ {bets} Value Bets gescannt")
    else:
        await msg.edit_text(f"✅ Scan durchgeführt\n{json.dumps(result, indent=2)[:1000]}")

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DIAGNOSE VERSION - zeigt warum /bets nicht funktioniert"""
    await update.message.reply_text("🔍 Analysiere /bets Problem...")
    
    # Test 1: Direkter Backend-Call
    result = call_backend_diagnose("/feed?limit=5")
    
    if not result:
        await update.message.reply_text("❌ Backend nicht erreichbar")
        return
    
    if 'error' in result:
        message = (
            f"❌ *FEHLER GEFUNDEN:*\n\n"
            f"Problem: {result.get('error')}\n"
            f"Details: {result.get('details', 'Keine')}\n\n"
            f"🔧 *Mögliche Lösungen:*\n"
            f"1. API-Key in Railway prüfen\n"
            f"2. Backend /feed Endpoint testen\n"
            f"3. Supabase Verbindung prüfen"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
        return
    
    # Check if we have bets
    if 'bets' in result:
        bets_list = result['bets']
        if bets_list:
            message = f"🎯 *{len(bets_list)} Value Bets in DB:*\n\n"
            for bet in bets_list[:3]:
                message += f"• {bet.get('match')} (+{bet.get('edge')}%)\n"
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            message = (
                f"📭 *Keine Value Bets in Datenbank*\n\n"
                f"Datenbank ist leer.\n"
                f"Starte /scan um neue Value Bets zu finden.\n\n"
                f"*Response war:*\n"
                f"```json\n{json.dumps(result, indent=2)[:500]}\n```"
            )
            await update.message.reply_text(message, parse_mode='Markdown')
    else:
        message = (
            f"⚠️ *Unerwartete Antwort*\n\n"
            f"Backend antwortet, aber keine 'bets' im Response.\n\n"
            f"*Vollständige Antwort:*\n"
            f"```json\n{json.dumps(result, indent=2)[:1000]}\n```"
        )
        await update.message.reply_text(message, parse_mode='Markdown')

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Testet alle Backend-Endpoints"""
    await update.message.reply_text("🧪 Starte API Tests...")
    
    tests = [
        ("/health", "Health Check"),
        ("/ping", "Ping Test"),
        ("/feed?limit=1", "Datenbank Test"),
        ("/test-filter?quote=2.0&edge=3.0", "Filter Test")
    ]
    
    results = []
    for endpoint, name in tests:
        result = call_backend_diagnose(endpoint)
        status = "✅" if result and 'error' not in result else "❌"
        results.append(f"{status} {name}: {endpoint}")
    
    await update.message.reply_text("\n".join(results))

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug Informationen"""
    info = (
        f"🔧 *SYSTEM INFO*\n\n"
        f"*Bot Token:* {TELEGRAM_BOT_TOKEN[:10]}...\n"
        f"*API Key:* {BACKEND_API_KEY[:10]}...\n"
        f"*Backend URL:* {BACKEND_URL}\n\n"
        f"*Env Variables:*\n"
        f"TELEGRAM_BOT_TOKEN: {'✅ Gesetzt' if TELEGRAM_BOT_TOKEN else '❌ Fehlt'}\n"
        f"BACKEND_API_KEY: {'✅ Gesetzt' if BACKEND_API_KEY else '❌ Fehlt'}\n\n"
        f"*Test Links:*\n"
        f"{BACKEND_URL}/health\n"
        f"{BACKEND_URL}/feed?limit=1"
    )
    await update.message.reply_text(info, parse_mode='Markdown')

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("🔧 ValueEdge Bot - DIAGNOSE MODE")
    print(f"Backend: {BACKEND_URL}")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("bets", bets))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("debug", debug))
    
    print("✅ Diagnose-Bot gestartet")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()