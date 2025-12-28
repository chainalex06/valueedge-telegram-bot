# bot.py - ValueEdge Bot FÜR MULTI-SPORT MIT NEUER DB
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
# BACKEND FUNKTIONEN
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
            logger.error(f"Backend {response.status_code} für {endpoint}: {response.text[:200]}")
            return {"error": f"Status {response.status_code}", "details": response.text[:200]}
    except requests.exceptions.Timeout:
        logger.error(f"Timeout für {endpoint}")
        return {"error": "Timeout", "details": "Backend antwortet nicht"}
    except Exception as e:
        logger.error(f"Verbindungsfehler für {endpoint}: {e}")
        return {"error": str(e)}

# =====================================================
# TELEGRAM COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ValueEdge Bot - MULTI-SPORT SCANNER*\n"
        "📅 *Datum: 28.12.2025 (Winter)*\n\n"
        "🏀 *Aktive Sportarten heute:*\n"
        "• NBA (Basketball) 🏀\n"
        "• NHL (Eishockey) 🏒\n"
        "• Tennis 🎾\n"
        "• NFL (American Football) 🏈\n\n"
        "⚽ *Fußball:* Winterpause bis Januar\n\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Multi-Sport Scan starten\n"
        "✅ /bets - Value Bets anzeigen\n"
        "✅ /sports - Alle Sportarten\n"
        "✅ /stats - System Status\n"
        "✅ /analysis - Detaillierte Analyse\n"
        "✅ /sport <name> - Value Bets nach Sportart\n\n"
        "🎯 *Winter-Proof! Keine Winterpause!*",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "🏀🏒🎾 *Multi-Sport Scan startet...*\n"
        "📅 Datum: 28.12.2025\n"
        "✅ Scanne aktive Winter-Sportarten\n"
        "⏱️ Dauer: 1-2 Minuten",
        parse_mode='Markdown'
    )
    
    result = get_backend("/scan", timeout=180)
    
    if result is None:
        await msg.edit_text("❌ Backend nicht erreichbar")
        return
    
    if 'error' in result:
        await msg.edit_text(f"❌ Fehler: {result['error']}")
        return
    
    bets = result.get('total_value_bets', 0)
    duration = result.get('duration_seconds', 0)
    sports_scanned = result.get('sports_scanned', 0)
    sports_with_bets = result.get('sports_with_bets', 0)
    bets_by_sport = result.get('bets_by_sport', {})
    
    if bets > 0:
        # Liste der erfolgreichen Sportarten
        sports_text = ""
        for sport, count in bets_by_sport.items():
            emoji = get_sport_emoji(sport)
            sports_text += f"{emoji} {sport}: {count} Value Bets\n"
        
        await msg.edit_text(
            f"🎉 *MULTI-SPORT SCAN ERFOLGREICH!*\n"
            f"📅 Datum: 28.12.2025\n\n"
            f"🏆 Gescannte Sportarten: {sports_scanned}\n"
            f"✅ Value Bets gefunden: {bets}\n"
            f"🎯 Sportarten mit Bets: {sports_with_bets}\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"📊 *Value Bets pro Sportart:*\n"
            f"{sports_text}\n"
            f"Tippe /bets zum Anzeigen! 🚀",
            parse_mode='Markdown'
        )
    else:
        sports_list = result.get('results_summary', {}).get('no_bets_sports', [])
        sports_text = "\n".join([f"• {s}" for s in sports_list[:5]])
        
        await msg.edit_text(
            f"✅ *Scan abgeschlossen*\n"
            f"📅 Datum: 28.12.2025\n\n"
            f"🏆 Gescannte Sportarten: {sports_scanned}\n"
            f"🔍 Value Bets: 0\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"*Keine Value Bets heute in:*\n"
            f"{sports_text}\n\n"
            f"💡 Tippe /analysis für Details",
            parse_mode='Markdown'
        )

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/feed?limit=15&min_edge=1.0")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text(
            "📭 Keine Value Bets in Datenbank.\n"
            "🏀🏒🎾 Tippe /scan für Multi-Sport Scan!\n"
            "📅 Datum: 28.12.2025",
            parse_mode='Markdown'
        )
        return
    
    bets_sorted = sorted(bets_list, key=lambda x: x.get('edge', 0), reverse=True)
    
    message = f"🎯 *Top {len(bets_sorted)} Value Bets:*\n"
    message += "📅 Datum: 28.12.2025\n\n"
    
    for i, bet in enumerate(bets_sorted[:15], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get('odds', 0)
        sport_name = bet.get('sport_name', 'Unbekannt')
        sport_type = bet.get('sport_type', 'unknown')
        emoji = bet.get('emoji', '🎯')
        
        if edge > 5:
            edge_emoji = "🔥"
        elif edge > 3:
            edge_emoji = "⚡"
        else:
            edge_emoji = "📈"
        
        message += (
            f"{i}. {emoji} *{match}*\n"
            f"   {edge_emoji} {pick} @ {odds:.2f}\n"
            f"   Edge: +{edge:.1f}%\n"
            f"   🏆 {sport_name}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def sports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/sports")
    
    if not result or 'error' in result:
        await update.message.reply_text("❌ Kann Sportarten nicht laden")
        return
    
    sports_by_type = result.get('sports_by_type', {})
    active_today = result.get('active_today', [])
    inactive_winter = result.get('inactive_winter', [])
    
    message = "🏀🏒🎾 *SPORTARTEN KONFIGURATION:*\n"
    message += "📅 Datum: 28.12.2025\n\n"
    
    message += "✅ *AKTIVE SPORTARTEN HEUTE:*\n"
    for sport in active_today:
        message += f"• {sport}\n"
    
    message += "\n⏸️ *INAKTIV (WINTERPAUSE):*\n"
    for sport in inactive_winter:
        message += f"• {sport}\n"
    
    message += "\n📊 *KONFIGURIERTE SPORTARTEN:*\n"
    for sport_type, sports_list in sports_by_type.items():
        type_emoji = get_sport_type_emoji(sport_type)
        message += f"\n{type_emoji} *{sport_type.upper()}*:\n"
        
        for sport in sports_list[:3]:  # Nur erste 3 zeigen
            message += f"  • {sport['name']} ({sport['country']})\n"
        
        if len(sports_list) > 3:
            message += f"  • ... und {len(sports_list) - 3} weitere\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if not result:
        await update.message.reply_text("❌ Backend nicht erreichbar")
        return
    
    sports_stats = get_backend("/stats/sports")
    
    total_bets = result.get('total_value_bets', 0)
    active_sports = result.get('active_sports', 0)
    sports_list = result.get('sports', [])
    
    sports_text = ""
    if sports_stats and 'top_sports' in sports_stats:
        top_sports = sports_stats['top_sports']
        if top_sports:
            top_sport = top_sports[0]
            sports_text = f"\n🏆 *Top Sportart:* {top_sport.get('sport', 'N/A')} ({top_sport.get('count', 0)} Bets)"
    
    message = (
        f"📊 *MULTI-SPORT SCANNER STATUS*\n"
        f"📅 Datum: 28.12.2025\n\n"
        f"• Datenbank: {result.get('database', '❓')}\n"
        f"• Odds API: {result.get('odds_api', '❓')}\n"
        f"• Aktive Sportarten: {active_sports}\n"
        f"• Value Bets in DB: {total_bets}\n"
        f"{sports_text}\n"
        f"• Winter-Proof: ✅ Ja\n"
        f"• Zeit: {result.get('timestamp', '')[:19]}\n\n"
        f"✅ *Aktive Sportarten heute:*\n"
    )
    
    for sport in sports_list[:5]:
        message += f"  • {sport}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📊 Analysiere Multi-Sport Daten...")
    
    try:
        # 1. Zuerst Backend-Status prüfen
        health = get_backend("/health")
        if not health or 'error' in health:
            await msg.edit_text("❌ Backend nicht erreichbar")
            return
        
        # 2. Statistiken holen
        result = get_backend("/stats/sports")
        
        if not result:
            await msg.edit_text("❌ Kann Analyse nicht laden: Backend liefert keine Daten")
            return
        
        if 'error' in result:
            error_msg = result.get('error', 'Unbekannter Fehler')
            error_details = result.get('details', '')
            await msg.edit_text(f"❌ Backend-Fehler: {error_msg}\n\nDetails: {error_details[:100]}")
            return
        
        if result.get('status') == 'error':
            await msg.edit_text(f"❌ {result.get('message', 'Unbekannter Fehler')}")
            return
        
        total_bets = result.get('total_value_bets', 0)
        
        if total_bets == 0:
            await msg.edit_text(
                "📭 Keine Value Bets für Analyse\n"
                "📅 Datum: 28.12.2025\n"
                "💡 Tippe /scan für neuen Scan!",
                parse_mode='Markdown'
            )
            return
        
        avg_edge = result.get('average_edge', 0)
        top_sports = result.get('top_sports', [])
        edge_dist = result.get('edge_distribution', {})
        
        message = "📊 *MULTI-SPORT ANALYSE*\n"
        message += "📅 Datum: 28.12.2025\n\n"
        message += f"• Gesamt Value Bets: {total_bets}\n"
        message += f"• Durchschnitt Edge: {avg_edge:.1f}%\n"
        message += f"• Winter-Proof: ✅ Ja\n\n"
        
        message += "🏆 *TOP SPORTARTEN NACH VALUE BETS:*\n"
        for sport in top_sports[:3]:
            sport_name = sport.get('sport', 'Unknown')
            count = sport.get('count', 0)
            avg = sport.get('avg_edge', 0)
            sport_type = sport.get('type', 'unknown')
            emoji = get_sport_type_emoji(sport_type)
            
            message += f"  {emoji} {sport_name}: {count} Bets (Ø{avg:.1f}%)\n"
        
        # Edge-Verteilung
        high_edges = edge_dist.get('high_edges', 0)
        medium_edges = edge_dist.get('medium_edges', 0)
        low_edges = edge_dist.get('low_edges', 0)
        
        message += f"\n📈 *EDGE-VERTEILUNG:*\n"
        message += f"  • Hoch (>5%): {high_edges} Bets\n"
        message += f"  • Mittel (2-5%): {medium_edges} Bets\n"
        message += f"  • Niedrig (<2%): {low_edges} Bets\n\n"
        
        # Empfehlung basierend auf Datum
        today = datetime.now()
        if today.month in [12, 1]:  # Winter
            message += "❄️ *WINTER-EMPFEHLUNG:*\n"
            message += "  • Fokussier auf NBA 🏀\n"
            message += "  • NHL hat gute Value 🏒\n"
            message += "  • Tennis indoor 🎾\n"
            message += "  • Fußball erst ab Januar ⚽\n"
        else:
            message += "🌞 *EMPFEHLUNG:* Alle Sportarten aktiv\n"
        
        await msg.edit_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Analysis Fehler: {e}")
        await msg.edit_text(f"❌ Unerwarteter Fehler: {str(e)[:100]}")
        return

