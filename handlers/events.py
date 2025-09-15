import logging
import requests
from pathlib import Path
import yaml
from datetime import datetime, timezone
from icalendar import Calendar
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# Load config
CONFIG = yaml.safe_load(Path("config.yaml").read_text())


def fetch_events():
    url = CONFIG["feeds"]["events"]
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        gcal = Calendar.from_ical(r.text)

        now = datetime.now(timezone.utc)
        events = []
        for component in gcal.walk():
            if component.name == "VEVENT":
                start = component.get("DTSTART").dt
                if start >= now:
                    title = str(component.get("SUMMARY"))

                    # Try URL, then ATTACH, then try to parse DESCRIPTION
                    link = str(component.get("URL", "")) or \
                           str(component.get("ATTACH", "")) or ""

                    if not link:
                        desc = str(component.get("DESCRIPTION", ""))
                        # crude fallback: find http(s) links inside description
                        import re
                        match = re.search(r"https?://\S+", desc)
                        if match:
                            link = match.group(0)

                    if not link:
                        link = "No link available"

                    date = start.strftime("%Y-%m-%d %H:%M")
                    events.append({
                        "title": title,
                        "date": date,
                        "link": link
                    })

        events.sort(key=lambda e: e["date"])
        return events[:5] or [{"title": "No upcoming events", "date": "", "link": ""}]
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return [{"title": "⚠️ Could not fetch events", "date": "", "link": ""}]


# --- Telegram handler ---
async def events(update, context):
    """
    Telegram command handler for /events
    """
    event_list = fetch_events()
    if not event_list:
        await update.message.reply_text("No upcoming events found.")
        return

    text = ""
    for e in event_list:
        link = e['link']
        if link and link.startswith("http"):
            link_text = f"[Click here]({link})"
        else:
            link_text = "No link available"

        text += (
            f"📌 *{e['title']}*\n"
            f"📅 {e['date']}\n"
            f"🔗 {link_text}\n\n"
        )

    await update.message.reply_text(
        text.strip(),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

