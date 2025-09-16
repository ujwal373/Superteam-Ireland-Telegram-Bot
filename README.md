# 🤖 Superteam Ireland Telegram Bot  

A **community-first Telegram bot** built for Superteam Ireland.  
It lives in groups and DMs, helping members stay updated with **events, bounties, FAQs, and daily digests.**  

---

## ✨ Features  

### 🔹 Q&A Assistant  
- Ask `/faq <question>` in chat.  
- Powered by **Gemini AI** + Markdown knowledge base.  
- Answers include light Irish flair ☘️ (but not spammy greetings).  

### 🔹 Events  
- Use `/events` to see upcoming Superteam Ireland events.  
- Data pulled directly from **Luma iCal feed**.  

### 🔹 Bounties  
- Use `/bounties` to list open **Superteam Earn bounties** filtered for Ireland.  
- Shows **title, reward, deadline, and direct link**.  

### 🔹 Alerts & Subscriptions  
- `/subscribe` → get DM alerts for new bounties and events.  
- `/unsubscribe` → stop alerts anytime.  
- New bounties & events are auto-notified.  

### 🔹 Morning Digest  
- Auto-posts daily at **8 AM (configurable)**.  
- Includes a motivational opener (**Gemini-generated**),  
  plus the next event and up to 3 open bounties.  

### 🔹 Commands in Groups  
- `/help` → shows available commands.  
- Bot replies to **mentions only** (e.g. `@SuperteamIrelandBot how to join?`).  

---

## 🛠️ Setup  

### 1. Clone the Repo  
```bash
git clone https://github.com/<your-username>/<repo>.git
cd <repo>
```

### 2. Install Dependencies  
```bash
pip install -r requirements.txt
```

### 3. Environment Variables  
Create a `.env` file in the project root:  
```env
TELEGRAM_TOKEN=your-telegram-bot-token
GEMINI_API_KEY=your-gemini-api-key
```

⚠️ Make sure `.env` is added to `.gitignore` (already included).  

### 4. Config File  
`config.yaml` contains feeds & schedule settings:  
```yaml
feeds:
  bounties: "https://earn.superteam.fun/api/bounties?search=ireland&status=OPEN"
  events: "https://api2.luma.com/ics/get?entity=calendar&id=cal-qfk26kVBexCBTh7"

schedule:
  bounty_check_minutes: 10
```

### 5. Run Locally  
```bash
python bot.py
```

---

## 🚀 Deployment on Render  

1. Push this repo to GitHub.  
2. Create a new **Web Service** on [Render](https://render.com/).  
3. Select **Python 3** environment.  
4. Add `.env` variables in **Render > Environment > Secret Files**.  
5. Add this as the **Start Command**:  
   ```bash
   python bot.py
   ```  
6. Deploy → your bot runs **24/7 🎉**  

---

## 📂 Project Structure  

```
.
├── bot.py              # Main entrypoint
├── config.yaml         # Configurable feeds & schedule
├── .env                # Secrets (ignored by git)
├── .gitignore          
├── requirements.txt    
├── handlers/           # Handlers for each command
│   ├── faq.py
│   ├── events.py
│   ├── bounties.py
│   └── alerts.py
└── faq/                # Knowledge base in Markdown
    ├── join.md
    ├── opportunities.md
    ├── meetups.md
    ├── talent-hub.md
    ├── buildstation.md
    └── colosseum.md
```

---

## 🤝 Contribution  

PRs and issues are welcome!  
If you’d like to extend this bot (e.g. custom NLP, better UI, multi-region bounties) — **fork it, build it, and tag us.**  

---

## 💡 Credits  

- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)  
- [Gemini API](https://ai.google.dev/) for NLP  
- [Luma](https://lu.ma/) + [Superteam Earn](https://earn.superteam.fun/) feeds  

---

## 🟢 Live Bot Handle  

👉 [@SuperteamIrelandBot](https://t.me/SuperteamIrelandBot)  

☘️ *Small Country, Big at Heart — Powered by Solana, Web3, and community.*  

---

## 👤 Author  

**Ujwal Mojidra**  
📧 Email: [ujwal.mojidra@gmail.com](mailto:ujwal.mojidra@gmail.com)  
🔗 LinkedIn: [linkedin.com/in/ujwalmojidra](https://www.linkedin.com/in/ujwalmojidra/)  
