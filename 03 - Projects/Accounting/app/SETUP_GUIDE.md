# Quick Setup Guide

## ⚡ 5-Minute Setup

### Step 1: Install Node.js
1. Go to https://nodejs.org/
2. Download the LTS version (left button)
3. Run the installer
4. Click "Next" through everything (use default settings)
5. Restart your computer

### Step 2: Extract Files
1. Extract the `financial-tracker` folder to your Desktop
2. You should see files like `bot.js`, `database.js`, etc.

### Step 3: Install Dependencies
1. **Windows**: 
   - Right-click in the folder while holding Shift
   - Click "Open PowerShell window here" or "Open command window here"
   
2. **Mac**: 
   - Open Terminal
   - Type: `cd ~/Desktop/financial-tracker`
   - Press Enter

3. **In the terminal/command prompt, type:**
   ```bash
   npm install
   ```
   
4. Wait 1-2 minutes while it downloads everything
5. You should see a lot of text scroll by - this is normal!

### Step 4: Get Your Telegram Bot Token
1. Open Telegram on your phone or computer
2. Search for: `@BotFather` (the official one with a blue checkmark)
3. Send this message: `/newbot`
4. BotFather asks for a name: Type `My Finance Tracker`
5. BotFather asks for a username: Type `my_finance_tracker_bot` (or any name ending in "_bot")
6. BotFather sends you a TOKEN - it looks like: `123456789:ABCdefGHI...`
7. **Copy this token** (long-press on phone, or Ctrl+C on computer)

### Step 5: Add Your Token
1. In the `financial-tracker` folder, find `.env.example`
2. Copy it and rename the copy to `.env` (just `.env`, remove `.example`)
3. Open `.env` with Notepad (Windows) or TextEdit (Mac)
4. Replace the fake token with your real token:
   ```
   TELEGRAM_BOT_TOKEN=paste_your_real_token_here
   ```
5. Save the file

### Step 6: Initialize Database
In the terminal/command prompt, type:
```bash
npm run init-db
```

You should see: "Database initialized successfully!"

### Step 7: Start the Bot
```bash
npm start
```

You should see:
```
Bot is running...
✅ Bot is ready!
💬 Send /start to your bot to begin
```

**🎉 Done! Your bot is running!**

### Step 8: Test Your Bot
1. Open Telegram
2. Search for your bot's username (e.g., `my_finance_tracker_bot`)
3. Click Start
4. Send: `/start`
5. Bot should respond with a welcome message!

---

## 🚀 Running the Dashboards

### Personal Dashboard

**Open a NEW terminal/command prompt** (keep the bot running in the first one!)

```bash
npm run dashboard-personal
```

Then open your browser to: **http://localhost:3000**

### Business Dashboard

**Open ANOTHER NEW terminal/command prompt**

```bash
npm run dashboard-business
```

Then open your browser to: **http://localhost:3001**

---

## 📝 Quick Tips

### Stopping Everything
- Bot: Press `Ctrl+C` in its terminal
- Dashboards: Press `Ctrl+C` in their terminals
- Or just close the terminal windows

### Starting Everything Again
1. Open terminal in the `financial-tracker` folder
2. Run `npm start` for bot
3. Open new terminals for dashboards

### If Something Goes Wrong
1. Close everything (`Ctrl+C`)
2. Delete `financial_tracker.db` file
3. Run `npm run init-db` again
4. Start the bot again

---

## 🎯 Using the System

### Adding Personal Transactions
1. Open Telegram
2. Message your bot: `/personal`
3. Follow the prompts:
   - Date: Type `today` or `2024-03-15`
   - Amount: Type `45.50` (positive for income, negative like `-45.50` for expenses)
   - Category: Click a button
   - Payment: Click a button
   - Description: Type what it was for

### Adding Business Transactions
1. Message your bot: `/business`
2. Follow the prompts:
   - Type: Click Income or Expense
   - Category: Click appropriate category
   - Date: Type `today` or date
   - Amount: Type amount (GST calculated automatically!)
   - ABN: If expense >$75, confirm if ABN provided
   - Description: Type details

### Viewing Summaries
- Type `/summary` in Telegram for quick overview
- Open dashboards in browser for detailed reports
- Personal: http://localhost:3000
- Business: http://localhost:3001

---

## 🆘 Troubleshooting

### "npm: command not found"
→ Node.js not installed properly. Reinstall from nodejs.org

### "TELEGRAM_BOT_TOKEN not found"
→ Make sure your `.env` file exists and has the token

### Bot doesn't respond
→ Check if bot is running (terminal shows "Bot is running...")
→ Make sure you're messaging the correct bot

### Dashboard won't load
→ Make sure dashboard is running in its own terminal
→ Try a different browser (Chrome or Firefox)
→ Check you're using the right port (3000 or 3001)

### Database errors
→ Close everything
→ Delete `financial_tracker.db`
→ Run `npm run init-db`
→ Start again

---

## 🔒 Security

**Important:**
1. **Never share your bot token** - it's like a password
2. **Never commit `.env` to GitHub** - it contains your token
3. **Backup your `.db` file regularly** - it contains all your data
4. Keep your `.db` file safe - it has all your financial records

---

## 💾 Backing Up Your Data

**Every week, do this:**
1. Find `financial_tracker.db` in your project folder
2. Copy it
3. Rename to `backup_2024-03-15.db` (use today's date)
4. Store somewhere safe (Google Drive, external drive, etc.)

**To restore:**
1. Delete current `financial_tracker.db`
2. Copy your backup file
3. Rename it to `financial_tracker.db`
4. Restart bot

---

## 📞 Need Help?

### Check the main README.md for:
- Detailed explanations
- Australian tax information
- ATO compliance requirements
- Advanced features

### Common Questions

**Q: Can I use this on multiple computers?**
A: The bot works from any device with Telegram, but the database is only on one computer. You'd need to share the database file.

**Q: What if I make a mistake?**
A: Currently, you can't edit from the bot, but you can delete the transaction from the database directly or wait for future updates.

**Q: Is my data private?**
A: Yes! Everything is stored on your computer. The bot only talks to you on Telegram.

**Q: Do I need internet?**
A: Yes, for the Telegram bot. But dashboards work offline once data is in the database.

---

**You're all set! Happy tracking! 🎉**