async def sport_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🏀 *Verwendung:* /sport <Sportart>\n\n"
            "Beispiele:\n"
            "/sport NBA\n"
            "/sport NHL\n"
            "/sport tennis\n\n"
            "📅 Heute aktiv: NBA, NHL, Tennis",
            parse_mode='Markdown'
        )
        return
    
    sport_name = ' '.join(context.args).upper()
    
    # Value Bets filtern
    result = get_backend("/feed?limit=100&min_edge=1.0")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text("📭 Datenbank ist leer")
        return
    
    # Nach Sportart filtern
    sport_bets = []
    for bet in bets_list:
        bet_sport = bet.get('sport_name', '').upper()
        bet_type = bet.get('sport_type', '').upper()
        
        if sport_name in bet_sport or sport_name in bet_type:
            sport_bets.append(bet)
    
    if not sport_bets:
        await update.message.reply_text(
            f"📭 Keine Value Bets für '{sport_name}'\n\n"
            f"📅 Datum: 28.12.2025\n"
            f"💡 Heute aktiv: NBA, NHL, Tennis",
            parse_mode='Markdown'
        )
        return
    
    sorted_bets = sorted(sport_bets, key=lambda x: x.get('edge', 0), reverse=True)
    sport_emoji = get_sport_emoji(sport_name)
    
    message = f"{sport_emoji} *VALUE BETS FÜR {sport_name.upper()}*\n"
    message += "📅 Datum: 28.12.2025\n\n"
    
    for i, bet in enumerate(sorted_bets[:10], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get('odds', 0)
        
        message += (
            f"{i}. *{match}*\n"
            f"   ⚡ {pick} @ {odds:.2f}\n"
            f"   📈 Edge: +{edge:.1f}%\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

# =====================================================
# HELPER FUNKTIONEN
# =====================================================
def get_sport_emoji(sport_name):
    sport_name = sport_name.lower()
    
    if any(x in sport_name for x in ['nba', 'basketball', 'euroleague']):
        return "🏀"
    elif any(x in sport_name for x in ['nhl', 'hockey', 'eishockey', 'shl']):
        return "🏒"
    elif any(x in sport_name for x in ['tennis', 'atp', 'wta']):
        return "🎾"
    elif any(x in sport_name for x in ['football', 'nfl', 'american']):
        return "🏈"
    elif any(x in sport_name for x in ['soccer', 'fußball', 'premier', 'bundesliga']):
        return "⚽"
    else:
        return "🎯"

def get_sport_type_emoji(sport_type):
    sport_type = sport_type.lower()
    
    if sport_type == "basketball":
        return "🏀"
    elif sport_type == "icehockey":
        return "🏒"
    elif sport_type == "tennis":
        return "🎾"
    elif sport_type == "americanfootball":
        return "🏈"
    elif sport_type == "soccer":
        return "⚽"
    else:
        return "🎯"

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("🤖 ValueEdge Bot - MULTI-SPORT SCANNER")
    print(f"Backend: {BACKEND_URL}")
    print("📅 Datum: 28.12.2025")
    print("🏀 Aktive Sportarten: NBA, NHL, Tennis")
    print("✅ Winter-Proof! Keine Winterpause!")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands registrieren
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("bets", bets))
    app.add_handler(CommandHandler("sports", sports))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("analysis", analysis))
    app.add_handler(CommandHandler("sport", sport_cmd))
    
    print("✅ Bot gestartet mit Multi-Sport Support")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()