"""
🤖 ValueEdge Telegram Bot
Version: 9.0 (Fixed Edition)
Datum: 30.12.2025
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import aiohttp
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# =====================================================
# LOGGING
# =====================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION
# =====================================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "https://value-bet-backend-production.up.railway.app")

if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN nicht gesetzt!")
    exit(1)

# Sport Emojis
SPORT_EMOJIS = {
    'basketball': '🏀',
    'icehockey': '🏒',
    'tennis': '🎾',
    'americanfootball': '🏈',
    'soccer': '⚽',
    'baseball': '⚾'
}

# =====================================================
# BACKEND API FUNCTIONS
# =====================================================
async def api_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Macht Anfrage an das Backend"""
    
    url = f"{BACKEND_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json"
    }
    
    if BACKEND_API_KEY:
        headers["X-API-Key"] = BACKEND_API_KEY
    
    timeout = aiohttp.ClientTimeout(total=60)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if method == "GET":
                async with session.get(url, headers=headers) as response:
                    text = await response.text()
                    if response.status == 200:
                        return json.loads(text) if text else {}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
            
            elif method == "POST":
                async with session.post(url, headers=headers, json=data) as response:
                    text = await response.text()
                    if response.status == 200:
                        return json.loads(text) if text else {}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}"}
    
    except asyncio.TimeoutError:
        return {"success": False, "error": "Timeout - Backend antwortet nicht"}
    except Exception as e:
        logger.error(f"API Fehler: {e}")
        return {"success": False, "error": str(e)}

# =====================================================
# COMMAND HANDLERS
# =====================================================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start-Befehl"""
    
    message = """
🤖 <b>ValueEdge Bot v9.0</b>
📅 Multi-Sport Value Bet Scanner

✅ <b>Aktive Sportarten:</b>
• 🏀 NBA Basketball
• 🏒 NHL Eishockey
• 🎾 Tennis (ATP/WTA)
• 🏈 NFL Football
• ⚽ Fußball (EPL, Bundesliga)

<b>📋 Befehle:</b>
/scan - Startet Value Bet Scan
/bets - Zeigt gefundene Value Bets
/stats - System-Statistiken
/help - Hilfe anzeigen

<b>⚙️ Einstellungen:</b>
• Min. Edge: 0.2%
• Märkte: H2H, Spreads, Totals
"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 Scan starten", callback_data="scan")],
        [InlineKeyboardButton("📊 Value Bets", callback_data="bets")],
        [InlineKeyboardButton("📈 Statistiken", callback_data="stats")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scan-Befehl"""
    
    # Lade-Nachricht
    loading_msg = await update.message.reply_text(
        "🔄 <b>Starte Multi-Sport Scan...</b>\n\n"
        "🏀 NBA Basketball\n"
        "🏒 NHL Eishockey\n"
        "🎾 Tennis\n"
        "🏈 NFL Football\n"
        "⚽ Fußball\n\n"
        "⏳ Bitte warten (kann bis zu 60 Sekunden dauern)...",
        parse_mode='HTML'
    )
    
    # Synchronen Scan ausführen (wartet auf Ergebnis)
    result = await api_request("/scan/sync", "POST")
    
    if result.get("success"):
        total_bets = result.get("total_bets", 0)
        total_matches = result.get("total_matches", 0)
        duration = result.get("duration_seconds", 0)
        results_by_sport = result.get("results_by_sport", {})
        
        # Ergebnis-Nachricht bauen
        message = f"""
✅ <b>Scan abgeschlossen!</b>

📊 <b>Ergebnis:</b>
• Spiele gescannt: <b>{total_matches}</b>
• Value Bets gefunden: <b>{total_bets}</b>
• Dauer: {duration}s

<b>Details pro Sportart:</b>
"""
        
        for sport_key, data in results_by_sport.items():
            if isinstance(data, dict) and "error" not in data:
                matches = data.get("matches", 0)
                bets = data.get("bets", 0)
                emoji = "🎯" if bets > 0 else "⚪"
                message += f"{emoji} {sport_key}: {bets} Bets ({matches} Spiele)\n"
        
        if total_bets > 0:
            message += f"\n💡 Nutze /bets um die Value Bets anzuzeigen!"
        else:
            message += f"\n⚠️ Keine Value Bets gefunden. Versuche es später erneut."
        
        keyboard = [
            [InlineKeyboardButton("📊 Value Bets anzeigen", callback_data="bets")],
            [InlineKeyboardButton("🔄 Erneut scannen", callback_data="scan")]
        ]
        
        await loading_msg.edit_text(
            message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        error = result.get("error", "Unbekannter Fehler")
        await loading_msg.edit_text(
            f"❌ <b>Scan fehlgeschlagen</b>\n\nFehler: {error}",
            parse_mode='HTML'
        )

async def cmd_bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bets-Befehl"""
    
    # Sport-Filter aus Argumenten
    sport_filter = None
    if context.args:
        sport_map = {
            'basketball': 'basketball',
            'nba': 'basketball',
            'hockey': 'icehockey',
            'nhl': 'icehockey',
            'eishockey': 'icehockey',
            'tennis': 'tennis',
            'nfl': 'americanfootball',
            'football': 'americanfootball',
            'soccer': 'soccer',
            'fussball': 'soccer'
        }
        sport_filter = sport_map.get(context.args[0].lower())
    
    # API-Anfrage
    endpoint = "/feed"
    if sport_filter:
        endpoint = f"/feed?sport={sport_filter}"
    
    result = await api_request(endpoint)
    
    if not result.get("success"):
        await update.message.reply_text(
            f"❌ Fehler: {result.get('error', 'Unbekannt')}"
        )
        return
    
    bets = result.get("bets", [])
    count = result.get("count", 0)
    
    if count == 0:
        message = """
📭 <b>Keine Value Bets gefunden</b>

Mögliche Gründe:
• Noch kein Scan durchgeführt
• Keine Spiele mit genug Edge
• Filter zu streng

💡 Starte einen neuen Scan mit /scan
"""
        keyboard = [[InlineKeyboardButton("🎯 Jetzt scannen", callback_data="scan")]]
        
        await update.message.reply_text(
            message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Bets anzeigen (max 10 pro Nachricht)
    message = f"""
🎯 <b>VALUE BETS</b>
📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}
📊 Gefunden: <b>{count}</b>

