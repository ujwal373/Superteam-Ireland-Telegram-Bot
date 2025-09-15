import os
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import google.generativeai as genai
import httpx 

logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-1.5-flash"

# Load all markdown files into context
FAQ_DIR = Path("faq")
FAQ_CONTEXT = {}
for md_file in FAQ_DIR.glob("*.md"):
    title = md_file.stem.replace("-", " ").title()
    FAQ_CONTEXT[title] = md_file.read_text(encoding="utf-8")

# --- Escape helper for Telegram MarkdownV2 ---
def escape_markdown(text: str) -> str:
    """Escape Telegram MarkdownV2 special chars in AI responses."""
    escape_chars = r"_*[]()~`>#+-=|{}.!<>"
    for ch in escape_chars:
        text = text.replace(ch, f"\\{ch}")
    return text


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        topics = [
            "🚀 *BuildStation* — co-working & build sessions",
            "🏛️ *Colosseum* — pitch & feedback arena",
            "🤝 *Join* — how to become part of Superteam",
            "🎉 *Meetups* — upcoming community events",
            "💼 *Opportunities* — bounties & grants",
            "☕ *Talent Hub* — weekly Friday builder meetups",
        ]
        await update.message.reply_text(
            "*How to use FAQ* ❓\n"
            "_Ask me a question after typing_ `/faq`.\n\n"
            "👉 Example: `/faq How do I join Superteam Ireland?`\n\n"
            "*Available topics:*\n" + "\n".join(topics),
            parse_mode="Markdown"
        )
        return

    question = " ".join(context.args)
    await update.message.reply_text("💡 Thinking…")

    try:
        # Build context dynamically from markdowns
        context_text = "\n\n".join(FAQ_CONTEXT.values())

        prompt = (
            "You are a helpful assistant for *Superteam Ireland*'s Telegram community.\n"
            "Answer ONLY using the context provided below.\n\n"
            "Guidelines:\n"
            "- DO NOT always start with the same phrase. Avoid using 'Top o' the mornin'' or repetitive greetings.\n"
            "- Use clear, friendly language like a community guide.\n"
            "- Occasionally add light Irish flavour (☘️, witty phrasing), but vary it.\n"
            "- Format answers with Telegram MarkdownV2: bold, italics, bullet points, and links.\n"
            "- If the context does not contain the answer, reply with:\n"
            "'⚠️ Sorry, I don't know that yet\\. Please check [Superteam Ireland Hub](https://bento.me/superteamie).'\n\n"
            f"*Context:*\n{context_text}\n\n"
            f"*Question:* {question}\n\n*Answer:*"
        )

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            response.raise_for_status()
            data = response.json()
            answer = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "🤔 Sorry, I couldn't answer that.")
            )

        safe_answer = escape_markdown(answer)

        await update.message.reply_text(
            safe_answer,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Gemini FAQ error: {e}")
        await update.message.reply_text("⚠️ Sorry, I couldn't fetch an answer right now.")
