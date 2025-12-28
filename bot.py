# bot.py - ValueEdge Telegram Bot MIT ANALYSIS
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
        "🤖 *ValueEdge Bot - ERWEITERTE FILTER*\n\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Scan starten\n"
        "✅ /bets - Value Bets anzeigen\n"
        "✅ /analysis - Detaillierte Analyse\n"
        "✅ /leagues - Alle Ligen\n"
        "✅ /stats - System Status\n"
        "✅ /top - Top 5 Value Bets\n"
        "✅ /country <land> - Value Bets nach Land\n\n"
        "🎯 *Erweiterter Filter:* Quote 1.40-5.0, Edge≥1.0%\n"
        "⚡ *Mehr Value Bets als je zuvor!*",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "⚽ *Scan startet mit erweiterten Filtern...*\n"
        "Scanne 28 Ligen...\n"
        "Filter: Quote 1.40-5.0, Edge≥1.0%",
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
    leagues_scanned = result.get('leagues_scanned', 0)
    leagues_with_bets = result.get('leagues_with_bets', 0)
    
    if bets > 0:
        leagues_list = result.get('results_summary', {}).get('leagues_with_bets', [])
        leagues_text = "\n".join([f"• {l}" for l in leagues_list[:3]])
        
        await msg.edit_text(
            f"🎉 *SCAN ERFOLGREICH!*\n\n"
            f"⚽ Gescannt: {leagues_scanned} Ligen\n"
            f"✅ Value Bets gefunden: {bets}\n"
            f"🏆 Ligen mit Bets: {leagues_with_bets}\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"🎯 *Erfolgreiche Ligen:*\n"
            f"{leagues_text}\n\n"
            f"🎯 Filter: Quote 1.40-5.0, Edge≥1.0%\n\n"
            f"Tippe /bets zum Anzeigen! 🚀",
            parse_mode='Markdown'
        )
    else:
        leagues_list = result.get('results_summary', {}).get('leagues_no_bets', [])
        leagues_text = "\n".join([f"• {l}" for l in leagues_list[:5]])
        
        await msg.edit_text(
            f"✅ *Scan abgeschlossen*\n\n"
            f"⚽ Gescannt: {leagues_scanned} Ligen\n"
            f"🔍 Value Bets: 0\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"🎯 Filter: Quote 1.40-5.0, Edge≥1.0%\n\n"
            f"*Keine Value Bets heute in:*\n"
            f"{leagues_text}\n\n"
            f"💡 Tipp: Probier /analysis für Details",
            parse_mode='Markdown'
        )

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/feed?limit=15")
    
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
    
    bets_sorted = sorted(bets_list, key=lambda x: x.get('edge', 0), reverse=True)
    
    message = f"🎯 *Top {len(bets_sorted)} Value Bets:*\n"
    message += "🎯 Filter: Quote 1.40-5.0, Edge≥1.0%\n\n"
    
    for i, bet in enumerate(bets_sorted[:15], 1):
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
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📊 Analysiere Daten...")
    
    result = get_backend("/stats/advanced")
    
    if not result or 'error' in result:
        await msg.edit_text("❌ Kann Analyse nicht laden")
        return
    
    total_bets = result.get('total_value_bets', 0)
    
    if total_bets == 0:
        await msg.edit_text("📭 Keine Value Bets für Analyse")
        return
    
    avg_edge = result.get('average_edge', 0)
    top_leagues = result.get('top_5_leagues', [])
    edge_dist = result.get('edge_distribution', {})
    pick_dist = result.get('pick_distribution', {})
    
    message = "📊 *DETAILLIERTE VALUE BET ANALYSE*\n\n"
    message += f"• Gesamt Value Bets: {total_bets}\n"
    message += f"• Durchschnitt Edge: {avg_edge:.1f}%\n\n"
    
    message += "🏆 *TOP LIGEN:*\n"
    for league in top_leagues[:3]:
        name = league.get('name', league.get('league', 'Unknown'))
        count = league.get('count', 0)
        message += f"  • {name}: {count} Value Bets\n"
    
    message += f"\n📈 *EDGE-VERTEILUNG:*\n"
    message += f"  • Hoch (>5%): {edge_dist.get('high', 0)}\n"
    message += f"  • Mittel (2-5%): {edge_dist.get('medium', 0)}\n"
    message += f"  • Niedrig (<2%): {edge_dist.get('low', 0)}\n"
    
    message += f"\n🎯 *PICK-VERTEILUNG:*\n"
    message += f"  • HOME: {pick_dist.get('HOME', 0)}\n"
    message += f"  • AWAY: {pick_dist.get('AWAY', 0)}\n"
    message += f"  • DRAW: {pick_dist.get('DRAW', 0)}\n\n"
    
    if edge_dist.get('high', 0) > 0:
        message += "🔥 *EMPFEHLUNG:* Exzellente Value Bets vorhanden!"
    elif edge_dist.get('medium', 0) > 0:
        message += "⚡ *EMPFEHLUNG:* Gute Value Bets verfügbar"
    else:
        message += "💡 *EMPFEHLUNG:* Mehr Scans durchführen"
    
    message += "\n\n🎯 Filter: Quote 1.40-5.0, Edge≥1.0%"
    
    await msg.edit_text(message, parse_mode='Markdown')

