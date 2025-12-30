"""
🤖 ValueEdge Telegram Bot - Multi-Sport Scanner
Version: 8.0 (Winter-Proof Edition)
Datum: 29.12.2025
Autor: ValueEdge Team
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import aiohttp
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

# Konfiguration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Umgebungsvariablen
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")
BACKEND_URL = os.getenv("BACKEND_URL", "https://value-bet-backend-production.up.railway.app")

# Konfiguration prüfen
if not TELEGRAM_BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN nicht gesetzt!")
    exit(1)

if not BACKEND_API_KEY:
    logger.warning("⚠️  BACKEND_API_KEY nicht gesetzt - einige Funktionen könnten eingeschränkt sein")

# Sport-Emoji Mapping
SPORT_EMOJIS = {
    'basketball': '🏀',
    'icehockey': '🏒',
    'tennis': '🎾',
    'americanfootball': '🏈',
    'football': '⚽'
}

# Winter-Sportarten (aktiv)
WINTER_SPORTS = {
    'basketball': 'NBA Basketball',
    'icehockey': 'NHL Eishockey',
    'tennis': 'Tennis',
    'americanfootball': 'NFL Football'
}

async def make_backend_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Macht eine Anfrage an das Backend"""
    url = f"{BACKEND_URL}{endpoint}"
    
    headers = {
        "X-API-Key": BACKEND_API_KEY,
        "Content-Type": "application/json"
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if method == "GET":
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    try:
                        return json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError:
                        logger.error(f"JSON Decode Error: {response_text}")
                        return {"success": False, "error": "Invalid JSON response"}
            
            elif method == "POST":
                async with session.post(url, headers=headers, json=data) as response:
                    response_text = await response.text()
                    try:
                        return json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError:
                        logger.error(f"JSON Decode Error: {response_text}")
                        return {"success": False, "error": "Invalid JSON response"}
    
    except asyncio.TimeoutError:
        logger.error(f"Timeout bei Anfrage an {url}")
        return {"success": False, "error": "Timeout bei Verbindung zum Backend"}
    
    except Exception as e:
        logger.error(f"Fehler bei Backend-Anfrage: {str(e)}")
        return {"success": False, "error": str(e)}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start-Befehl"""
    sport_lines = "\n".join([f"  • {SPORT_EMOJIS.get(sport, '🎯')} {name}" for sport, name in WINTER_SPORTS.items()])
    
    welcome_message = f"""
🤖 <b>ValueEdge Bot - MULTI-SPORT SCANNER</b>
📅 Datum: 29.12.2025 (Winter Edition)

🎯 <b>Winter-Proof Scanner</b> - Keine Winterpause!
    
✅ Aktive Winter-Sportarten:
{sport_lines}

<b>🔧 Verfügbare Befehle:</b>

/scan - Startet Multi-Sport Scan (alle Winter-Sportarten)
/bets - Zeigt aktuelle Value Bets
/analysis - Detaillierte Analyse aller Sportarten
/sport <name> - Filter nach Sportart (z.B. /sport basketball)
/stats - System-Statistiken
/help - Zeigt diese Hilfe an

<b>⚙️ Filter-Einstellungen:</b>
• Basketball: 0.5% Edge
• Eishockey: 0.4% Edge  
• Tennis: 0.6% Edge
• NFL: 0.5% Edge

<code>🔗 Backend: {BACKEND_URL}</code>
"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 Scan starten", callback_data="scan")],
        [InlineKeyboardButton("📊 Value Bets anzeigen", callback_data="bets")],
        [InlineKeyboardButton("📈 Analyse", callback_data="analysis")],
        [InlineKeyboardButton("ℹ️  Hilfe", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Startet Multi-Sport Scan"""
    await update.message.reply_text("🔄 Starte Multi-Sport Scan...")
    
    # Loading Message
    loading_msg = await update.message.reply_text(
        "🔍 Scanne Winter-Sportarten...\n"
        "🏀 NBA Basketball\n"
        "🏒 NHL Eishockey\n" 
        "🎾 Tennis\n"
        "🏈 NFL Football\n\n"
        "⏳ Bitte warten..."
    )
    
    try:
        # Scan starten
        result = await make_backend_request("/scan", "POST")
        
        if result.get("success"):
            sport_lines = "\n".join([f"{SPORT_EMOJIS.get(sport, '🎯')} {name}" for sport, name in WINTER_SPORTS.items()])
            
            response_text = (
                f"✅ <b>Multi-Sport Scan gestartet!</b>\n\n"
                f"📅 Gestartet: {datetime.now().strftime('%H:%M:%S')}\n"
                f"🎯 Scannt alle Winter-Sportarten:\n"
                f"{sport_lines}\n\n"
                f"ℹ️  Der Scan läuft im Hintergrund. Verwende /bets um die Ergebnisse zu sehen."
            )
            
            await loading_msg.edit_text(
                response_text,
                parse_mode='HTML'
            )
        else:
            await loading_msg.edit_text(
                f"❌ <b>Fehler beim Starten des Scans:</b>\n{result.get('error', 'Unbekannter Fehler')}",
                parse_mode='HTML'
            )
    
    except Exception as e:
        logger.error(f"Fehler in scan_command: {str(e)}")
        await loading_msg.edit_text(
            f"❌ <b>Fehler:</b>\n{str(e)}",
            parse_mode='HTML'
        )

async def bets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeigt Value Bets an"""
    try:
        # Parameter parsen
        sport_filter = None
        if context.args:
            sport_arg = context.args[0].lower()
            sport_map = {
                'basketball': 'basketball',
                'nba': 'basketball',
                '🏀': 'basketball',
                'icehockey': 'icehockey',
                'hockey': 'icehockey',
                'nhl': 'icehockey',
                '🏒': 'icehockey',
                'tennis': 'tennis',
                '🎾': 'tennis',
                'football': 'americanfootball',
                'nfl': 'americanfootball',
                '🏈': 'americanfootball'
            }
            sport_filter = sport_map.get(sport_arg)
        
        # Lade Bets
        await update.message.reply_text("📊 Lade Value Bets...")
        
        endpoint = "/feed"
        if sport_filter:
            endpoint = f"/feed?sport={sport_filter}"
        
        result = await make_backend_request(endpoint)
        
        if not result.get("success"):
            await update.message.reply_text(
                f"❌ Fehler beim Laden der Bets: {result.get('error', 'Unbekannter Fehler')}"
            )
            return
        
        bets = result.get("bets", [])
        count = result.get("count", 0)
        
        if count == 0:
            # Keine Bets gefunden
            sport_info = sport_filter if sport_filter else 'Alle'
            no_bets_message = f"""
📭 <b>Keine Value Bets gefunden</b>

Sport: {sport_info}
Zeitraum: Letzte 24 Stunden

💡 <b>Mögliche Lösungen:</b>
1. Starte einen neuen Scan mit /scan
2. Überprüfe die Filter-Einstellungen
3. Warte auf neue Matches

🔧 Aktuelle Filter:
• Min. Edge: 0.3-0.6% (realistisch)
• Nur aktive Winter-Sportarten

<code>🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}</code>
"""
            await update.message.reply_text(no_bets_message, parse_mode='HTML')
            return
        
        # Bets in Gruppen aufteilen (max. 10 pro Nachricht)
        for i in range(0, len(bets), 10):
            batch = bets[i:i+10]
            
            message = f"🎯 <b>Value Edge Scanner</b>\n"
            message += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            message += f"📊 Gefunden: {count} Value Bets\n\n"
            
            if sport_filter:
                emoji = SPORT_EMOJIS.get(sport_filter, '🎯')
                message += f"🎮 Sport: {emoji} {sport_filter.capitalize()}\n\n"
            
            for bet in batch:
                sport = bet.get('sport', '')
                emoji = SPORT_EMOJIS.get(sport, '🎯')
                edge = float(bet.get('edge', 0))
                
                # Confidence Level
                if edge >= 2.0:
                    confidence = "🔥"
                elif edge >= 1.0:
                    confidence = "⚡"
                else:
                    confidence = "💡"
                
                message += f"{emoji} <b>{bet.get('match', 'N/A')}</b>\n"
                message += f"   🎯 <code>{bet.get('team', 'N/A')}</code>\n"
                message += f"   📊 Odds: <b>{bet.get('odds', 'N/A')}</b>\n"
                message += f"   📈 Edge: <b>{edge:.2f}%</b> {confidence}\n"
                message += f"   🏦 {bet.get('bookmaker', 'N/A')}\n"
                message += f"   🕐 {bet.get('match_time_formatted', 'N/A')}\n"
                message += f"   📅 Gefunden: {bet.get('created_at_formatted', 'N/A')}\n\n"
            
            # Filter-Info
            min_edge = result.get('filters', {}).get('min_edge', 0.3)
            message += f"🔧 <i>Filter: Min. Edge {min_edge}%</i>\n"
            message += f"<code>ID: VB{datetime.now().strftime('%Y%m%d')}</code>"
            
            # Inline Buttons für diese Batch
            if i == 0:
                keyboard = [
                    [
                        InlineKeyboardButton("🔄 Aktualisieren", callback_data="refresh_bets"),
                        InlineKeyboardButton("🎯 Neuer Scan", callback_data="scan")
                    ],
                    [
                        InlineKeyboardButton("🏀 NBA", callback_data="sport_basketball"),
                        InlineKeyboardButton("🏒 NHL", callback_data="sport_icehockey"),
                        InlineKeyboardButton("🎾 Tennis", callback_data="sport_tennis")
                    ],
                    [
                        InlineKeyboardButton("📈 Analyse", callback_data="analysis"),
                        InlineKeyboardButton("ℹ️  Hilfe", callback_data="help")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                reply_markup = None
            
            await update.message.reply_text(
                message,
                parse_mode='HTML',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
    
    except Exception as e:
        logger.error(f"Fehler in bets_command: {str(e)}")
        await update.message.reply_text(
            f"❌ Fehler beim Laden der Bets: {str(e)}"
        )

async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeigt detaillierte Analyse aller Sportarten"""
    await update.message.reply_text("📈 Lade Analyse...")
    
    try:
        result = await make_backend_request("/stats/sports")
        
        if not result.get("success"):
            await update.message.reply_text(
                f"❌ Fehler bei der Analyse: {result.get('error', 'Unbekannter Fehler')}"
            )
            return
        
        sports = result.get("sports", [])
        total_bets = result.get("total_weekly_bets", 0)
        
        message = f"""
📊 <b>VALUE EDGE MULTI-SPORT ANALYSE</b>
📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}
🎯 Winter-Proof Edition

<b>📈 WÖCHENTLICHE STATISTIK:</b>
Gesamte Value Bets: <b>{total_bets}</b>
Aktive Sportarten: <b>{len([s for s in sports if s.get('active')])}</b>

<b>🏆 SPORTARTEN-ÜBERSICHT:</b>
"""
        
        for sport in sports:
            name = sport.get('sport', '')
            emoji = sport.get('emoji', '🎯')
            active = sport.get('active', False)
            weekly = sport.get('weekly_bets', 0)
            edge = sport.get('min_edge', 0)
            status = sport.get('status', '')
            
            if active:
                message += f"\n{emoji} <b>{name}</b>"
                message += f"\n   📊 Bets diese Woche: <b>{weekly}</b>"
                message += f"\n   🎯 Min. Edge: <b>{edge}%</b>"
                message += f"\n   ✅ Status: <code>{status}</code>"
            else:
                message += f"\n⏸️  {name}"
                message += f"\n   🏖️  Winterpause"
        
        message += f"\n\n<b>📊 SYSTEM STATUS:</b>"
        
        # Backend Health check
        health_result = await make_backend_request("/health")
        if health_result.get("status") == "healthy":
            message += "\n🟢 Backend: <code>AKTIV</code>"
        else:
            message += "\n🔴 Backend: <code>FEHLER</code>"
        
        message += f"\n🤖 Bot: <code>AKTIV</code>"
        message += f"\n🎯 Version: <code>8.0 Winter-Proof</code>"
        
        message += f"\n\n<b>💡 EMPFEHLUNGEN:</b>"
        
        if total_bets == 0:
            message += "\n• Starte einen Scan mit /scan"
            message += "\n• Überprüfe die Filter-Einstellungen"
            message += "\n• Aktiviere mehr Sportarten"
        elif total_bets < 5:
            message += "\n• Gute Basis, scanne regelmäßig"
            message += "\n• Überprüfe NFL & Tennis"
            message += "\n• Edge-Filter anpassen"
        else:
            message += "\n• Exzellente Ergebnisse!"
            message += "\n• Regelmäßige Scans empfohlen"
            message += "\n• Ergebnisse verfolgen"
        
        message += f"\n\n<code>🔗 {BACKEND_URL}</code>"
        
        keyboard = [
            [InlineKeyboardButton("🎯 Scan starten", callback_data="scan")],
            [InlineKeyboardButton("📊 Value Bets", callback_data="bets")],
            [InlineKeyboardButton("🔄 Aktualisieren", callback_data="refresh_analysis")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='HTML',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    
    except Exception as e:
        logger.error(f"Fehler in analysis_command: {str(e)}")
        await update.message.reply_text(
            f"❌ Fehler bei der Analyse: {str(e)}"
        )

async def sport_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Filter nach Sportart"""
    if not context.args:
        help_text = (
            "ℹ️  Verwendung: /sport <sport>\n\n"
            "Verfügbare Sportarten:\n"
            "• basketball / nba / 🏀\n"
            "• icehockey / nhl / 🏒\n"
            "• tennis / 🎾\n"
            "• americanfootball / nfl / 🏈\n\n"
            "Beispiel: /sport basketball"
        )
        await update.message.reply_text(help_text)
        return
    
    sport_arg = context.args[0].lower()
    await bets_command(update, context)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """System-Statistiken"""
    try:
        # Backend Health
        health = await make_backend_request("/health")
        
        # Sport Stats
        stats = await make_backend_request("/stats/sports")
        
        message = f"""
📊 <b>SYSTEM STATISTIKEN</b>
📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}

<b>🤖 BOT STATUS:</b>
• Version: 8.0 Winter-Proof
• Laufzeit: Verfügbar
• Letzter Ping: {datetime.now().strftime('%H:%M:%S')}

<b>🔗 BACKEND STATUS:</b>
"""
        
        if health.get("status") == "healthy":
            message += f"• Status: 🟢 <code>AKTIV</code>\n"
            message += f"• Datenbank: {health.get('database', 'N/A')}\n"
            message += f"• Odds API: {health.get('odds_api', 'N/A')}\n"
            message += f"• Sportarten: {len(health.get('winter_sports', []))}\n"
        else:
            message += f"• Status: 🔴 <code>FEHLER</code>\n"
        
        message += f"\n<b>🎯 WERTE DIESE WOCHE:</b>\n"
        
        if stats.get("success"):
            sports = stats.get("sports", [])
            for sport in sports:
                if sport.get("active"):
                    name = sport.get("sport", "")
                    weekly = sport.get("weekly_bets", 0)
                    emoji = sport.get("emoji", "🎯")
                    message += f"• {emoji} {name}: {weekly} Bets\n"
        
        message += f"\n<b>🔧 UMWELTVARIABLEN:</b>\n"
        message += f"• Backend URL: <code>{BACKEND_URL}</code>\n"
        message += f"• API Key: {'✅ Gesetzt' if BACKEND_API_KEY else '❌ Fehlt'}\n"
        message += f"• Bot Token: ✅ Gesetzt\n"
        
        message += f"\n<code>Winter-Proof Edition 2025</code>"
        
        keyboard = [
            [InlineKeyboardButton("📈 Analyse", callback_data="analysis")],
            [InlineKeyboardButton("🔄 Health Check", callback_data="health_check")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    except Exception as e:
        logger.error(f"Fehler in stats_command: {str(e)}")
        await update.message.reply_text(
            f"❌ Fehler bei Statistiken: {str(e)}"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hilfe-Befehl"""
    help_message = f"""
❓ <b>VALUE EDGE BOT - HILFE</b>
Version 8.0 (Winter-Proof Edition)

<b>🎯 BEFEHLE:</b>

/start - Startet den Bot
/scan - Startet Multi-Sport Scan
/bets - Zeigt Value Bets an
/bets <sport> - Filter nach Sportart
/analysis - Detaillierte Analyse
/sport <name> - Filter nach Sportart
/stats - System-Statistiken
/help - Diese Hilfe

<b>🏆 AKTIVE SPORTARTEN (WINTER):</b>
• 🏀 NBA Basketball (min. 0.5% Edge)
• 🏒 NHL Eishockey (min. 0.4% Edge)
• 🎾 Tennis (min. 0.6% Edge)
• 🏈 NFL Football (min. 0.5% Edge)

<b>💡 TIPPS:</b>
• Scanne regelmäßig (alle 2-4 Stunden)
• Überprüfe verschiedene Sportarten
• Realistische Edge-Erwartungen (0.3-0.6%)
• Winter-Sportarten sind aktiver

<b>🔧 TECHNISCHE INFO:</b>
• Backend: {BACKEND_URL}
• Hosting: Render/Railway
• Datenbank: Supabase
• API: The Odds API

<b>⚠️  BEKANNTE PROBLEME:</b>
• "Kann Analyse nicht laden" → Backend neu starten
• "0 Value Bets" → Edge-Filter senken
• Duplikate → Automatisch gefiltert

<code>📅 Letztes Update: 29.12.2025</code>
"""
    
    keyboard = [
        [InlineKeyboardButton("🎯 Jetzt scannen", callback_data="scan")],
        [InlineKeyboardButton("📊 Bets anzeigen", callback_data="bets")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_message,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handhabt Callback-Queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "scan":
        # Simuliere /scan command
        context.args = []
        await scan_command(update, context)
    
    elif data == "bets":
        # Simuliere /bets command
        context.args = []
        await bets_command(update, context)
    
    elif data == "analysis":
        # Simuliere /analysis command
        context.args = []
        await analysis_command(update, context)
    
    elif data == "help":
        # Simuliere /help command
        context.args = []
        await help_command(update, context)
    
    elif data == "refresh_bets":
        # Aktualisiere Bets
        await query.edit_message_text("🔄 Aktualisiere Value Bets...")
        context.args = []
        await bets_command(update, context)
    
    elif data == "refresh_analysis":
        # Aktualisiere Analyse
        await query.edit_message_text("🔄 Aktualisiere Analyse...")
        context.args = []
        await analysis_command(update, context)
    
    elif data.startswith("sport_"):
        # Sport Filter
        sport = data.split("_")[1]
        sport_names = {
            "basketball": "basketball",
            "icehockey": "icehockey",
            "tennis": "tennis",
            "americanfootball": "americanfootball"
        }
        
        if sport in sport_names:
            context.args = [sport_names[sport]]
            await query.edit_message_text(f"🔍 Filtere nach {sport}...")
            await bets_command(update, context)
    
    elif data == "health_check":
        # Health Check
        try:
            health = await make_backend_request("/health")
            
            if health.get("status") == "healthy":
                status_text = "🟢 BACKEND AKTIV"
            else:
                status_text = "🔴 BACKEND FEHLER"
            
            await query.edit_message_text(
                f"🏥 <b>HEALTH CHECK</b>\n\n"
                f"Status: {status_text}\n"
                f"Zeit: {datetime.now().strftime('%H:%M:%S')}\n"
                f"Version: {health.get('version', 'N/A')}\n"
                f"Datenbank: {health.get('database', 'N/A')}\n"
                f"Winter-Sportarten: {len(health.get('winter_sports', []))}\n\n"
                f"<code>✅ Systemprüfung abgeschlossen</code>",
                parse_mode='HTML'
            )
        
        except Exception as e:
            await query.edit_message_text(
                f"❌ Health Check fehlgeschlagen: {str(e)}"
            )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handhabt Fehler"""
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        await update.message.reply_text(
            "❌ Ein Fehler ist aufgetreten. Bitte versuche es später erneut.\n"
            f"Fehler: {str(context.error)[:100]}"
        )
    except:
        pass

def main():
    """Startet den Bot"""
    # Bot Application erstellen
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Command Handler
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("bets", bets_command))
    application.add_handler(CommandHandler("analysis", analysis_command))
    application.add_handler(CommandHandler("sport", sport_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callback Query Handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Error Handler
    application.add_error_handler(error_handler)
    
    # Starte Bot
    logger.info("🤖 ValueEdge Bot gestartet (Winter-Proof Edition)")
    logger.info(f"🎯 Aktive Sportarten: {list(WINTER_SPORTS.keys())}")
    logger.info(f"🔗 Backend: {BACKEND_URL}")
    
    # Polling starten
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()