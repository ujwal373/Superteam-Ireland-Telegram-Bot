import os
import re
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import httpx

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# OpenAI config
# ──────────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ──────────────────────────────────────────────────────────────────────────────
# Load Knowledge Base (Markdown files under ./faq/)
# ──────────────────────────────────────────────────────────────────────────────
FAQ_DIR = Path("faq")
FAQ_CONTEXT = {}

md_files = sorted(FAQ_DIR.glob("*.md"), key=lambda p: p.name.lower())
for md_file in md_files:
    title = md_file.stem.replace("-", " ").title()
    FAQ_CONTEXT[title] = md_file.read_text(encoding="utf-8")

def build_kb_text() -> str:
    parts = []
    # Ensure deterministic ordering; put 00_basics.md first naturally if named like that
    for title, txt in FAQ_CONTEXT.items():
        rendered = md_to_safe_html(txt)
        # Make section title bold, then rendered content
        parts.append(f"<b>{html.escape(title)}</b>\n{rendered}")
    # Separate sections with a clear delimiter
    return "\n\n— — —\n\n".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# Telegram HTML sanitizer (allow only <b> <i> <u> <s> <a> <code> <pre>)
# ──────────────────────────────────────────────────────────────────────────────
_BR_TAG = re.compile(r'<br\s*/?>', re.I)
_UNSUPPORTED_TAGS = re.compile(
    r'</?(?:ul|ol|li|span|strong|em|ins|del|strike|tg-spoiler|img|table|tr|td|th|h[1-6]|div|p|blockquote|hr|sup|sub)[^>]*>',
    re.I,
)
# Remove attributes in allowed tags except href in <a>
_ALLOWED_TAG_ATTRS = re.compile(r'<(b|i|u|s|code|pre)(\s+[^>]*)?>', re.I)
_A_TAG_CLEAN = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>', re.I)

def sanitize_for_telegram_html(s: str) -> str:
    if not s:
        return s
    s = s.replace("&nbsp;", " ")
    s = _BR_TAG.sub("\n", s)           # convert <br> to newline
    s = _UNSUPPORTED_TAGS.sub("", s)   # drop unsupported tags entirely
    # Clean allowed tags to remove attributes (Telegram dislikes many attrs)
    s = _ALLOWED_TAG_ATTRS.sub(lambda m: f"<{m.group(1).lower()}>", s)
    s = _A_TAG_CLEAN.sub(lambda m: f'<a href="{m.group(1)}">', s)
    # Collapse 3+ newlines to max 2 for neatness
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s

import html, re

# Convert a subset of Markdown to Telegram-safe HTML (<b> <i> <code> <a>) + newline bullets.
_MD_IMG = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
_MD_LINK = re.compile(r'\[([^\]]+)\]\((https?://[^)]+)\)')
_MD_CODE = re.compile(r'`([^`]+)`')
_MD_BOLD = re.compile(r'(\*\*|__)(.*?)\1', re.DOTALL)
# italics: *text* or _text_ (simple, line-scoped)
_MD_ITAL = re.compile(r'(?:(?<!\*)\*(?!\*))([^*\n]+?)(?<!\*)\*(?!\*)|_([^_\n]+?)_', re.DOTALL)
_MD_H = re.compile(r'^\s{0,3}#{1,6}\s*(.+)$', re.M)
_MD_UL = re.compile(r'^\s*[-*]\s+', re.M)
_MD_OL = re.compile(r'^\s*\d+\.\s+', re.M)
_MD_HR = re.compile(r'^\s{0,3}(-{3,}|\*{3,}|_{3,})\s*$', re.M)

