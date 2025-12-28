# bot.py - ERWEITERT FÜR 20+ LIGEN
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
        "🤖 *ValueEdge Bot - 20+ LIGEN*\n\n"
        "✅ /start - Diese Hilfe\n"
        "✅ /scan - Neuen Scan starten\n"
        "✅ /bets - Value Bets anzeigen\n"
        "✅ /leagues - Alle Ligen anzeigen\n"
        "✅ /stats - System Status\n"
        "✅ /top - Top 5 Value Bets\n"
        "✅ /country <land> - Value Bets nach Land\n\n"
        f"⚽ *{len(get_leagues_list())} Fußballligen aktiv*",
        parse_mode='Markdown'
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text(
        "⚽ *Scan startet...*\n"
        f"Scanne {len(get_leagues_list())} Ligen\n"
        "Dauer: 2-3 Minuten",
        parse_mode='Markdown'
    )
    
    result = get_backend("/scan", timeout=180)  # 3 Minuten Timeout
    
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
        await msg.edit_text(
            f"🎉 *SCAN ERFOLGREICH!*\n\n"
            f"⚽ Gescannt: {leagues_scanned} Ligen\n"
            f"✅ Value Bets: {bets}\n"
            f"🏆 Ligen mit Bets: {leagues_with_bets}\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"Tippe /bets zum Anzeigen! 🚀",
            parse_mode='Markdown'
        )
    else:
        await msg.edit_text(
            f"✅ *Scan abgeschlossen*\n\n"
            f"⚽ Gescannt: {leagues_scanned} Ligen\n"
            f"🔍 Value Bets: 0\n"
            f"⏱️ Dauer: {duration:.1f}s\n\n"
            f"Keine Value Bets in den gescannten Ligen.",
            parse_mode='Markdown'
        )

