# Financial Tracker Bot - Complete Guide

A comprehensive financial tracking system for Australian PTY LTD construction/painting companies with:
- Telegram Bot for easy data entry
- Personal Finance Dashboard
- Business/ATO Compliance Dashboard

## 📋 Table of Contents
- [Installation](#installation)
- [Getting Your Telegram Bot Token](#getting-telegram-bot-token)
- [Running the System](#running-the-system)
- [Using the Telegram Bot](#using-the-telegram-bot)
- [Using the Dashboards](#using-the-dashboards)
- [Database Structure](#database-structure)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Installation

### Prerequisites
- **Node.js** (version 14 or higher) - [Download here](https://nodejs.org/)
- **npm** (comes with Node.js)
- A computer (Windows, Mac, or Linux)
- A Telegram account

### Step-by-Step Installation

#### 1. Install Node.js
- Download from https://nodejs.org/
- Run the installer
- Verify installation by opening terminal/command prompt and typing:
  ```bash
  node --version
  npm --version
  ```
  You should see version numbers (e.g., v18.0.0)

#### 2. Download/Extract Project Files
- Extract the `financial-tracker` folder to a location you can find (e.g., Desktop or Documents)

#### 3. Install Dependencies
Open terminal/command prompt and navigate to the project folder:

**Windows:**
```cmd
cd C:\Users\YourName\Desktop\financial-tracker
```

**Mac/Linux:**
```bash
cd ~/Desktop/financial-tracker
```

Then install all required packages:
```bash
npm install
```

This will download all necessary software packages. It might take 1-2 minutes.

#### 4. Initialize the Database
```bash
npm run init-db
```

You should see: "Database initialized successfully!"

---

## 🤖 Getting Telegram Bot Token

### Step-by-Step Guide

1. **Open Telegram** on your phone or computer

2. **Find BotFather**
   - Search for `@BotFather` in Telegram
   - Click on the official BotFather (verified with blue checkmark)

3. **Create Your Bot**
   - Send `/newbot` to BotFather
   - BotFather will ask for a name - type: `Financial Tracker` (or any name you like)
   - BotFather will ask for a username - must end with 'bot', e.g., `myfinance_tracker_bot`
   - BotFather will send you a token (long string of numbers and letters)

4. **Copy the Token**
   - It looks like: `<REDACTED-TELEGRAM-TOKEN>0`
   - Keep this secret! Don't share it with anyone.

5. **Add Token to Project**
   - In the project folder, copy `.env.example` and rename it to `.env`
   - Open `.env` with a text editor (Notepad, TextEdit, etc.)
   - Replace the example token with your real token:
     ```
     TELEGRAM_BOT_TOKEN=<REDACTED-TELEGRAM-TOKEN>0
     ```
   - Save the file

6. **Test Your Bot**
   - In Telegram, search for your bot's username
   - Click "Start" or send `/start`
   - The bot should respond (if not running yet, see next section)

---

## ▶️ Running the System

### Start the Telegram Bot

Open terminal in the project folder and run:
```bash
npm start
```

You should see:
```
Initializing database...
Database initialized successfully!
Bot is running...
✅ Bot is ready!
💬 Send /start to your bot to begin
```

**Keep this terminal window open!** The bot runs as long as this window is open.

To stop the bot: Press `Ctrl+C` (or `Cmd+C` on Mac)

### Start the Personal Dashboard

Open a **new** terminal window (keep the bot running in the first one):
```bash
npm run dashboard-personal
```

Open your web browser and go to: `http://localhost:3000`

### Start the Business Dashboard

Open another **new** terminal window:
```bash
npm run dashboard-business
```

Open your web browser and go to: `http://localhost:3001`

---

## 💬 Using the Telegram Bot

### Quick Start

1. Open Telegram and find your bot
2. Send `/start` to see welcome message
3. Use `/personal` to add personal transactions
4. Use `/business` to add business transactions

### Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and introduction |
| `/personal` | Add a personal transaction (groceries, entertainment, etc.) |
| `/business` | Add a business transaction (materials, invoices, etc.) |
| `/summary` | View current month summary |
| `/help` | Show help and all commands |
| `/cancel` | Cancel current transaction |

### Adding a Personal Transaction

1. Send `/personal`
2. Bot guides you through 5 steps:
   - **Date**: Type date in YYYY-MM-DD format (e.g., `2024-03-15`) or type `today`
   - **Amount**: Enter amount (e.g., `45.50` or `-45.50` for expenses)
   - **Category**: Click a button (Income, Groceries, Utilities, etc.)
   - **Payment Method**: Click a button (Cash, Card, Bank Transfer, etc.)
   - **Description**: Type what it was for (e.g., "Weekly groceries at Woolworths")
3. Bot confirms and saves!

**Example Conversation:**
```
You: /personal
Bot: Step 1/5: Enter the date
You: today
Bot: Step 2/5: Enter the amount
You: -85.50
Bot: Step 3/5: Select category
[You click: Groceries]
Bot: Step 4/5: How did you pay?
[You click: Debit Card]
Bot: Step 5/5: Enter a description
You: Weekly groceries at Coles
Bot: ✅ Personal Transaction Saved!
```

### Adding a Business Transaction

1. Send `/business`
2. Bot guides you through 7 steps:
   - **Type**: Click Income or Expense
   - **Category**: Click appropriate category
   - **Date**: Type date or `today`
   - **Amount**: Enter amount (GST calculated automatically)
   - **ABN**: If expense >$75, confirm if ABN was provided
   - **Description**: Type details (e.g., "Paint supplies from Bunnings")
3. Bot shows full details including GST!

**Important for ATO Compliance:**
- GST is automatically calculated (10%)
- ABN tracking for payments over $75
- All data stored for BAS reporting

---

## 📊 Using the Dashboards

### Personal Dashboard (http://localhost:3000)

**Features:**
- Monthly income vs expenses summary
- Category breakdown with pie charts
- 6-month spending trends
- Search and filter transactions
- Export to CSV for Excel

**How to Use:**
1. Open browser to `http://localhost:3000`
2. Dashboard automatically loads current month
3. Use filters to view different months
4. Click "Export to CSV" to download data

### Business Dashboard (http://localhost:3001)

**Features:**
- BAS (Business Activity Statement) reporting
- Profit & Loss statements
- Compliance alerts
- GST calculations
- Quarterly summaries

**How to Use:**
1. Open browser to `http://localhost:3001`
2. Select financial year and quarter
3. View BAS fields (G1, G10, G11, etc.)
4. Check compliance alerts
5. Export reports for accountant

**BAS Fields Explained:**
- **G1**: Total sales (including GST)
- **G10**: Capital purchases (equipment)
- **G11**: Non-capital purchases (materials, supplies)
- **G18**: Total GST you paid on purchases
- **1A**: Total GST you collected on sales
- **Net GST**: Amount to pay ATO (or refund if negative)

---

## 🗄️ Database Structure

### Location
The database file is created at: `financial-tracker/financial_tracker.db`

### Tables

#### personal_transactions
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique ID |
| date | TEXT | Date (YYYY-MM-DD) |
| amount | REAL | Amount in dollars |
| category | TEXT | Transaction category |
| description | TEXT | What it was for |
| payment_method | TEXT | How you paid |
| created_at | DATETIME | When record was created |

#### business_transactions
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique ID |
| date | TEXT | Transaction date |
| amount | REAL | Amount (excluding GST) |
| type | TEXT | Income or Expense |
| category | TEXT | Business category |
| description | TEXT | Transaction details |
| gst_amount | REAL | GST amount (10%) |
| has_abn | INTEGER | 1 if ABN provided, 0 if not |
| receipt_url | TEXT | Link to receipt (future) |
| created_at | DATETIME | When created |

### Backup Your Data

**Important!** Regularly backup your database file:

1. Find `financial_tracker.db` in the project folder
2. Copy it to a safe location (Google Drive, external drive, etc.)
3. Rename with date (e.g., `financial_tracker_backup_2024-03-15.db`)

To restore: Replace the current `.db` file with your backup.

---

## 🔧 Troubleshooting

### Bot Not Responding

**Problem:** Bot doesn't reply in Telegram

**Solutions:**
1. Check if bot is running (terminal should show "Bot is running...")
2. Verify token in `.env` file is correct
3. Make sure you're messaging the correct bot username
4. Try restarting: `Ctrl+C` then `npm start` again

### "TELEGRAM_BOT_TOKEN not found"

**Problem:** Error when starting bot

**Solution:**
1. Make sure you have a `.env` file (not `.env.example`)
2. Open `.env` and check token is there
3. No spaces around the `=` sign
4. Token should be on one line

### Database Errors

**Problem:** "Database locked" or "SQLITE_ERROR"

**Solutions:**
1. Close all dashboards and bot
2. Delete `financial_tracker.db`
3. Run `npm run init-db` again
4. Restart bot

### Dashboard Won't Load

**Problem:** Browser shows "Can't connect" or "Connection refused"

**Solutions:**
1. Check terminal - dashboard should be running
2. Make sure you're using correct port:
   - Personal: http://localhost:3000
   - Business: http://localhost:3001
3. Try different browser (Chrome, Firefox)
4. Restart dashboard

### Port Already in Use

**Problem:** "Port 3000 already in use"

**Solutions:**
1. Close other programs using that port
2. Edit dashboard file to use different port (e.g., 3002)
3. Or kill the process using the port

**Windows:**
```cmd
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F
```

**Mac/Linux:**
```bash
lsof -ti:3000 | xargs kill
```

### GST Calculation Wrong

**Problem:** GST amount seems incorrect

**Explanation:**
- GST is 10% of the amount EXCLUDING GST
- Example: $100 item → $10 GST → $110 total
- If you paid $110 total, enter $100 as amount (bot calculates $10 GST)

### Wrong Financial Year

**Problem:** Transactions showing in wrong year

**Explanation:**
- Australian financial year: July 1 - June 30
- Example: July 2024 - June 2025 = FY 2024-25
- Q1: Jul-Sep, Q2: Oct-Dec, Q3: Jan-Mar, Q4: Apr-Jun

---

## 📞 Getting Help

### Common Questions

**Q: Can I edit a transaction after saving?**
A: Not yet in the bot, but you can edit directly in database or wait for next update.

**Q: Can I attach receipts?**
A: Future feature! Database has field ready for receipt URLs.

**Q: How do I share data with my accountant?**
A: Use the Export feature in dashboards to create CSV files.

**Q: Is my data secure?**
A: Data is stored locally on your computer. Keep backups safe.

**Q: Can I use this on multiple devices?**
A: Bot works from any device with Telegram, but database is on one computer.

### Need More Help?

1. Check error messages in terminal - they often explain the problem
2. Make sure all dependencies installed: `npm install`
3. Try restarting everything
4. Check Node.js version: `node --version` (should be 14+)

---

## 🎯 Tips for Success

### Daily Use
1. Add transactions immediately (don't wait!)
2. Use descriptive descriptions for business expenses
3. Keep receipts for business transactions
4. Check `/summary` regularly

### Monthly Tasks
1. Review dashboards
2. Export data for records
3. Backup database
4. Check compliance alerts

### Quarterly Tasks (Business)
1. Generate BAS report
2. Review profit & loss
3. Prepare for accountant/ATO
4. Check all ABN recordings

### Before Tax Time
1. Export all business transactions
2. Generate annual reports
3. Review all flagged items
4. Organize receipts
5. Consult accountant

---

## 📚 Australian Tax Information

### Key Dates
- **Financial Year**: July 1 - June 30
- **BAS Due Dates**: 
  - Q1 (Jul-Sep): Due Oct 28
  - Q2 (Oct-Dec): Due Feb 28
  - Q3 (Jan-Mar): Due Apr 28
  - Q4 (Apr-Jun): Due Jul 28

### Important Thresholds
- **ABN Required**: Payments over $75
- **Cash Reporting**: Transactions over $10,000
- **GST Registration**: Usually required for businesses

### What to Track
✅ All business income (with GST)
✅ All business expenses (with GST)
✅ ABN for suppliers
✅ Asset purchases for depreciation
✅ Vehicle expenses
✅ Insurance payments

---

## 🔐 Security Best Practices

1. **Never share your bot token**
2. **Backup your database regularly**
3. **Don't commit `.env` file to GitHub**
4. **Keep your Node.js updated**
5. **Store receipts securely**

---

## 📝 Version History

**Version 1.0** (Current)
- Basic Telegram bot with personal & business tracking
- SQLite database
- Personal dashboard
- Business/ATO dashboard
- BAS reporting
- Compliance alerts

**Planned Features:**
- Receipt photo upload
- Edit/delete transactions from bot
- Multi-user support
- Automatic backups
- Mobile-friendly dashboards
- Project tracking
- Invoice generation

---

## 📄 License

This project is for personal/business use. Consult with a qualified accountant for tax advice.

---

**Happy Tracking! 🎉**

Remember: This tool helps organize your data, but always consult with a qualified accountant or tax professional for Australian tax compliance.
