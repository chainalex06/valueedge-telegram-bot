# bot.py - ValueEdge MULTI-SPORT TELEGRAM BOT (VOLLSTÄNDIG)
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
logger = logging.getLogger("ValueEdgeBot")

# =====================================================
# BACKEND REQUEST WRAPPER (VERBESSERT)
# =====================================================
def get_backend(endpoint: str, timeout: int = 30):
    """Sichere Backend-Abfrage mit Fehlerbehandlung"""
    url = f"{BACKEND_URL}{endpoint}"
    headers = {
        "X-API-Key": BACKEND_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                return {"error": True, "message": data.get("error", "Unbekannter Fehler")}
            return data
        else:
            return {
                "error": True,
                "message": f"Status {response.status_code}",
                "details": response.text[:200]
            }
    except requests.exceptions.Timeout:
        return {"error": True, "message": "Timeout - Backend antwortet nicht"}
    except requests.exceptions.ConnectionError:
        return {"error": True, "message": "Verbindungsfehler - Backend nicht erreichbar"}
    except Exception as e:
        return {"error": True, "message": f"Unerwarteter Fehler: {str(e)}"}

# =====================================================
# EMOJI HELPER (MIT None-CHECK)
# =====================================================
def get_sport_emoji(name: str):
    """Gibt das passende Emoji für den Sportnamen zurück"""
    if not name:
        return "🎯"
    
    name_lower = str(name).lower()
    
    if any(x in name_lower for x in ['nba', 'basketball', 'euroleague']):
        return "🏀"
    elif any(x in name_lower for x in ['nhl', 'hockey', 'eishockey', 'shl']):
        return "🏒"
    elif any(x in name_lower for x in ['tennis', 'atp', 'wta']):
        return "🎾"
    elif any(x in name_lower for x in ['football', 'nfl', 'american']):
        return "🏈"
    elif any(x in name_lower for x in ['soccer', 'fußball', 'premier', 'bundesliga']):
        return "⚽"
    else:
        return "🎯"

def get_sport_type_emoji(sport_type: str):
    """Gibt das passende Emoji für den Sporttyp zurück"""
    if not sport_type:
        return "🎯"
    
    sport_type_lower = str(sport_type).lower()
    
    emoji_map = {
        "basketball": "🏀",
        "icehockey": "🏒",
        "tennis": "🎾",
        "americanfootball": "🏈",
        "soccer": "⚽",
        "baseball": "⚾",
        "rugby": "🏉"
    }
    
    return emoji_map.get(sport_type_lower, "🎯")

# =====================================================
# TELEGRAM COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ValueEdge Bot – Multi-Sport Scanner*\n"
        "📅 Datum: 28.12.2025 (Winter)\n\n"
        "🏀 *Aktive Sportarten heute:*\n"
        "• NBA (Basketball) 🏀\n"
        "• NHL (Eishockey) 🏒\n"
        "• Tennis 🎾\n"
        "• NFL (American Football) 🏈\n\n"
        "⚽ *Fußball:* Winterpause bis Januar\n\n"
        "📌 *Kommandos:*\n"
        "• /start – Diese Hilfe\n"
        "• /scan – Multi-Sport Scan starten\n"
        "• /bets – Aktuelle Value Bets\n"
        "• /sports – Verfügbare Sportarten\n"
        "• /stats – System Status\n"
        "• /analysis – Detaillierte Analyse\n"
        "• /sport <name> – Bets nach Sportart filtern\n\n"
        "🎯 *Winter-Proof! Keine Winterpause!*",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "🏀🏒🎾 *Multi-Sport Scan startet...*\n"
        "📅 Datum: 28.12.2025\n"
        "⏱️ Dauer: ca. 1-2 Minuten",
        parse_mode='Markdown'
    )
    
    result = get_backend("/scan", timeout=180)
    
    if result.get("error"):
        await msg.edit_text(f"❌ Fehler beim Scan: {result.get('message', 'Unbekannter Fehler')}")
        return
    
    bets = result.get('total_value_bets', 0)
    duration = result.get('duration_seconds', 0)
    sports_scanned = result.get('sports_scanned', 0)
    
    if bets > 0:
        bets_by_sport = result.get('bets_by_sport', {})
        sports_text = ""
        
        for sport, count in bets_by_sport.items():
            emoji = get_sport_emoji(sport)
            sports_text += f"{emoji} {sport}: {count} Bets\n"
        
        await msg.edit_text(
            f"🎉 *SCAN ERFOLGREICH!*\n"
            f"📅 Datum: 28.12.2025\n\n"
            f"🏆 Sportarten: {sports_scanned}\n"
            f"✅ Value Bets: {bets}\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"📊 *Bets pro Sportart:*\n"
            f"{sports_text}\n"
            f"➡️ /bets zum Anzeigen",
            parse_mode='Markdown'
        )
    else:
        await msg.edit_text(
            f"✅ *Scan abgeschlossen*\n"
            f"📅 Datum: 28.12.2025\n\n"
            f"🏆 Gescannte Sportarten: {sports_scanned}\n"
            f"🔍 Value Bets gefunden: 0\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"💡 Tippe /analysis für Details",
            parse_mode='Markdown'
        )

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/feed?limit=15&min_edge=1.0")
    
    if result.get("error") or not result.get("bets"):
        await update.message.reply_text(
            "📭 *Keine Value Bets verfügbar*\n\n"
            "🏀🏒🎾 Tippe /scan für neuen Multi-Sport Scan!\n"
            "📅 Datum: 28.12.2025",
            parse_mode='Markdown'
        )
        return
    
    bets_list = result["bets"]
    bets_sorted = sorted(bets_list, key=lambda x: x.get('edge', 0), reverse=True)
    
    message = "🎯 *Top Value Bets*\n"
    message += "📅 Datum: 28.12.2025\n\n"
    
    for i, bet in enumerate(bets_sorted[:15], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get('odds', 0)
        sport_name = bet.get('sport_name', 'Unbekannt')
        emoji = bet.get('emoji', '🎯')
        
        # Edge Emoji
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
    
    if result.get("error"):
        await update.message.reply_text("❌ Kann Sportarten nicht laden")
        return
    
    message = "🏀🏒🎾 *SPORTARTEN KONFIGURATION*\n"
    message += "📅 Datum: 28.12.2025\n\n"
    
    message += "✅ *AKTIVE SPORTARTEN HEUTE:*\n"
    message += "• NBA (Basketball) 🏀\n"
    message += "• NHL (Eishockey) 🏒\n"
    message += "• Tennis 🎾\n"
    message += "• NFL (American Football) 🏈\n\n"
    
    message += "⏸️ *INAKTIV (WINTERPAUSE):*\n"
    message += "• Fußball ⚽ (bis Januar)\n\n"
    
    sports_by_type = result.get("sports_by_type", {})
    
    if sports_by_type:
        message += "📊 *KONFIGURIERTE SPORTARTEN:*\n"
        for sport_type, sports_list in sports_by_type.items():
            type_emoji = get_sport_type_emoji(sport_type)
            message += f"\n{type_emoji} *{sport_type.upper()}*:\n"
            
            for sport in sports_list[:3]:
                message += f"  • {sport['name']} ({sport['country']})\n"
            
            if len(sports_list) > 3:
                message += f"  • ... und {len(sports_list) - 3} weitere\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if result.get("error"):
        await update.message.reply_text("❌ Backend nicht erreichbar")
        return
    
    message = (
        f"📊 *SYSTEM STATUS*\n"
        f"📅 Datum: 28.12.2025\n\n"
        f"• Datenbank: {result.get('database', '❓')}\n"
        f"• Odds API: {result.get('odds_api', '❓')}\n"
        f"• Aktive Sportarten: {result.get('active_sports', 0)}\n"
        f"• Value Bets in DB: {result.get('total_value_bets', 0)}\n"
        f"• Winter-Proof: ✅ Ja\n"
        f"• Zeit: {result.get('timestamp', '')[:19]}\n\n"
    )
    
    sports_list = result.get('sports', [])
    if sports_list:
        message += "✅ *Aktive Sportarten:*\n"
        for sport in sports_list[:5]:
            message += f"  • {sport}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📊 Analysiere Multi-Sport Daten...")
    
    result = get_backend("/stats/sports", timeout=45)
    
    if result.get("error"):
        await msg.edit_text(f"❌ Kann Analyse nicht laden: {result.get('message', 'Unbekannter Fehler')}")
        return
    
    total_bets = result.get('total_value_bets', 0)
    
    if total_bets == 0:
        await msg.edit_text(
            "📭 *Keine Value Bets für Analyse*\n\n"
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
    
    if top_sports:
        message += "🏆 *TOP SPORTARTEN:*\n"
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
    
    # Winter-Empfehlung
    message += "❄️ *WINTER-EMPFEHLUNG:*\n"
    message += "  • Fokussier auf NBA 🏀\n"
    message += "  • NHL hat gute Value 🏒\n"
    message += "  • Tennis indoor 🎾\n"
    message += "  • Fußball erst ab Januar ⚽\n"
    
    await msg.edit_text(message, parse_mode='Markdown')

async def sport_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🏀 *Verwendung:* /sport <Sportart>\n\n"
            "Beispiele:\n"
            "• /sport NBA\n"
            "• /sport NHL\n"
            "• /sport tennis\n\n"
            "📅 Heute aktiv: NBA, NHL, Tennis, NFL",
            parse_mode='Markdown'
        )
        return
    
    sport_name = ' '.join(context.args).upper()
    
    result = get_backend("/feed?limit=100&min_edge=1.0")
    
    if result.get("error") or not result.get("bets"):
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result["bets"]
    sport_bets = []
    
    for bet in bets_list:
        bet_sport = str(bet.get('sport_name', '')).upper()
        bet_type = str(bet.get('sport_type', '')).upper()
        
        if sport_name in bet_sport or sport_name in bet_type:
            sport_bets.append(bet)
    
    if not sport_bets:
        await update.message.reply_text(
            f"📭 *Keine Value Bets für '{sport_name}'*\n\n"
            f"📅 Datum: 28.12.2025\n"
            f"💡 Aktive Sportarten: NBA, NHL, Tennis, NFL",
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
# BOT START
# =====================================================
def main():
    print("🤖 ValueEdge Bot startet...")
    print(f"Backend URL: {BACKEND_URL}")
    print("📅 Datum: 28.12.2025")
    print("🏀 Aktive Sportarten: NBA, NHL, Tennis, NFL")
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
    
    print("✅ Bot ist bereit!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()