def md_to_safe_html(md: str) -> str:
    if not md:
        return ""

    # Escape raw HTML first
    s = html.escape(md)

    # Images → keep alt text only
    s = _MD_IMG.sub(lambda m: m.group(1), s)
    # Links → <a href="...">text</a>
    s = _MD_LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    # Inline code
    s = _MD_CODE.sub(lambda m: f"<code>{m.group(1)}</code>", s)
    # Bold
    s = _MD_BOLD.sub(lambda m: f"<b>{m.group(2)}</b>", s)
    # Italic (two-alternative groups)
    def ital_repl(m):
        txt = m.group(1) or m.group(2) or ""
        return f"<i>{txt}</i>"
    s = _MD_ITAL.sub(ital_repl, s)
    # Headings → bold line
    s = _MD_H.sub(lambda m: f"<b>{m.group(1)}</b>", s)
    # Lists → bullet prefix "• "
    s = _MD_UL.sub("• ", s)
    s = _MD_OL.sub("• ", s)
    # Horizontal rules → blank line
    s = _MD_HR.sub("\n", s)

    # Normalize newlines
    s = re.sub(r'\r\n?', '\n', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s

# ──────────────────────────────────────────────────────────────────────────────
# Friendly small-talk: allow greetings ONLY (no knowledge claims)
# ──────────────────────────────────────────────────────────────────────────────
GREETING_RE = re.compile(r"\b(hi|hello|hey|howdy|gm|good\s+(morning|evening|afternoon))\b", re.I)

def greeting_reply_html() -> str:
    return (
        "👋 <b>Hey there!</b>\n"
        "I can answer from our Superteam Ireland knowledge base. "
        "Please start your question with <code>/faq</code> so I can help.\n"
        "Try one of these to begin:\n"
        "• <code>/faq how to join Superteam Ireland</code>\n"
        "• <code>/faq upcoming meetups</code>\n"
        "• <code>/faq bounties</code>\n"
        "☘️ <i>Ask away — I’ve got your back.</i>"
    )

# ──────────────────────────────────────────────────────────────────────────────
# Out-of-scope refusal (exact HTML used when KB can’t answer)
# ──────────────────────────────────────────────────────────────────────────────
FALLBACK_REFUSAL_HTML = (
    "🤖 <b>Out of my league (for now)</b> ☘️\n"
    "Sorry, the query you asked is outside my current knowledge base and training scope.\n"
    "My developer team has me on a strict Superteam-Ireland FAQ diet while I’m still learning.\n"
    'To meet the grown-ups on the team, please visit the '
    '<a href="https://bento.me/superteamie">Superteam Ireland Hub</a> — '
    "I hope you’ll find your answer there. If not, nudge me again and I’ll flag it to the crew. 🙏"
)

# ──────────────────────────────────────────────────────────────────────────────
# Prompt builder: strict KB-first policy, HTML-only formatting
# ──────────────────────────────────────────────────────────────────────────────
def build_messages_html(context_text: str, question: str):
    """
    KB-first, Telegram-safe HTML, human tone, no verbatim dumps.
    Small talk allowed; otherwise answer only from Context.
    """
    system_msg = (
        "You are the Superteam Ireland assistant.\n"
        "FORMAT:\n"
        "- Use ONLY Telegram-safe HTML: <b>, <i>, <u>, <s>, <a>, <code>, <pre>.\n"
        "- Use newlines for breaks; bullets start with '• '.\n"
        "- No Markdown. No <br>/<ul>/<ol>/<li>. No tables/images."
    )

    user_msg = (
        # Policy
        "PRIMARY RULE:\n"
        "Answer ONLY using the <b>Context</b> below. If the Context lacks what is needed, "
        "reply EXACTLY with the provided refusal HTML (do not improvise).\n\n"

        # Human touch + paraphrase rules
        "STYLE & TONE (for non-greeting answers):\n"
        "- Write to the user directly (\"you\").\n"
        "- Paraphrase the Context in your own words; do NOT paste long passages.\n"
        "- HARD CAP: never copy more than 8 consecutive words from the Context.\n"
        "- Prefer 3–6 short lines or 3–5 bullet points starting with '• '.\n"
        "- Use one light Irish touch (☘️) only if it fits naturally.\n"
        "- If you include commands, buttons, paths, or code-ish text, wrap in <code>…</code>.\n"
        "- Only include links that already appear in the Context.\n"
        "- Do not preface with phrases like 'According to the context'.\n\n"

        # Small talk exception
        "SMALL TALK EXCEPTION (GREETINGS ONLY):\n"
        "If the user greets (hi/hello/how are you/gm), reply with a warm 1–2 line greeting, then instruct:\n"
        "\"Start your question with <code>/faq</code> so I can help.\"\n"
        "Show exactly 2–3 example lines, and each MUST begin with <code>/faq</code>. Example patterns:\n"
        "• <code>/faq how to join Superteam Ireland</code>\n"
        "• <code>/faq upcoming meetups</code>\n"
        "• <code>/faq bounties</code>\n"
        "Do NOT make knowledge claims in the greeting and do NOT show commands without the /faq prefix.\n\n"

        # Refusal (use exactly this if out-of-KB)
        "INSUFFICIENT CONTEXT → Use this HTML verbatim:\n\n"
        f"{FALLBACK_REFUSAL_HTML}\n\n"

        # Inputs
        f"<b>Context:</b>\n{context_text}\n\n"
        f"<b>Question:</b> {question}\n\n"
        "<b>Answer:</b>"
    )
    return system_msg, user_msg

# ──────────────────────────────────────────────────────────────────────────────
# /faq command handler
# ──────────────────────────────────────────────────────────────────────────────
async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # No args → usage help
    if not context.args:
        topics = [
            "🚀 <b>BuildStation</b> — co-working & build sessions",
            "🏛️ <b>Colosseum</b> — pitch & feedback arena",
            "🤝 <b>Join</b> — how to become part of Superteam",
            "🎉 <b>Meetups</b> — upcoming community events",
            "💼 <b>Opportunities</b> — bounties & grants",
            "☕ <b>Talent Hub</b> — weekly Friday builder meetups",
        ]
        await update.message.reply_text(
            "<b>How to use /faq</b> ❓\n"
            "Type <i>/faq</i> followed by your question.\n\n"
            "👉 Example: <code>/faq How do I join Superteam Ireland?</code>\n\n"
            "<b>Available topics:</b>\n" + "\n".join(topics),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    question = " ".join(context.args).strip()

    # Allow friendly greeting without touching the KB
    if GREETING_RE.search(question):
        msg = sanitize_for_telegram_html(greeting_reply_html())
        await update.message.reply_text(
            msg,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    await update.message.reply_text("💡 Thinking…", parse_mode="HTML")

    # Guard: ensure API key exists
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set.")
        await update.message.reply_text(
            "⚠️ OpenAI model is not configured yet. Please try again later.",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    # Build strict KB prompt
    context_text = build_kb_text()
    system_msg, user_msg = build_messages_html(context_text, question)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 700,
                    "frequency_penalty": 0.2,   # reduces copy-ish repetition
                    "presence_penalty": 0.1     # nudges variety a bit
                },
            )
            resp.raise_for_status()
            data = resp.json()
            answer = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

        # Sanitize for Telegram and send
        if not answer:
            answer = FALLBACK_REFUSAL_HTML
        answer = sanitize_for_telegram_html(answer)

        await update.message.reply_text(
            answer,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except Exception as e:
        logger.error(f"OpenAI FAQ error: {e}")
        await update.message.reply_text(
            "⚠️ Sorry, I couldn't fetch an answer right now.",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
