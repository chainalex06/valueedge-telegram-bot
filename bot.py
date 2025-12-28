# bot.py - ValueEdge Bot FÜR ALLE SPORTARTEN
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
            logger.error(f"Backend {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        logger.error(f"Verbindungsfehler: {e}")
        return None

# =====================================================
# TELEGRAM COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ValueEdge Bot - MULTI-SPORT SCANNER*\n\n"
        "🏀 *Basketball:* NBA, Euroleague\n"
        "🏒 *Eishockey:* NHL, Swedish Hockey\n"
        "🎾 *Tennis:* ATP Australian Open\n"
        "⚽ *Fußball:* (Winterpause)\n\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Multi-Sport Scan\n"
        "✅ /bets - Value Bets anzeigen\n"
        "✅ /sports - Alle Sportarten\n"
        "✅ /stats - System Status\n"
        "✅ /analysis - Detaillierte Analyse\n"
        "✅ /sport <name> - Value Bets nach Sportart\n\n"
        "🎯 *Winter-Proof! Keine Winterpause mehr!*",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "🏀🏒🎾 *Multi-Sport Scan startet...*\n"
        "Scanne aktive Sportarten (keine Winterpause!)\n"
        "NBA, NHL, Tennis & mehr...",
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
            sports_text += f"{emoji} {sport}: {count} Bets\n"
        
        await msg.edit_text(
            f"🎉 *MULTI-SPORT SCAN ERFOLGREICH!*\n\n"
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
        sports_list = result.get('results_summary', {}).get('sports_no_bets', [])
        sports_text = "\n".join([f"• {s}" for s in sports_list[:5]])
        
        await msg.edit_text(
            f"✅ *Scan abgeschlossen*\n\n"
            f"🏆 Gescannte Sportarten: {sports_scanned}\n"
            f"🔍 Value Bets: 0\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"*Keine Value Bets heute in:*\n"
            f"{sports_text}\n\n"
            f"💡 Tipp: Probier /analysis für Details",
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
            "🏀🏒🎾 Tippe /scan für Multi-Sport Scan!",
            parse_mode='Markdown'
        )
        return
    
    bets_sorted = sorted(bets_list, key=lambda x: x.get('edge', 0), reverse=True)
    
    message = f"🎯 *Top {len(bets_sorted)} Value Bets:*\n\n"
    
    for i, bet in enumerate(bets_sorted[:15], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get('odds', bet.get('odds_home', 0))
        sport_name = bet.get('sport_name', 'Unbekannt')
        sport_type = bet.get('sport_type', 'unknown')
        
        sport_emoji = get_sport_emoji(sport_name)
        
        if edge > 5:
            edge_emoji = "🔥"
        elif edge > 3:
            edge_emoji = "⚡"
        else:
            edge_emoji = "📈"
        
        message += (
            f"{i}. {sport_emoji} *{match}*\n"
            f"   {edge_emoji} {pick} @ {odds:.2f}\n"
            f"   Edge: +{edge:.1f}%\n"
            f"   🏆 {sport_name} ({sport_type})\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def sports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/sports")
    
    if not result or 'error' in result:
        await update.message.reply_text("❌ Kann Sportarten nicht laden")
        return
    
    sports_list = result.get('sports', [])
    active_sports = [s for s in sports_list if s.get('active')]
    inactive_sports = [s for s in sports_list if not s.get('active')]
    
    message = "🏀🏒🎾 *ALLE SPORTARTEN:*\n\n"
    
    message += f"✅ *AKTIVE SPORTARTEN ({len(active_sports)}):*\n"
    for sport in active_sports:
        emoji = get_sport_emoji(sport['name'])
        message += f"{emoji} {sport['name']} ({sport['sport']})\n"
        message += f"   • Land: {sport['country']}\n"
        message += f"   • Priority: {sport['priority']}\n"
        message += f"   • Outcomes: {', '.join(sport['outcomes'])}\n\n"
    
    if inactive_sports:
        message += f"⏸️ *INAKTIVE SPORTARTEN ({len(inactive_sports)}):*\n"
        for sport in inactive_sports[:5]:  # Nur erste 5 zeigen
            emoji = get_sport_emoji(sport['name'])
            message += f"{emoji} {sport['name']} (Winterpause)\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if not result:
        await update.message.reply_text("❌ Backend nicht erreichbar")
        return
    
    multi_stats = get_backend("/stats/multi")
    
    total_bets = result.get('total_value_bets_in_db', 0)
    active_sports = result.get('active_sports', 0)
    sports_list = result.get('sports_list', [])
    
    sports_text = ""
    if multi_stats and 'top_sports' in multi_stats:
        top_sports = multi_stats['top_sports']
        if top_sports:
            sports_text = f"\n🏆 *Top Sportart:* {top_sports[0].get('sport', 'N/A')} ({top_sports[0].get('count', 0)} Bets)"
    
    message = (
        f"📊 *MULTI-SPORT SCANNER STATUS*\n\n"
        f"• Datenbank: {result.get('database', '❓')}\n"
        f"• Odds API: {result.get('odds_api', '❓')}\n"
        f"• Aktive Sportarten: {active_sports}\n"
        f"• Value Bets in DB: {total_bets}\n"
        f"{sports_text}\n"
        f"• Zeit: {result.get('timestamp', '')[:19]}\n\n"
        f"✅ *Aktive Sportarten:*\n"
    )
    
    for sport in sports_list[:5]:  # Nur erste 5 zeigen
        message += f"  • {sport}\n"
    
    if len(sports_list) > 5:
        message += f"  • ... und {len(sports_list) - 5} weitere\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📊 Analysiere Multi-Sport Daten...")
    
    result = get_backend("/stats/multi")
    
    if not result or 'error' in result:
        await msg.edit_text("❌ Kann Analyse nicht laden")
        return
    
    total_bets = result.get('total_value_bets', 0)
    
    if total_bets == 0:
        await msg.edit_text("📭 Keine Value Bets für Analyse")
        return
    
    avg_edge = result.get('average_edge', 0)
    top_sports = result.get('top_sports', [])
    sport_stats = result.get('sport_statistics', {})
    active_sports = result.get('active_sports_today', [])
    
    message = "📊 *MULTI-SPORT ANALYSE*\n\n"
    message += f"• Gesamt Value Bets: {total_bets}\n"
    message += f"• Durchschnitt Edge: {avg_edge:.1f}%\n"
    message += f"• Aktive Sportarten heute: {len(active_sports)}\n\n"
    
    message += "🏆 *TOP SPORTARTEN NACH VALUE BETS:*\n"
    for sport in top_sports[:3]:
        sport_name = sport.get('sport', 'Unknown')
        count = sport.get('count', 0)
        avg = sport.get('avg_edge', 0)
        sport_type = sport.get('type', 'unknown')
        emoji = get_sport_emoji(sport_name)
        
        message += f"  {emoji} {sport_name} ({sport_type}): {count} Bets (Ø{avg:.1f}%)\n"
    
    # Edge-Verteilung
    high_edges = 0
    medium_edges = 0
    low_edges = 0
    
    for sport, stats in sport_stats.items():
        count = stats.get('count', 0)
        avg_edge = stats.get('avg_edge', 0)
        
        if avg_edge > 5:
            high_edges += 1
        elif avg_edge >= 2:
            medium_edges += 1
        else:
            low_edges += 1
    
    message += f"\n📈 *EDGE-VERTEILUNG (pro Sportart):*\n"
    message += f"  • Hoch (>5%): {high_edges} Sportarten\n"
    message += f"  • Mittel (2-5%): {medium_edges} Sportarten\n"
    message += f"  • Niedrig (<2%): {low_edges} Sportarten\n\n"
    
    # Empfehlung
    if high_edges > 0:
        message += "🔥 *EMPFEHLUNG:* Exzellente Value Bets in mehreren Sportarten!"
    elif medium_edges > 0:
        message += "⚡ *EMPFEHLUNG:* Gute Value Bets verfügbar"
    else:
        message += "💡 *EMPFEHLUNG:* Mehr Sportarten aktivieren"
    
    message += "\n\n🎯 *Aktive Sportarten:* " + ", ".join(active_sports[:5])
    
    await msg.edit_text(message, parse_mode='Markdown')

async def sport_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🏀 *Verwendung:* /sport <Sportart>\n\n"
            "Beispiele:\n"
            "/sport NBA\n"
            "/sport NHL\n"
            "/sport Euroleague\n\n"
            "🏒 Tippe /sports für alle verfügbaren Sportarten",
            parse_mode='Markdown'
        )
        return
    
    sport_name = ' '.join(context.args).upper()
    
    # Hole alle Sportarten zuerst
    sports_result = get_backend("/sports")
    if not sports_result:
        await update.message.reply_text("❌ Kann Sportarten nicht laden")
        return
    
    # Finde passende Sportarten
    matching_sports = []
    for sport in sports_result.get('sports', []):
        if sport_name.lower() in sport.get('name', '').lower():
            matching_sports.append(sport.get('key'))
    
    if not matching_sports:
        await update.message.reply_text(f"❌ Keine Sportart gefunden für '{sport_name}'")
        return
    
    # Value Bets für diese Sportarten holen
    all_bets = []
    for sport_key in matching_sports:
        result = get_backend(f"/feed?sport={sport_key}&limit=20")
        if result and 'bets' in result:
            all_bets.extend(result['bets'])
    
    if not all_bets:
        await update.message.reply_text(
            f"📭 Keine Value Bets für {sport_name}\n\n"
            f"💡 Tippe /scan für neuen Multi-Sport Scan",
            parse_mode='Markdown'
        )
        return
    
    # Nach Edge sortieren
    sorted_bets = sorted(all_bets, key=lambda x: x.get('edge', 0), reverse=True)
    sport_info = next((s for s in sports_result.get('sports', []) if s.get('key') == matching_sports[0]), {})
    
    sport_display_name = sport_info.get('name', sport_name)
    sport_emoji = get_sport_emoji(sport_display_name)
    
    message = f"{sport_emoji} *VALUE BETS FÜR {sport_display_name.upper()}:*\n\n"
    
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
    emoji_map = {
        "NBA": "🏀",
        "Euroleague": "🏀",
        "basketball": "🏀",
        "NHL": "🏒",
        "Swedish Hockey League": "🏒",
        "icehockey": "🏒",
        "ATP Australian Open": "🎾",
        "tennis": "🎾",
        "Premier League": "⚽",
        "Serie A": "⚽",
        "soccer": "⚽"
    }
    
    for key, emoji in emoji_map.items():
        if key.lower() in sport_name.lower():
            return emoji
    
    return "🎯"

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("🤖 ValueEdge Bot - MULTI-SPORT SCANNER")
    print(f"Backend: {BACKEND_URL}")
    print("🏀 Basketball: NBA, Euroleague")
    print("🏒 Eishockey: NHL, Swedish Hockey")
    print("🎾 Tennis: ATP Australian Open")
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