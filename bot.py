# bot.py - ERWEITERTER TELEGRAM BOT MIT ANALYSIS
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

def post_backend(endpoint, timeout=180):
    try:
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.get(  # Achtung: /scan ist GET, nicht POST!
            f"{BACKEND_URL}{endpoint}",
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Backend Scan {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        logger.error(f"Scan Fehler: {e}")
        return None

# =====================================================
# TELEGRAM COMMANDS
# =====================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ValueEdge Bot - SMART SCANNER*\n\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Smart Scan starten\n"
        "✅ /bets - Value Bets anzeigen\n"
        "✅ /analysis - Detaillierte Analyse\n"
        "✅ /leagues - Aktive Ligen\n"
        "✅ /stats - System Status\n"
        "✅ /top - Top 5 Value Bets\n"
        "✅ /country <land> - Value Bets nach Land\n\n"
        "🎯 *Erweiterter Filter:* Quote 1.40-5.0, Edge≥1.0%",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "🎯 *Smart Scan startet...*\n"
        "Scanne nur aktive Ligen\n"
        "Erweiterter Filter aktiv",
        parse_mode='Markdown'
    )
    
    result = post_backend("/scan", timeout=180)
    
    if result is None:
        await msg.edit_text("❌ Backend nicht erreichbar")
        return
    
    if 'error' in result:
        await msg.edit_text(f"❌ Fehler: {result['error']}")
        return
    
    bets = result.get('total_value_bets', 0)
    duration = result.get('duration_seconds', 0)
    leagues_scanned = result.get('leagues_scanned', 0)
    active_leagues = result.get('active_leagues_today', 0)
    leagues_with_bets = result.get('leagues_with_bets', 0)
    
    if bets > 0:
        await msg.edit_text(
            f"🎉 *SMART SCAN ERFOLGREICH!*\n\n"
            f"⚽ Aktive Ligen heute: {active_leagues}\n"
            f"🔍 Gescannt: {leagues_scanned} Ligen\n"
            f"✅ Value Bets gefunden: {bets}\n"
            f"🏆 Ligen mit Value Bets: {leagues_with_bets}\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"🎯 Filter: Quote 1.40-5.0, Edge≥1.0%\n\n"
            f"Tippe /bets zum Anzeigen! 🚀",
            parse_mode='Markdown'
        )
    else:
        leagues_list = result.get('results_summary', {}).get('leagues_no_bets', [])
        leagues_text = "\n".join([f"• {l}" for l in leagues_list[:5]])
        
        await msg.edit_text(
            f"✅ *Scan abgeschlossen*\n\n"
            f"⚽ Aktive Ligen: {active_leagues}\n"
            f"🔍 Gescannt: {leagues_scanned} Ligen\n"
            f"🎯 Value Bets: 0\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"*Keine Value Bets heute in:*\n"
            f"{leagues_text}\n\n"
            f"💡 Tipp: Probier /analysis für Details",
            parse_mode='Markdown'
        )

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeigt Value Bets mit erweiterten Filtern"""
    result = get_backend("/feed?limit=15&min_edge=1.0&max_odds=5.0")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text(
            "📭 Keine Value Bets in Datenbank.\n"
            "🎯 Filter: Quote 1.40-5.0, Edge≥1.0%\n"
            "💡 Tippe /scan für neuen Scan!",
            parse_mode='Markdown'
        )
        return
    
    # Nach Edge sortieren
    bets_sorted = sorted(bets_list, key=lambda x: x.get('edge', 0), reverse=True)
    
    message = f"🎯 *Top {len(bets_sorted)} Value Bets:*\n"
    message += "🎯 Filter: Quote 1.40-5.0, Edge≥1.0%\n\n"
    
    for i, bet in enumerate(bets_sorted[:15], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        
        # Korrekte Odds finden
        if pick == "HOME":
            odds = bet.get('odds_home', 0)
        elif pick == "AWAY":
            odds = bet.get('odds_away', 0)
        else:  # DRAW
            odds = bet.get('odds_draw', 0)
        
        league = bet.get('league', 'Unbekannt')
        country_emoji = get_country_emoji(league)
        
        # Edge-Farbe basierend auf Wert
        if edge > 5:
            edge_emoji = "🔥"
        elif edge > 3:
            edge_emoji = "⚡"
        else:
            edge_emoji = "📈"
        
        message += (
            f"{i}. {country_emoji} *{match}*\n"
            f"   {edge_emoji} {pick} @ {odds:.2f}\n"
            f"   Edge: +{edge:.1f}%\n"
            f"   🏆 {get_league_name(league)}\n\n"
        )
    
    message += f"🎯 *Filter:* Quote 1.40-5.0, Edge≥1.0%"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detaillierte Analyse der Value Bets"""
    msg = await update.message.reply_text("📊 Analysiere Daten...")
    
    # Hole Daten
    stats_result = get_backend("/stats/advanced")
    bets_result = get_backend("/feed?limit=50")
    
    if not stats_result or 'error' in stats_result:
        await msg.edit_text("❌ Kann Analyse nicht laden")
        return
    
    if not bets_result or 'error' in bets_result:
        await msg.edit_text("📭 Keine Value Bets für Analyse")
        return
    
    bets_list = bets_result.get('bets', [])
    if not bets_list:
        await msg.edit_text("📭 Keine Value Bets in Datenbank")
        return
    
    # Basis-Statistiken
    total_bets = stats_result.get('total_value_bets', 0)
    avg_edge = stats_result.get('average_edge', 0)
    top_leagues = stats_result.get('top_leagues', [])
    
    # Detaillierte Analyse
    edge_distribution = {
        "high": 0,    # > 5%
        "medium": 0,  # 2-5%
        "low": 0      # 1-2%
    }
    
    odds_distribution = {
        "low": 0,     # 1.40-2.00
        "medium": 0,  # 2.01-3.50
        "high": 0     # 3.51-5.00
    }
    
    for bet in bets_list:
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        
        # Edge-Verteilung
        if edge > 5:
            edge_distribution["high"] += 1
        elif edge >= 2:
            edge_distribution["medium"] += 1
        else:
            edge_distribution["low"] += 1
        
        # Odds-Verteilung
        if pick == "HOME":
            odds = bet.get('odds_home', 0)
        elif pick == "AWAY":
            odds = bet.get('odds_away', 0)
        else:
            odds = bet.get('odds_draw', 0)
        
        if odds <= 2.00:
            odds_distribution["low"] += 1
        elif odds <= 3.50:
            odds_distribution["medium"] += 1
        else:
            odds_distribution["high"] += 1
    
    # Nachrichten erstellen
    message = "📊 *DETAILLIERTE VALUE BET ANALYSE*\n\n"
    
    message += f"• Gesamt Value Bets: {total_bets}\n"
    message += f"• Durchschnitt Edge: {avg_edge:.1f}%\n\n"
    
    message += "🏆 *TOP LIGEN NACH VALUE BETS:*\n"
    for league in top_leagues[:3]:
        name = league.get('name', league.get('league', 'Unknown'))
        count = league.get('count', 0)
        avg = league.get('avg_edge', 0)
        message += f"  • {name}: {count} Bets (Ø{avg:.1f}%)\n"
    
    message += "\n📈 *EDGE-VERTEILUNG:*\n"
    message += f"  • Hoch (>5%): {edge_distribution['high']}\n"
    message += f"  • Mittel (2-5%): {edge_distribution['medium']}\n"
    message += f"  • Niedrig (1-2%): {edge_distribution['low']}\n"
    
    message += "\n🎯 *QUOTEN-VERTEILUNG:*\n"
    message += f"  • Niedrig (1.40-2.00): {odds_distribution['low']}\n"
    message += f"  • Mittel (2.01-3.50): {odds_distribution['medium']}\n"
    message += f"  • Hoch (3.51-5.00): {odds_distribution['high']}\n\n"
    
    # Empfehlung
    if edge_distribution['high'] > 0:
        message += "🔥 *EMPFEHLUNG:* Exzellente Value Bets vorhanden!\n"
    elif edge_distribution['medium'] > 0:
        message += "⚡ *EMPFEHLUNG:* Gute Value Bets verfügbar\n"
    else:
        message += "💡 *EMPFEHLUNG:* Filter erweitern oder mehr Ligen scannen\n"
    
    message += "\n🎯 Aktueller Filter: Quote 1.40-5.0, Edge≥1.0%"
    
    await msg.edit_text(message, parse_mode='Markdown')

async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeigt aktive Ligen"""
    result = get_backend("/health")
    
    if not result or 'error' in result:
        await update.message.reply_text("❌ Kann Ligen-Info nicht laden")
        return
    
    active_leagues = result.get('active_leagues', 0)
    
    message = f"⚽ *AKTIVE LIGEN KONFIGURIERT:* {active_leagues}\n\n"
    
    # Statische Liste (basierend auf main.py)
    active_leagues_list = [
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (England)",
        "🇮🇹 Serie A (Italy)",
        "🇪🇸 La Liga (Spain)",
        "🇩🇪 Bundesliga (Germany)",
        "🇫🇷 Ligue 1 (France)",
        "🇳🇱 Eredivisie (Netherlands)",
        "🇵🇹 Primeira Liga (Portugal)",
        "🇧🇪 Belgium Pro League",
        "🇹🇷 Süper Lig (Turkey)",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship (England)",
        "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership"
    ]
    
    for league in active_leagues_list:
        message += f"• {league}\n"
    
    message += "\n🎯 *Smart Scanner:* Scannt nur aktive Ligen"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if not result:
        await update.message.reply_text("❌ Backend nicht erreichbar")
        return
    
    # Detaillierte Statistiken
    detailed = get_backend("/stats/advanced")
    
    total_bets = result.get('total_value_bets_in_db', 0)
    active_leagues = result.get('active_leagues', 0)
    filter_info = result.get('filter', 'Unknown')
    
    db_info = ""
    if detailed and 'top_leagues' in detailed:
        top_league = detailed['top_leagues'][0] if detailed['top_leagues'] else {}
        db_info = f"\n🏆 Top Liga: {top_league.get('name', 'N/A')} ({top_league.get('count', 0)} Bets)"
    
    message = (
        f"📊 *SMART SCANNER STATUS*\n\n"
        f"• Datenbank: {result.get('database', '❓')}\n"
        f"• Odds API: {result.get('odds_api', '❓')}\n"
        f"• Aktive Ligen: {active_leagues}\n"
        f"• Value Bets in DB: {total_bets}\n"
        f"{db_info}\n"
        f"• Filter: {filter_info}\n"
        f"• Zeit: {result.get('timestamp', '')[:19]}\n\n"
        f"🔗 {BACKEND_URL}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Top 5 Value Bets nach Edge"""
    result = get_backend("/feed?limit=5&order=edge.desc")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text("📭 Datenbank ist leer")
        return
    
    message = "🏆 *TOP 5 VALUE BETS (höchster Edge):*\n\n"
    
    for i, bet in enumerate(bets_list, 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        
        if pick == "HOME":
            odds = bet.get('odds_home', 0)
        elif pick == "AWAY":
            odds = bet.get('odds_away', 0)
        else:
            odds = bet.get('odds_draw', 0)
        
        league = bet.get('league', 'Unbekannt')
        country_emoji = get_country_emoji(league)
        
        message += (
            f"{i}. {country_emoji} *{match}*\n"
            f"   ⚡ {pick} @ {odds:.2f}\n"
            f"   📈 Edge: +{edge:.1f}%\n"
            f"   🏆 {get_league_name(league)}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Value Bets nach Land filtern"""
    if not context.args:
        await update.message.reply_text(
            "🌍 *Verwendung:* /country <Land>\n\n"
            "Beispiele:\n"
            "/country Germany\n"
            "/country Spain\n"
            "/country England\n\n"
            "🎯 Filter: Quote 1.40-5.0, Edge≥1.0%",
            parse_mode='Markdown'
        )
        return
    
    country_name = ' '.join(context.args).title()
    
    # Alle Value Bets holen
    result = get_backend("/feed?limit=100&min_edge=1.0")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text("📭 Datenbank ist leer")
        return
    
    # Nach Land filtern
    country_bets = []
    for bet in bets_list:
        league = bet.get('league', '')
        league_country = get_country_by_league(league)
        if league_country and country_name.lower() in league_country.lower():
            country_bets.append(bet)
    
    if not country_bets:
        await update.message.reply_text(
            f"📭 Keine Value Bets für {country_name}\n\n"
            f"🎯 Filter: Quote 1.40-5.0, Edge≥1.0%\n"
            f"💡 Tipp: Probier /scan für neuen Scan",
            parse_mode='Markdown'
        )
        return
    
    country_emoji = get_country_emoji_by_name(country_name)
    message = f"{country_emoji} *VALUE BETS FÜR {country_name.upper()}:*\n\n"
    
    for i, bet in enumerate(country_bets[:10], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        
        if pick == "HOME":
            odds = bet.get('odds_home', 0)
        elif pick == "AWAY":
            odds = bet.get('odds_away', 0)
        else:
            odds = bet.get('odds_draw', 0)
        
        message += (
            f"{i}. *{match}*\n"
            f"   ⚡ {pick} @ {odds:.2f}\n"
            f"   📈 Edge: +{edge:.1f}%\n\n"
        )
    
    message += f"🎯 Filter: Quote 1.40-5.0, Edge≥1.0%"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# =====================================================
# HELPER FUNKTIONEN
# =====================================================
def get_league_name(league_key):
    """Gibt den lesbaren Namen einer Liga zurück"""
    league_map = {
        "soccer_epl": "Premier League",
        "soccer_italy_serie_a": "Serie A",
        "soccer_spain_la_liga": "La Liga",
        "soccer_germany_bundesliga": "Bundesliga",
        "soccer_france_ligue_one": "Ligue 1",
        "soccer_netherlands_eredivisie": "Eredivisie",
        "soccer_portugal_primeira_liga": "Primeira Liga",
        "soccer_belgium_first_div": "Belgium Pro League",
        "soccer_turkey_super_lig": "Süper Lig",
        "soccer_england_efl_champ": "Championship",
        "soccer_scotland_premier": "Scottish Premiership"
    }
    return league_map.get(league_key, league_key)

def get_country_emoji(league_key):
    """Gibt Länder-Emoji basierend auf Liga"""
    country_map = {
        'england': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
        'germany': '🇩🇪',
        'spain': '🇪🇸',
        'italy': '🇮🇹',
        'france': '🇫🇷',
        'netherlands': '🇳🇱',
        'portugal': '🇵🇹',
        'belgium': '🇧🇪',
        'turkey': '🇹🇷',
        'scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿'
    }
    
    league_key_lower = league_key.lower()
    for country, emoji in country_map.items():
        if country in league_key_lower:
            return emoji
    
    return '🏟️'

def get_country_emoji_by_name(country_name):
    """Gibt Emoji für Ländernamen"""
    emoji_map = {
        'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
        'Germany': '🇩🇪',
        'Spain': '🇪🇸',
        'Italy': '🇮🇹',
        'France': '🇫🇷',
        'Netherlands': '🇳🇱',
        'Portugal': '🇵🇹',
        'Belgium': '🇧🇪',
        'Turkey': '🇹🇷',
        'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿'
    }
    
    return emoji_map.get(country_name, '🌍')

def get_country_by_league(league_key):
    """Gibt Land basierend auf Liga-Key zurück"""
    country_map = {
        "soccer_epl": "England",
        "soccer_italy_serie_a": "Italy",
        "soccer_spain_la_liga": "Spain",
        "soccer_germany_bundesliga": "Germany",
        "soccer_france_ligue_one": "France",
        "soccer_netherlands_eredivisie": "Netherlands",
        "soccer_portugal_primeira_liga": "Portugal",
        "soccer_belgium_first_div": "Belgium",
        "soccer_turkey_super_lig": "Turkey",
        "soccer_england_efl_champ": "England",
        "soccer_scotland_premier": "Scotland"
    }
    return country_map.get(league_key, "")

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("🤖 ValueEdge Bot - SMART SCANNER")
    print(f"Backend: {BACKEND_URL}")
    print("🎯 Erweiterter Filter: Quote 1.40-5.0, Edge≥1.0%")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands registrieren
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("bets", bets))
    app.add_handler(CommandHandler("analysis", analysis))
    app.add_handler(CommandHandler("leagues", leagues))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("country", country))
    
    print("✅ Bot gestartet mit Smart Scanner")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()