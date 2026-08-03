// bot.js
// Main Telegram Bot for Financial Tracking
// This bot guides users through adding personal and business transactions

const TelegramBot = require('node-telegram-bot-api');
const db = require('./database');
require('dotenv').config();

// Initialize database on startup
db.initializeDatabase();

// Get bot token from environment variable (we'll set this up in .env file)
const token = process.env.TELEGRAM_BOT_TOKEN;

if (!token) {
  console.error('ERROR: TELEGRAM_BOT_TOKEN not found in .env file!');
  console.log('Please create a .env file with your bot token:');
  console.log('TELEGRAM_BOT_TOKEN=your_token_here');
  process.exit(1);
}

// Create bot instance with polling (constantly checks for new messages)
const bot = new TelegramBot(token, { polling: true });

console.log('Bot is running...');

// Store user states (what step they're on in adding a transaction)
// This is needed because Telegram bots are stateless - we need to remember context
const userStates = {};

// Categories for personal transactions
const PERSONAL_CATEGORIES = [
  'Income', 'Groceries', 'Utilities', 'Entertainment', 'Transport', 'Other'
];

// Payment methods
const PAYMENT_METHODS = [
  'Cash', 'Debit Card', 'Credit Card', 'Bank Transfer', 'PayPal', 'Other'
];

// Business income categories
const BUSINESS_INCOME_CATEGORIES = [
  'Project Payment', 'Deposit', 'Retention Release'
];

// Business expense categories
const BUSINESS_EXPENSE_CATEGORIES = [
  'Materials', 'Subcontractors', 'Equipment Hire', 'Vehicle', 'Fuel',
  'Insurance', 'Marketing', 'Office Supplies', 'Professional Fees', 'Other'
];

/**
 * HELPER FUNCTIONS
 */

// Create inline keyboard buttons from an array of options
function createInlineKeyboard(options, columns = 2) {
  const keyboard = [];
  for (let i = 0; i < options.length; i += columns) {
    const row = options.slice(i, i + columns).map(option => ({
      text: option,
      callback_data: option
    }));
    keyboard.push(row);
  }
  return { inline_keyboard: keyboard };
}

// Format currency for display
function formatCurrency(amount) {
  return `$${parseFloat(amount).toFixed(2)}`;
}

// Get current date in YYYY-MM-DD format
function getCurrentDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Validate date format
function isValidDate(dateString) {
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(dateString)) return false;
  
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date);
}

/**
 * BOT COMMANDS
 */

// /start command - Welcome message
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  const welcomeMessage = `
🎉 *Welcome to Financial Tracker Bot!*

I'll help you track both personal and business finances for your construction/painting company.

📊 *Available Commands:*
/personal - Add a personal transaction
/business - Add a business transaction
/summary - View current month summary
/help - Show all commands

💡 *Quick Start:*
• Use /personal for personal expenses (groceries, entertainment, etc.)
• Use /business for company transactions (materials, invoices, etc.)
• All business transactions are ATO-compliant with automatic GST calculation

Ready to start tracking? Try /personal or /business!
  `;
  
  bot.sendMessage(chatId, welcomeMessage, { parse_mode: 'Markdown' });
});

// /help command
bot.onText(/\/help/, (msg) => {
  const chatId = msg.chat.id;
  const helpMessage = `
📖 *Help Guide*

*Commands:*
/start - Show welcome message
/personal - Add personal transaction
/business - Add business transaction  
/summary - Monthly summary
/help - Show this help message

*Personal Transactions:*
Track your personal income and expenses:
• Income, Groceries, Utilities, Entertainment, Transport, Other

*Business Transactions:*
Track company finances (ATO compliant):
• Automatically calculates 10% GST
• Tracks ABN for payments over $75
• Income: Project Payment, Deposit, Retention Release
• Expenses: Materials, Subcontractors, Equipment, Vehicle, etc.

*Tips:*
• Dates must be in YYYY-MM-DD format (e.g., 2024-03-15)
• Amounts should be numbers only (e.g., 150.50)
• You can cancel anytime by typing /cancel

*Australian Tax Info:*
• Financial year: July 1 - June 30
• GST rate: 10%
• Payments >$75 require ABN tracking
• Transactions >$10,000 flagged for reporting

Need more help? Contact your administrator.
  `;
  
  bot.sendMessage(chatId, helpMessage, { parse_mode: 'Markdown' });
});