async def bets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/feed?limit=10")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text("📭 Datenbank ist leer. Starte /scan")
        return
    
    # Nach Edge sortieren
    bets_sorted = sorted(bets_list, key=lambda x: x.get('edge', 0), reverse=True)
    
    message = f"🎯 *Top {len(bets_sorted)} Value Bets:*\n\n"
    
    for i, bet in enumerate(bets_sorted[:10], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get(f'odds_{pick.lower()}', bet.get('odds_home', 0))
        league = bet.get('league', 'Unbekannt')
        
        # Länder-Emoji basierend auf Liga
        country_emoji = get_country_emoji(league)
        
        message += (
            f"{i}. {country_emoji} *{match}*\n"
            f"   ⚡ {pick} @ {odds:.2f}\n"
            f"   📈 Edge: +{edge:.1f}%\n"
            f"   🏆 {get_league_name(league)}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeigt alle konfigurierten Ligen"""
    result = get_backend("/leagues")
    
    if not result or 'error' in result:
        await update.message.reply_text("❌ Kann Ligen-Info nicht laden")
        return
    
    leagues_list = result.get('leagues', [])
    
    # Gruppieren nach Land
    leagues_by_country = {}
    for league in leagues_list:
        country = league.get('country', 'Unknown')
        if country not in leagues_by_country:
            leagues_by_country[country] = []
        leagues_by_country[country].append(league)
    
    message = f"🌍 *{len(leagues_list)} Fußballligen konfiguriert:*\n\n"
    
    for country, country_leagues in sorted(leagues_by_country.items()):
        country_emoji = get_country_emoji_by_name(country)
        message += f"{country_emoji} *{country}:*\n"
        
        for league in sorted(country_leagues, key=lambda x: x.get('priority', 99)):
            league_name = league.get('name', 'Unknown')
            priority = league.get('priority', 99)
            priority_star = "⭐" if priority == 1 else "🔸" if priority == 2 else "🔹"
            
            message += f"  {priority_star} {league_name}\n"
        
        message += "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = get_backend("/health")
    
    if not result:
        await update.message.reply_text("❌ Backend nicht erreichbar")
        return
    
    # Detaillierte Statistiken
    detailed = get_backend("/stats/detailed")
    
    db_info = ""
    if detailed and 'value_bets_per_league' in detailed:
        leagues_with_bets = len(detailed['value_bets_per_league'])
        db_info = f"\n🏆 Ligen mit Value Bets: {leagues_with_bets}"
    
    message = (
        f"📊 *System Status - 20+ Ligen*\n\n"
        f"• Datenbank: {result.get('database', '❓')}\n"
        f"• Odds API: {result.get('odds_api', '❓')}\n"
        f"• Konfig. Ligen: {result.get('total_leagues', '❓')}\n"
        f"{db_info}\n"
        f"• Zeit: {result.get('timestamp', '')[:19]}\n\n"
        f"🔗 {BACKEND_URL}"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Top 5 Value Bets nach Edge"""
    result = get_backend("/feed?limit=20")
    
    if not result or 'error' in result:
        await update.message.reply_text("📭 Keine Value Bets verfügbar")
        return
    
    bets_list = result.get('bets', [])
    if not bets_list:
        await update.message.reply_text("📭 Datenbank ist leer")
        return
    
    # Nach Edge sortieren (absteigend)
    bets_sorted = sorted(bets_list, key=lambda x: x.get('edge', 0), reverse=True)
    top_5 = bets_sorted[:5]
    
    message = "🏆 *Top 5 Value Bets (höchster Edge):*\n\n"
    
    for i, bet in enumerate(top_5, 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get(f'odds_{pick.lower()}', bet.get('odds_home', 0))
        league = bet.get('league', 'Unbekannt')
        
        message += (
            f"{i}. *{match}*\n"
            f"   ⚡ {pick} @ {odds:.2f}\n"
            f"   📈 Edge: +{edge:.1f}%\n"
            f"   🏆 {get_league_name(league)}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Value Bets nach Land filtern"""
    if not context.args:
        await update.message.reply_text(
            "🌍 *Usage:* /country <Land>\n"
            "Beispiele:\n"
            "/country England\n"
            "/country Germany\n"
            "/country Spain",
            parse_mode='Markdown'
        )
        return
    
    country_name = ' '.join(context.args).title()
    
    # Alle Value Bets holen
    result = get_backend("/feed?limit=50")
    
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
        await update.message.reply_text(f"📭 Keine Value Bets für {country_name}")
        return
    
    country_emoji = get_country_emoji_by_name(country_name)
    message = f"{country_emoji} *Value Bets für {country_name}:*\n\n"
    
    for i, bet in enumerate(country_bets[:10], 1):
        match = bet.get('match', 'N/A')
        edge = bet.get('edge', 0)
        pick = bet.get('pick', '')
        odds = bet.get(f'odds_{pick.lower()}', bet.get('odds_home', 0))
        
        message += (
            f"{i}. *{match}*\n"
            f"   ⚡ {pick} @ {odds:.2f}\n"
            f"   📈 Edge: +{edge:.1f}%\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

# =====================================================
# HELPER FUNKTIONEN
# =====================================================
def get_leagues_list():
    """Holt die Liste der Ligen vom Backend"""
    result = get_backend("/leagues")
    if result and 'leagues' in result:
        return result['leagues']
    return []

def get_league_name(league_key):
    """Gibt den lesbaren Namen einer Liga zurück"""
    leagues = get_leagues_list()
    for league in leagues:
        if league.get('key') == league_key:
            return league.get('name', league_key)
    return league_key

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
    """Gibt Land basierend auf Liga-Key zurück"""
    leagues = get_leagues_list()
    for league in leagues:
        if league.get('key') == league_key:
            return league.get('country', '')
    return ''

# =====================================================
# HAUPTPROGRAMM
# =====================================================
def main():
    print("⚽ ValueEdge Bot - 20+ LIGEN")
    print(f"Backend: {BACKEND_URL}")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Commands registrieren
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("bets", bets))
    app.add_handler(CommandHandler("leagues", leagues))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("country", country))
    
    print("✅ Bot gestartet mit 20+ Ligen Support")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()