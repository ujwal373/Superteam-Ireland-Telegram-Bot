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

## 🚀 Deployment on Google Cloud VM  

We deployed this bot on **Google Cloud Compute Engine**, using free monthly credits.  
Follow these steps if you want to replicate:  

1. **Push this repo to GitHub**  
   Make sure your `.env` file is ignored via `.gitignore`.  

2. **Create a Compute Engine VM** on [Google Cloud](https://cloud.google.com/compute)  
   - OS: Ubuntu 22.04 LTS (recommended)  
   - Machine type: `e2-micro` (eligible for free tier / credits)  
   - Allow HTTP/HTTPS traffic  

3. **SSH into your VM** from Google Cloud Console  

4. **Install dependencies**  
   ```bash
   sudo apt update && sudo apt install -y python3 python3-pip git
5. **Clone your GitHub repo**
    ``` bash
    git clone https://github.com/your-username/superteam-ireland-bot.git
    cd superteam-ireland-bot
6. **Set up environment variables**
    Copy your `.env` file (contains `TELEGRAM_TOKEN`, `GEMINI_API_KEY`, etc.) into the VM.
    You can upload it manually or create it directly in the VM:
   ```bash
   nano .env   
7. **Install Python requirements**
   ```bash
    pip install -r requirements.txt
8. **Run the bot**
   ```bash
    python bot.py
9. **Keep it running in the background (so it doesn’t stop when you close SSH)**
    Option A — use `tmux`:
   ```bash
   sudo apt install tmux
   tmux new -s bot
   python bot.py
(Detach with Ctrl+B then D, reattach with tmux attach -t bot)
    Option B — use `pm2` (process manager):
  ```bash
    pip install pm2
    pm2 start bot.py --interpreter=python3
    pm2 startup
    pm2 save
``` 

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