/**
 * PERSONAL TRANSACTION FLOW
 */

// /personal command - Start personal transaction
bot.onText(/\/personal/, (msg) => {
  const chatId = msg.chat.id;
  
  // Initialize user state
  userStates[chatId] = {
    type: 'personal',
    step: 'date',
    data: {}
  };
  
  bot.sendMessage(
    chatId,
    `📝 *Adding Personal Transaction*\n\nStep 1/5: Enter the date\n\nFormat: YYYY-MM-DD (e.g., ${getCurrentDate()})\nOr type "today" for today's date`,
    { parse_mode: 'Markdown' }
  );
});

// /business command - Start business transaction
bot.onText(/\/business/, (msg) => {
  const chatId = msg.chat.id;
  
  // Initialize user state
  userStates[chatId] = {
    type: 'business',
    step: 'type',
    data: {}
  };
  
  const keyboard = createInlineKeyboard(['Income', 'Expense'], 2);
  
  bot.sendMessage(
    chatId,
    '💼 *Adding Business Transaction*\n\nStep 1/7: Is this Income or Expense?',
    {
      parse_mode: 'Markdown',
      reply_markup: keyboard
    }
  );
});

// /summary command - Show monthly summary
bot.onText(/\/summary/, async (msg) => {
  const chatId = msg.chat.id;
  
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  const monthName = now.toLocaleString('default', { month: 'long' });
  
  try {
    // Get personal summary
    const personalTransactions = db.getPersonalTransactionsByMonth(year, month);
    const personalTotal = personalTransactions.reduce((sum, t) => sum + t.amount, 0);
    const personalIncome = personalTransactions
      .filter(t => t.category === 'Income')
      .reduce((sum, t) => sum + t.amount, 0);
    const personalExpenses = personalTransactions
      .filter(t => t.category !== 'Income')
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);
    
    // Get business summary
    const businessTransactions = db.getBusinessTransactionsByMonth(year, month);
    const businessIncome = businessTransactions
      .filter(t => t.type === 'Income')
      .reduce((sum, t) => sum + t.amount, 0);
    const businessExpenses = businessTransactions
      .filter(t => t.type === 'Expense')
      .reduce((sum, t) => sum + t.amount, 0);
    const businessGST = businessTransactions
      .reduce((sum, t) => sum + (t.type === 'Income' ? t.gst_amount : -t.gst_amount), 0);
    
    const summaryMessage = `
📊 *${monthName} ${year} Summary*

*Personal Finances:*
💰 Income: ${formatCurrency(personalIncome)}
💸 Expenses: ${formatCurrency(personalExpenses)}
📈 Net: ${formatCurrency(personalIncome - personalExpenses)}
📝 Transactions: ${personalTransactions.length}

*Business Finances:*
💼 Income: ${formatCurrency(businessIncome)}
💼 Expenses: ${formatCurrency(businessExpenses)}
💼 Net Profit: ${formatCurrency(businessIncome - businessExpenses)}
🧾 GST Balance: ${formatCurrency(businessGST)}
📝 Transactions: ${businessTransactions.length}

Use the dashboards for detailed reports!
    `;
    
    bot.sendMessage(chatId, summaryMessage, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Error generating summary:', error);
    bot.sendMessage(chatId, '❌ Error generating summary. Please try again.');
  }
});

// /cancel command
bot.onText(/\/cancel/, (msg) => {
  const chatId = msg.chat.id;
  
  if (userStates[chatId]) {
    delete userStates[chatId];
    bot.sendMessage(chatId, '❌ Transaction cancelled. Type /personal or /business to start again.');
  } else {
    bot.sendMessage(chatId, 'No active transaction to cancel.');
  }
});

/**
 * HANDLE INLINE KEYBOARD CALLBACKS
 */
bot.on('callback_query', async (callbackQuery) => {
  const chatId = callbackQuery.message.chat.id;
  const data = callbackQuery.data;
  const state = userStates[chatId];
  
  // Answer the callback to remove loading state
  bot.answerCallbackQuery(callbackQuery.id);
  
  if (!state) {
    bot.sendMessage(chatId, 'Session expired. Please start again with /personal or /business');
    return;
  }
  
  // Handle different steps based on transaction type
  if (state.type === 'personal') {
    handlePersonalCallback(chatId, data, state);
  } else if (state.type === 'business') {
    handleBusinessCallback(chatId, data, state);
  }
});

