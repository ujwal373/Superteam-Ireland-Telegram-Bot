import logging
import asyncio
from pathlib import Path
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import httpx
from telegram import Bot

from handlers import bounties, events

logger = logging.getLogger(__name__)

# --- DB setup ---
DB_FILE = Path("db.json")
if not DB_FILE.exists():
    DB_FILE.write_text(json.dumps({
        "subscribers": [],
        "seen_bounties": [],
        "seen_events": [],
        "last_digest_date": None
    }))

DB = json.loads(DB_FILE.read_text())


def save_db():
    DB_FILE.write_text(json.dumps(DB, indent=2))


# --- Subscribe / Unsubscribe ---
async def subscribe(update, context):
    user_id = update.message.from_user.id
    if user_id not in DB["subscribers"]:
        DB["subscribers"].append(user_id)
        save_db()
        await update.message.reply_text("✅ You have subscribed to alerts!")
    else:
        await update.message.reply_text("ℹ️ You are already subscribed.")


async def unsubscribe(update, context):
    user_id = update.message.from_user.id
    if user_id in DB["subscribers"]:
        DB["subscribers"].remove(user_id)
        save_db()
        await update.message.reply_text("❌ You have unsubscribed from alerts.")
    else:
        await update.message.reply_text("ℹ️ You are not subscribed.")


# --- Alert sending ---
async def send_alert(bot: Bot, message: str):
    for user_id in DB["subscribers"]:
        try:
            await bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Failed to send alert to {user_id}: {e}")


# --- Gemini opener (daily quotes) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash"

async def generate_opener():
    if not GEMINI_API_KEY:
        return (
            "“Builders write history in code, not in headlines.” ☘️\n"
            "#solana #web3 #community #smallcountrybigatheart #superteamireland"
        )

    prompt = (
        "You are an inspirational Irish storyteller speaking to a Web3 builder community. "
        "Generate ONE short motivational quote (not a casual greeting), around 25 words, "
        "about crypto, builders, or community spirit. "
        "Make it sound like a proverb or wise saying, with a subtle Irish touch (not cheesy). "
        "At the end, put these hashtags on a NEW LINE:\n"
        "#solana #web3 #community #smallcountrybigatheart #superteamireland"
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Safety: ensure hashtags at the end
            if "#solana" not in text:
                text += "\n#solana #web3 #community #smallcountrybigatheart #superteamireland"
            return text
    except Exception as e:
        logger.warning(f"Gemini opener failed: {e}")
        return (
            "“When markets dip, true builders rise.” ☘️\n"
            "#solana #web3 #community #smallcountrybigatheart #superteamireland"
        )

# --- Bounty alerts ---
async def check_bounties(bot: Bot):
    current_bounties = bounties.fetch_bounties()
    new_bounties = []

    for b in current_bounties:
        key = f"{b['title']}_{b['deadline']}"
        if key not in DB["seen_bounties"]:
            DB["seen_bounties"].append(key)
            new_bounties.append(b)

    if new_bounties:
        save_db()
        for b in new_bounties:
            deadline_str = b["deadline"] if b["deadline"] else "N/A"
            message = (
                f"🏆 *New Bounty!*\n\n"
                f"*{b['title']}*\n"
                f"💰 Reward: {b['reward']}\n"
                f"⏳ Deadline: {deadline_str}\n"
                f"🔗 {b['link']}"
            )
            await send_alert(bot, message)


# --- Event alerts ---
async def check_events(bot: Bot):
    current_events = events.fetch_events()
    new_events = []

    for e in current_events:
        key = f"{e['title']}_{e['date']}"
        if key not in DB["seen_events"]:
            DB["seen_events"].append(key)
            new_events.append(e)

    if new_events:
        save_db()
        for e in new_events:
            message = (
                f"📌 *New Event!*\n\n"
                f"*{e['title']}*\n"
                f"📅 {e['date']}\n"
                f"🔗 {e['link']}"
            )
            await send_alert(bot, message)


# --- Scheduler ---
async def scheduler(bot: Bot, interval_minutes=10):
    """Run periodic checks for new bounties and events."""
    while True:
        try:
            await check_bounties(bot)
            await check_events(bot)
        except Exception as e:
            logger.error(f"Error in scheduler: {e}")
        await asyncio.sleep(interval_minutes * 60)


# --- Morning Digest ---
async def send_morning_digest(bot: Bot, group_chat_id: int):
    opener = await generate_opener()
    evts = events.fetch_events() or []
    btys = bounties.fetch_bounties() or []

    parts = [f"{opener}\n\n*Superteam Ireland — Daily Brief*"]

    if evts:
        e = evts[0]
        parts.append("— *Next Event* —")
        parts.append(f"📌 *{e['title']}*\n📅 {e['date']}\n🔗 {e['link']}")
    else:
        parts.append("— *Next Event* —\nNo upcoming events yet.")

    if btys:
        parts.append("\n— *Open Bounties* —")
        for b in btys[:5]:
            deadline_str = b["deadline"] if b["deadline"] else "N/A"
            parts.append(
                f"🏆 *{b['title']}*\n"
                f"💰 {b['reward']}\n"
                f"⏳ {deadline_str}\n"
                f"🔗 {b['link']}"
            )
    else:
        parts.append("\nNo open bounties right now. Check back later!")

    text = "\n\n".join(parts)

    try:
        await bot.send_message(
            chat_id=group_chat_id,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.warning(f"Failed to send digest to group {group_chat_id}: {e}")


async def digest_loop(bot: Bot, digest_time_str: str, tz_name: str, group_chat_id: int):
    """Send a daily digest at the configured time."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Europe/Dublin")

    while True:
        now = datetime.now(tz)
        target_h, target_m = map(int, digest_time_str.split(":"))
        last = DB.get("last_digest_date")

        if now.hour == target_h and now.minute == target_m and (last != now.date().isoformat()):
            logger.info("Sending morning digest…")
            await send_morning_digest(bot, group_chat_id)
            DB["last_digest_date"] = now.date().isoformat()
            save_db()
            await asyncio.sleep(90)
        else:
            await asyncio.sleep(30)


# # --- Digest Now (manual trigger) ---
async def digestnow(update, context):
    """Manually trigger the morning digest for testing."""
    group_id = update.message.chat_id  # send digest in the same chat
    await send_morning_digest(context.bot, group_id)
    #await update.message.reply_text("✅ Morning digest sent here.")