async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if not result or 'error' in result:
        await update.message.reply_text("❌ Kann Ligen-Info nicht laden")
        return
    
    total_leagues = result.get('total_leagues', 0)
    
    message = f"⚽ *{total_leagues} FUSSBALLLIGEN KONFIGURIERT:*\n\n"
    
    # Top 10 Ligen auflisten
    top_leagues = [
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League (England)",
        "🇮🇹 Serie A (Italy)",
        "🇪🇸 La Liga (Spain)",
        "🇩🇪 Bundesliga (Germany)",
        "🇫🇷 Ligue 1 (France)",
        "🇳🇱 Eredivisie (Netherlands)",
        "🇵🇹 Primeira Liga (Portugal)",
        "🇧🇪 Belgium Pro League",
        "🇹🇷 Süper Lig (Turkey)",
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship (England)"
    ]
    
    for league in top_leagues:
        message += f"• {league}\n"
    
    message += f"\n... und {total_leagues - 10} weitere Ligen\n\n"
    message += "🎯 Filter: Quote 1.40-5.0, Edge≥1.0%"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if not result:
        await update.message.reply_text("❌ Backend nicht erreichbar")
        return
    
    total_bets = result.get('total_value_bets_in_db', 0)
    total_leagues = result.get('total_leagues', 0)
    filter_info = result.get('filter', 'Unknown')
    
    message = (
        f"📊 *SYSTEM STATUS - ERWEITERTE FILTER*\n\n"
        f"• Datenbank: {result.get('database', '❓')}\n"
        f"• Odds API: {result.get('odds_api', '❓')}\n"
        f"• Konfig. Ligen: {total_leagues}\n"
        f"• Value Bets in DB: {total_bets}\n"
        f"• Filter: {filter_info}\n"
        f"• Zeit: {result.get('timestamp', '')[:19]}\n\n"
        f"🔗 {BACKEND_URL}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/feed?limit=5")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text("📭 Datenbank ist leer")
        return
    
    bets_sorted = sorted(bets_list, key=lambda x: x.get('edge', 0), reverse=True)
    
    message = "🏆 *TOP 5 VALUE BETS (höchster Edge):*\n\n"
    
    for i, bet in enumerate(bets_sorted[:5], 1):
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
    
    message += "🎯 Filter: Quote 1.40-5.0, Edge≥1.0%"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    result = get_backend("/feed?limit=100")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text("📭 Datenbank ist leer")
        return
    
    country_bets = []
    for bet in bets_list:
        league = bet.get('league', '')
        league_country = get_country_by_league(league)
        if league_country and country_name.lower() in league_country.lower():
            country_bets.append(bet)
    
    if not country_bets:
        await update.message.reply_text(
            f"📭 Keine Value Bets für {country_name}\n\n"
            f"🎯 Filter: Quote 1.40-5.0, Edge≥1.0%",
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
        "soccer_scotland_premier": "Scottish Premiership",
        "soccer_austria_bundesliga": "Austrian Bundesliga",
        "soccer_switzerland_superleague": "Swiss Super League",
        "soccer_russia_premier_league": "Russian Premier League",
        "soccer_greece_super_league": "Greek Super League",
        "soccer_denmark_superliga": "Danish Superliga",
        "soccer_sweden_allsvenskan": "Swedish Allsvenskan",
        "soccer_norway_eliteserien": "Norwegian Eliteserien",
        "soccer_poland_ekstraklasa": "Polish Ekstraklasa",
        "soccer_czech_republic_first_league": "Czech First League",
        "soccer_ukraine_premier_league": "Ukrainian Premier League",
        "soccer_usa_mls": "MLS",
        "soccer_brazil_serie_a": "Brasileirão",
        "soccer_argentina_primera_division": "Argentinian Primera",
        "soccer_mexico_liga_mx": "Liga MX",
        "soccer_japan_j1_league": "J1 League",
        "soccer_korea_kleague1": "K League 1",
        "soccer_australia_aleague": "A-League"
    }
    return league_map.get(league_key, league_key)