/**
 * HANDLE PERSONAL TRANSACTION CALLBACKS
 */
function handlePersonalCallback(chatId, data, state) {
  if (state.step === 'category') {
    state.data.category = data;
    state.step = 'payment_method';
    
    const keyboard = createInlineKeyboard(PAYMENT_METHODS, 2);
    bot.sendMessage(
      chatId,
      `Step 4/5: How did you pay?\n\nCategory: ${data}`,
      { reply_markup: keyboard }
    );
  } else if (state.step === 'payment_method') {
    state.data.payment_method = data;
    state.step = 'description';
    
    bot.sendMessage(
      chatId,
      `Step 5/5: Enter a description\n\nExample: "Weekly groceries at Woolworths"`
    );
  }
}

/**
 * HANDLE BUSINESS TRANSACTION CALLBACKS
 */
function handleBusinessCallback(chatId, data, state) {
  if (state.step === 'type') {
    state.data.type = data;
    state.step = 'category';
    
    const categories = data === 'Income' ? BUSINESS_INCOME_CATEGORIES : BUSINESS_EXPENSE_CATEGORIES;
    const keyboard = createInlineKeyboard(categories, 2);
    
    bot.sendMessage(
      chatId,
      `Step 2/7: Select category\n\nType: ${data}`,
      { reply_markup: keyboard }
    );
  } else if (state.step === 'category') {
    state.data.category = data;
    state.step = 'date';
    
    bot.sendMessage(
      chatId,
      `Step 3/7: Enter the date\n\nFormat: YYYY-MM-DD (e.g., ${getCurrentDate()})\nOr type "today"`
    );
  } else if (state.step === 'abn') {
    state.data.has_abn = (data === 'Yes');
    state.step = 'description';
    
    bot.sendMessage(
      chatId,
      `Step 7/7: Enter a description\n\nExample: "Paint supplies from Bunnings" or "Invoice #1234 - Smith residence"`
    );
  }
}

/**
 * HANDLE TEXT MESSAGES (for data entry)
 */
bot.on('message', async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;
  
  // Ignore commands (they're handled separately)
  if (text.startsWith('/')) return;
  
  const state = userStates[chatId];
  if (!state) return;
  
  if (state.type === 'personal') {
    await handlePersonalMessage(chatId, text, state);
  } else if (state.type === 'business') {
    await handleBusinessMessage(chatId, text, state);
  }
});

/**
 * HANDLE PERSONAL TRANSACTION MESSAGES
 */
async function handlePersonalMessage(chatId, text, state) {
  try {
    if (state.step === 'date') {
      // Handle date input
      let date = text.toLowerCase() === 'today' ? getCurrentDate() : text;
      
      if (!isValidDate(date)) {
        bot.sendMessage(chatId, '❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-03-15)');
        return;
      }
      
      state.data.date = date;
      state.step = 'amount';
      
      bot.sendMessage(chatId, `Step 2/5: Enter the amount\n\nExample: 45.50 or 100\n(Use positive for income, negative for expenses like -45.50)`);
      
    } else if (state.step === 'amount') {
      // Handle amount input
      const amount = parseFloat(text);
      
      if (isNaN(amount) || amount === 0) {
        bot.sendMessage(chatId, '❌ Invalid amount. Please enter a number (e.g., 45.50)');
        return;
      }
      
      state.data.amount = amount;
      state.step = 'category';
      
      const keyboard = createInlineKeyboard(PERSONAL_CATEGORIES, 2);
      bot.sendMessage(
        chatId,
        `Step 3/5: Select category\n\nAmount: ${formatCurrency(amount)}`,
        { reply_markup: keyboard }
      );
      
    } else if (state.step === 'description') {
      // Final step - save transaction
      state.data.description = text;
      
      // Save to database
      const id = db.addPersonalTransaction(
        state.data.date,
        state.data.amount,
        state.data.category,
        state.data.description,
        state.data.payment_method
      );
      
      const confirmMessage = `
✅ *Personal Transaction Saved!*

ID: #${id}
📅 Date: ${state.data.date}
💰 Amount: ${formatCurrency(state.data.amount)}
📁 Category: ${state.data.category}
💳 Payment: ${state.data.payment_method}
📝 Description: ${state.data.description}

Add another? Use /personal or /business
      `;
      
      bot.sendMessage(chatId, confirmMessage, { parse_mode: 'Markdown' });
      
      // Clear user state
      delete userStates[chatId];
    }
  } catch (error) {
    console.error('Error handling personal message:', error);
    bot.sendMessage(chatId, '❌ Error saving transaction. Please try again or use /cancel');
  }
}

