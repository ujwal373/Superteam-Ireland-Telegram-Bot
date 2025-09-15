import logging
import requests
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

# Load config
CONFIG = yaml.safe_load(Path("config.yaml").read_text())


def fetch_bounties():
    """Fetch open bounties as dicts for handler + alerts."""
    url = CONFIG["feeds"]["bounties"]
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return []

        bounties = []
        for bounty in results[:5]:
            title = bounty.get("title", "No title")
            reward_amount = bounty.get("rewardAmount")
            token = bounty.get("token", "")
            reward = f"{reward_amount} {token}" if reward_amount else "N/A"

            # Handle deadline safely
            deadline_raw = bounty.get("deadline")
            deadline = deadline_raw[:10] if isinstance(deadline_raw, str) else None

            # Build proper link from slug
            slug = bounty.get("slug", "")
            link = f"https://earn.superteam.fun/listing/{slug}" if slug else "#"

            bounties.append({
                "title": title,
                "reward": reward,
                "deadline": deadline,
                "link": link
            })
        return bounties

    except Exception as e:
        logger.error(f"Error fetching bounties: {e}")
        return []


# --- Telegram handler ---
async def bounties(update, context):
    """
    Telegram command handler for /bounties
    """
    bounty_list = fetch_bounties()
    if not bounty_list:
        await update.message.reply_text("No open bounties found.")
        return

    text = ""
    for b in bounty_list:
        deadline_str = b["deadline"] if b["deadline"] else "N/A"
        text += (
            f"🏆 {b['title']}\n"
            f"💰 Reward: {b['reward']}\n"
            f"⏳ Deadline: {deadline_str}\n"
            f"🔗 {b['link']}\n\n"
        )

    await update.message.reply_text(text.strip())
