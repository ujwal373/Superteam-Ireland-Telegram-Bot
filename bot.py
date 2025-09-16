import logging
from pathlib import Path
import json
import yaml
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv
import os
import asyncio
from telegram.ext import MessageHandler, filters
load_dotenv()
from handlers import faq, events, bounties, alerts
import time
last_group_reply = {}

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load config ---
CONFIG = yaml.safe_load(Path("config.yaml").read_text())

# --- Load DB ---
DB_FILE = Path("db.json")
if not DB_FILE.exists():
    DB_FILE.write_text(json.dumps({"subscribers": [], "seen_bounties": [], "seen_events": []}))
DB = json.loads(DB_FILE.read_text())


def save_db():
    DB_FILE.write_text(json.dumps(DB, indent=2))


# --- Start & Help ---
async def start(update, context):
    text = (
        "👋 *Welcome to the Superteam Ireland Bot!*\n\n"
        "I’m here to keep you in the loop with everything happening in our community:\n"
        "• ❓ Answer FAQs about *Superteam Ireland*, Talent Hub Fridays, BuildStation & more\n"
        "• 📅 Show upcoming community *events*\n"
        "• 🏆 List open *bounties* and opportunities\n"
        "• 🔔 Send you alerts when new bounties or events go live\n\n"
        "Type /help anytime to see how to use me.\n\n"
        "_Together, we build, learn, and grow the Web3 future in Ireland ☘️_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_cmd(update, context):
    text = (
        "🛠️ *Here’s how you can use me:*\n\n"
        "• `/faq <your question>` → Ask me about Superteam Ireland, events, or programs\n"
        "• `/events` → See the next 5 upcoming events\n"
        "• `/bounties` → Check the latest live bounties (with rewards & deadlines)\n"
        "• `/subscribe` → Get DM alerts when new bounties/events drop\n"
        "• `/unsubscribe` → Stop alerts anytime\n\n"
        "_Tip: In group chats, just mention me with a question (e.g. `@SuperteamIrelandBot When’s the next Talent Hub?`) and I’ll reply._"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# --- Group mention handler ---
async def mention_handler(update, context):
    """
    Trigger FAQ when bot is mentioned in a group with a question.
    Rate limited to avoid spam (1 reply every 10s per group).
    """
    if update.message.chat.type not in ["group", "supergroup"]:
        return

    chat_id = update.message.chat.id
    text = update.message.text or ""
    bot_username = context.bot.username  # already available, no need to call get_me()

    if f"@{bot_username}" not in text:
        return

    # --- Rate limiting ---
    now = time.time()
    last_time = last_group_reply.get(chat_id, 0)
    if now - last_time < 10:  # 10-second cooldown
        logger.info(f"Rate limit hit in chat {chat_id}, ignoring mention.")
        return
    last_group_reply[chat_id] = now

    # Clean the mention from the text
    question = text.replace(f"@{bot_username}", "").strip()

    if not question:
        await update.message.reply_text(
            f"👋 You mentioned me! Try asking a question, e.g.: '@{bot_username} How do I join Superteam?'"
        )
        return

    # Forward to FAQ
    context.args = question.split()
    await faq.faq(update, context)

# --- Main ---
def main():
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("faq", faq.faq))
    app.add_handler(CommandHandler("events", events.events))
    app.add_handler(CommandHandler("bounties", bounties.bounties))
    app.add_handler(CommandHandler("subscribe", alerts.subscribe))
    app.add_handler(CommandHandler("unsubscribe", alerts.unsubscribe))
    # app.add_handler(CommandHandler("testalert", alerts.testalert))
    # app.add_handler(CommandHandler("digestnow", alerts.digestnow))

    # Group mention handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_handler))

    # Startup hook
    async def on_startup(app):
        asyncio.create_task(
            alerts.scheduler(
                app.bot,
                interval_minutes=CONFIG.get("schedule", {}).get("bounty_check_minutes", 10)
            )
        )

    app.post_init = on_startup

    logger.info("Bot started in polling mode…")
    app.run_polling()   # <--- switched to polling


if __name__ == "__main__":
    main()