/**
 * HANDLE BUSINESS TRANSACTION MESSAGES
 */
async function handleBusinessMessage(chatId, text, state) {
  try {
    if (state.step === 'date') {
      // Handle date input
      let date = text.toLowerCase() === 'today' ? getCurrentDate() : text;
      
      if (!isValidDate(date)) {
        bot.sendMessage(chatId, '❌ Invalid date format. Please use YYYY-MM-DD');
        return;
      }
      
      state.data.date = date;
      state.step = 'amount';
      
      bot.sendMessage(chatId, `Step 4/7: Enter the amount (excluding GST)\n\nExample: 1000\n\nGST will be calculated automatically (10%)`);
      
    } else if (state.step === 'amount') {
      // Handle amount input
      const amount = parseFloat(text);
      
      if (isNaN(amount) || amount <= 0) {
        bot.sendMessage(chatId, '❌ Invalid amount. Please enter a positive number');
        return;
      }
      
      state.data.amount = amount;
      state.data.gst_amount = amount * 0.10; // 10% GST
      
      // Check if ABN required (expenses over $75)
      if (state.data.type === 'Expense' && amount > 75) {
        state.step = 'abn';
        const keyboard = createInlineKeyboard(['Yes', 'No'], 2);
        
        bot.sendMessage(
          chatId,
          `Step 5/7: ABN provided?\n\nAmount: ${formatCurrency(amount)}\nGST: ${formatCurrency(state.data.gst_amount)}\nTotal: ${formatCurrency(amount + state.data.gst_amount)}\n\n⚠️ ABN required for payments over $75`,
          { reply_markup: keyboard }
        );
      } else {
        state.data.has_abn = false;
        state.step = 'description';
        
        bot.sendMessage(
          chatId,
          `Step 6/7: Enter a description\n\nAmount: ${formatCurrency(amount)}\nGST: ${formatCurrency(state.data.gst_amount)}\nTotal: ${formatCurrency(amount + state.data.gst_amount)}`
        );
      }
      
    } else if (state.step === 'description') {
      // Final step - save transaction
      state.data.description = text;
      
      // Save to database
      const id = db.addBusinessTransaction(
        state.data.date,
        state.data.amount,
        state.data.type,
        state.data.category,
        state.data.description,
        state.data.gst_amount,
        state.data.has_abn,
        null // receipt_url (future feature)
      );
      
      const total = state.data.amount + state.data.gst_amount;
      const abnStatus = state.data.has_abn ? '✅ ABN Provided' : (state.data.amount > 75 && state.data.type === 'Expense' ? '⚠️ No ABN' : 'N/A');
      
      const confirmMessage = `
✅ *Business Transaction Saved!*

ID: #${id}
📅 Date: ${state.data.date}
💼 Type: ${state.data.type}
📁 Category: ${state.data.category}
💰 Amount: ${formatCurrency(state.data.amount)}
🧾 GST (10%): ${formatCurrency(state.data.gst_amount)}
💵 Total: ${formatCurrency(total)}
📋 ABN: ${abnStatus}
📝 Description: ${state.data.description}

${state.data.type === 'Expense' && state.data.amount > 75 && !state.data.has_abn ? '⚠️ *Warning:* No ABN recorded for payment >$75' : ''}

Add another? Use /personal or /business
      `;
      
      bot.sendMessage(chatId, confirmMessage, { parse_mode: 'Markdown' });
      
      // Clear user state
      delete userStates[chatId];
    }
  } catch (error) {
    console.error('Error handling business message:', error);
    bot.sendMessage(chatId, '❌ Error saving transaction. Please try again or use /cancel');
  }
}

/**
 * ERROR HANDLING
 */
bot.on('polling_error', (error) => {
  console.error('Polling error:', error);
});

process.on('unhandledRejection', (error) => {
  console.error('Unhandled promise rejection:', error);
});

console.log('✅ Bot is ready!');
console.log('💬 Send /start to your bot to begin');