"""
    
    for bet in bets[:10]:
        emoji = SPORT_EMOJIS.get(bet.get('sport', ''), '🎯')
        edge = bet.get('edge', 0)
        
        # Confidence
        if edge >= 3.0:
            conf = "🔥"
        elif edge >= 1.5:
            conf = "⚡"
        else:
            conf = "💡"
        
        message += f"{emoji} <b>{bet.get('match', 'N/A')}</b>\n"
        message += f"   🎯 {bet.get('team', 'N/A')}\n"
        message += f"   📊 Odds: <b>{bet.get('odds', 'N/A')}</b> @ {bet.get('bookmaker', 'N/A')}\n"
        message += f"   📈 Edge: <b>{edge:.2f}%</b> {conf}\n"
        message += f"   🕐 {bet.get('match_time_formatted', 'N/A')}\n\n"
    
    if count > 10:
        message += f"<i>... und {count - 10} weitere</i>\n"
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Aktualisieren", callback_data="bets"),
            InlineKeyboardButton("🎯 Neuer Scan", callback_data="scan")
        ],
        [
            InlineKeyboardButton("🏀 NBA", callback_data="filter_basketball"),
            InlineKeyboardButton("🏒 NHL", callback_data="filter_icehockey"),
            InlineKeyboardButton("⚽ Fußball", callback_data="filter_soccer")
        ]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stats-Befehl"""
    
    # Health Check
    health = await api_request("/health")
    
    # Sport Stats
    stats = await api_request("/stats/sports")
    
    message = f"""
📊 <b>SYSTEM STATUS</b>
📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}

<b>🔗 Backend:</b>
"""
    
    if health.get("status") == "healthy":
        message += "• Status: 🟢 Online\n"
        message += f"• Datenbank: {health.get('database', 'N/A')}\n"
        message += f"• Odds API: {health.get('odds_api', 'N/A')}\n"
    else:
        message += "• Status: 🔴 Offline\n"
    
    message += "\n<b>🎯 Sportarten:</b>\n"
    
    if stats.get("success"):
        for sport in stats.get("sports", []):
            if sport.get("active"):
                emoji = sport.get("emoji", "🎯")
                name = sport.get("display_name", "")
                weekly = sport.get("weekly_bets", 0)
                message += f"• {emoji} {name}: {weekly} Bets (7 Tage)\n"
    
    message += f"\n<b>⚙️ Einstellungen:</b>\n"
    message += f"• Min. Edge: 0.2%\n"
    message += f"• Märkte: H2H, Spreads, Totals\n"
    message += f"\n🤖 Bot Version: 9.0"
    
    keyboard = [
        [InlineKeyboardButton("🎯 Scan starten", callback_data="scan")],
        [InlineKeyboardButton("📊 Value Bets", callback_data="bets")]
    ]
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hilfe-Befehl"""
    
    message = """