def get_country_emoji(league_key):
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
        'scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
        'austria': '🇦🇹',
        'switzerland': '🇨🇭',
        'russia': '🇷🇺',
        'greece': '🇬🇷',
        'denmark': '🇩🇰',
        'sweden': '🇸🇪',
        'norway': '🇳🇴',
        'poland': '🇵🇱',
        'czech': '🇨🇿',
        'ukraine': '🇺🇦',
        'usa': '🇺🇸',
        'brazil': '🇧🇷',
        'argentina': '🇦🇷',
        'mexico': '🇲🇽',
        'japan': '🇯🇵',
        'korea': '🇰🇷',
        'australia': '🇦🇺'
    }
    
    league_key_lower = league_key.lower()
    for country, emoji in country_map.items():
        if country in league_key_lower:
            return emoji
    
    return '🏟️'

def get_country_emoji_by_name(country_name):
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
        'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
        'Austria': '🇦🇹',
        'Switzerland': '🇨🇭',
        'Russia': '🇷🇺',
        'Greece': '🇬🇷',
        'Denmark': '🇩🇰',
        'Sweden': '🇸🇪',
        'Norway': '🇳🇴',
        'Poland': '🇵🇱',
        'Czech Republic': '🇨🇿',
        'Ukraine': '🇺🇦',
        'USA': '🇺🇸',
        'Brazil': '🇧🇷',
        'Argentina': '🇦🇷',
        'Mexico': '🇲🇽',
        'Japan': '🇯🇵',
        'South Korea': '🇰🇷',
        'Australia': '🇦🇺'
    }
    
    return emoji_map.get(country_name, '🌍')

def get_country_by_league(league_key):
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
        "soccer_scotland_premier": "Scotland",
        "soccer_austria_bundesliga": "Austria",
        "soccer_switzerland_superleague": "Switzerland",
        "soccer_russia_premier_league": "Russia",
        "soccer_greece_super_league": "Greece",
        "soccer_denmark_superliga": "Denmark",
        "soccer_sweden_allsvenskan": "Sweden",
        "soccer_norway_eliteserien": "Norway",
        "soccer_poland_ekstraklasa": "Poland",
        "soccer_czech_republic_first_league": "Czech Republic",
        "soccer_ukraine_premier_league": "Ukraine",
        "soccer_usa_mls": "USA",
        "soccer_brazil_serie_a": "Brazil",
        "soccer_argentina_primera_division": "Argentina",
        "soccer_mexico_liga_mx": "Mexico",
        "soccer_japan_j1_league": "Japan",
        "soccer_korea_kleague1": "South Korea",
        "soccer_australia_aleague": "Australia"
    }
    return country_map.get(league_key, "")

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("🤖 ValueEdge Telegram Bot - ERWEITERTE FILTER")
    print(f"Backend: {BACKEND_URL}")
    print("🎯 Filter: Quote 1.40-5.0, Edge≥1.0%")
    
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
    
    print("✅ Bot gestartet mit erweiterten Filtern")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()