❓ <b>VALUEEDGE BOT - HILFE</b>

<b>📋 Befehle:</b>
/start - Bot starten
/scan - Multi-Sport Scan starten
/bets - Value Bets anzeigen
/bets nba - Nur NBA Bets
/bets nhl - Nur NHL Bets
/bets soccer - Nur Fußball Bets
/stats - Statistiken
/help - Diese Hilfe

<b>🎯 Was ist ein Value Bet?</b>
Ein Value Bet liegt vor, wenn ein Bookmaker bessere Odds anbietet als der Marktdurchschnitt.

<b>📊 Edge erklärt:</b>
• Edge = Vorteil gegenüber Markt
• 1% Edge = 1% mehr Odds als Durchschnitt
• Je höher der Edge, desto besser

<b>🔥 Confidence Level:</b>
• 💡 LOW = 0.2-1.5% Edge
• ⚡ MEDIUM = 1.5-3% Edge
• 🔥 HIGH = 3%+ Edge

<b>💡 Tipps:</b>
• Scanne regelmäßig (alle 2-4h)
• Setze nicht alles auf einen Bet
• Tracke deine Ergebnisse
"""
    
    await update.message.reply_text(message, parse_mode='HTML')

# =====================================================
# CALLBACK HANDLER
# =====================================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verarbeitet Button-Klicks"""
    
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Erstelle ein Fake-Message-Objekt für die Command-Handler
    class FakeMessage:
        def __init__(self, chat, message_id):
            self.chat = chat
            self.chat_id = chat.id
            self.message_id = message_id
        
        async def reply_text(self, text, **kwargs):
            return await query.message.reply_text(text, **kwargs)
    
    # Fake Update mit dem Message-Objekt
    class FakeUpdate:
        def __init__(self, message):
            self.message = message
    
    fake_message = FakeMessage(query.message.chat, query.message.message_id)
    fake_update = FakeUpdate(fake_message)
    
    if data == "scan":
        await query.message.edit_text("🔄 Starte Scan...", parse_mode='HTML')
        context.args = []
        await cmd_scan(fake_update, context)
    
    elif data == "bets":
        context.args = []
        await cmd_bets(fake_update, context)
    
    elif data == "stats":
        context.args = []
        await cmd_stats(fake_update, context)
    
    elif data.startswith("filter_"):
        sport = data.replace("filter_", "")
        context.args = [sport]
        await cmd_bets(fake_update, context)

# =====================================================
# ERROR HANDLER
# =====================================================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fehler-Handler"""
    logger.error(f"Error: {context.error}")
    
    try:
        if update and update.message:
            await update.message.reply_text(
                f"❌ Ein Fehler ist aufgetreten.\n\nDetails: {str(context.error)[:100]}"
            )
    except Exception:
        pass

# =====================================================
# MAIN
# =====================================================
def main():
    """Startet den Bot"""
    
    logger.info("🤖 Starte ValueEdge Bot v9.0")
    logger.info(f"🔗 Backend: {BACKEND_URL}")
    
    # Bot erstellen
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Command Handler
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("scan", cmd_scan))
    application.add_handler(CommandHandler("bets", cmd_bets))
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("help", cmd_help))
    
    # Callback Handler
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Error Handler
    application.add_error_handler(error_handler)
    
    # Starten
    logger.info("✅ Bot gestartet - warte auf Nachrichten...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
