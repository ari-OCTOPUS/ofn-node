// database.js
// This file handles all database operations for both personal and business transactions
// Using SQLite - a simple file-based database that doesn't require a server

const Database = require('better-sqlite3');
const path = require('path');

// Create database file in the same directory as this script
const dbPath = path.join(__dirname, 'financial_tracker.db');
const db = new Database(dbPath);

// Enable foreign keys for data integrity
db.pragma('foreign_keys = ON');

/**
 * Initialize the database with required tables
 * Creates separate tables for personal and business transactions
 */
function initializeDatabase() {
  console.log('Initializing database...');
  
  // Create personal_transactions table
  // This stores all personal expenses and income
  db.exec(`
    CREATE TABLE IF NOT EXISTS personal_transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      date TEXT NOT NULL,                    -- Date in YYYY-MM-DD format
      amount REAL NOT NULL,                  -- Transaction amount (positive for income, can be negative for expenses)
      category TEXT NOT NULL,                -- Category: Income, Groceries, Utilities, etc.
      description TEXT NOT NULL,             -- What was the transaction for
      payment_method TEXT NOT NULL,          -- How it was paid: Cash, Card, Bank Transfer, etc.
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- When this record was created
    )
  `);

  // Create business_transactions table
  // This stores all business transactions for ATO compliance
  db.exec(`
    CREATE TABLE IF NOT EXISTS business_transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      date TEXT NOT NULL,                    -- Transaction date in YYYY-MM-DD format
      amount REAL NOT NULL,                  -- Transaction amount (excluding GST)
      type TEXT NOT NULL,                    -- 'Income' or 'Expense'
      category TEXT NOT NULL,                -- Business category (Materials, Subcontractors, etc.)
      description TEXT NOT NULL,             -- Detailed description
      gst_amount REAL NOT NULL,              -- GST amount (10% of amount)
      has_abn INTEGER DEFAULT 0,             -- 1 if ABN provided, 0 if not (required for payments >$75)
      receipt_url TEXT,                      -- URL to receipt image (optional)
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Create index for faster date-based queries (important for monthly reports)
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_personal_date ON personal_transactions(date);
    CREATE INDEX IF NOT EXISTS idx_business_date ON business_transactions(date);
    CREATE INDEX IF NOT EXISTS idx_business_type ON business_transactions(type);
  `);

  console.log('Database initialized successfully!');
  console.log(`Database location: ${dbPath}`);
}

/**
 * PERSONAL TRANSACTION FUNCTIONS
 */

// Add a new personal transaction
function addPersonalTransaction(date, amount, category, description, paymentMethod) {
  const stmt = db.prepare(`
    INSERT INTO personal_transactions (date, amount, category, description, payment_method)
    VALUES (?, ?, ?, ?, ?)
  `);
  
  const result = stmt.run(date, amount, category, description, paymentMethod);
  return result.lastInsertRowid; // Return the ID of newly created record
}

// Get all personal transactions for a specific month
function getPersonalTransactionsByMonth(year, month) {
  // Format month as MM (e.g., 01, 02, 03)
  const monthStr = String(month).padStart(2, '0');
  const startDate = `${year}-${monthStr}-01`;
  
  // Calculate last day of month
  const lastDay = new Date(year, month, 0).getDate();
  const endDate = `${year}-${monthStr}-${lastDay}`;
  
  const stmt = db.prepare(`
    SELECT * FROM personal_transactions
    WHERE date >= ? AND date <= ?
    ORDER BY date DESC
  `);
  
  return stmt.all(startDate, endDate);
}

// Get personal transactions summary by category for a month
function getPersonalCategorySummary(year, month) {
  const monthStr = String(month).padStart(2, '0');
  const startDate = `${year}-${monthStr}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const endDate = `${year}-${monthStr}-${lastDay}`;
  
  const stmt = db.prepare(`
    SELECT 
      category,
      SUM(amount) as total,
      COUNT(*) as count
    FROM personal_transactions
    WHERE date >= ? AND date <= ?
    GROUP BY category
    ORDER BY total DESC
  `);
  
  return stmt.all(startDate, endDate);
}

/**
 * BUSINESS TRANSACTION FUNCTIONS
 */

// Add a new business transaction
function addBusinessTransaction(date, amount, type, category, description, gstAmount, hasAbn, receiptUrl = null) {
  const stmt = db.prepare(`
    INSERT INTO business_transactions (date, amount, type, category, description, gst_amount, has_abn, receipt_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
  
  const result = stmt.run(date, amount, type, category, description, gstAmount, hasAbn ? 1 : 0, receiptUrl);
  return result.lastInsertRowid;
}

// Get all business transactions for a specific month
function getBusinessTransactionsByMonth(year, month) {
  const monthStr = String(month).padStart(2, '0');
  const startDate = `${year}-${monthStr}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const endDate = `${year}-${monthStr}-${lastDay}`;
  
  const stmt = db.prepare(`
    SELECT * FROM business_transactions
    WHERE date >= ? AND date <= ?
    ORDER BY date DESC
  `);
  
  return stmt.all(startDate, endDate);
}

// Get BAS (Business Activity Statement) data for a quarter
// Australian quarters: Q1 (Jul-Sep), Q2 (Oct-Dec), Q3 (Jan-Mar), Q4 (Apr-Jun)
function getBASDataForQuarter(year, quarter) {
  // Calculate start and end dates based on Australian financial year
  let startMonth, endMonth, startYear, endYear;
  
  switch(quarter) {
    case 1: // Jul-Sep
      startMonth = 7; endMonth = 9;
      startYear = endYear = year;
      break;
    case 2: // Oct-Dec
      startMonth = 10; endMonth = 12;
      startYear = endYear = year;
      break;
    case 3: // Jan-Mar
      startMonth = 1; endMonth = 3;
      startYear = endYear = year + 1;
      break;
    case 4: // Apr-Jun
      startMonth = 4; endMonth = 6;
      startYear = endYear = year + 1;
      break;
  }
  
  const startDate = `${startYear}-${String(startMonth).padStart(2, '0')}-01`;
  const lastDay = new Date(endYear, endMonth, 0).getDate();
  const endDate = `${endYear}-${String(endMonth).padStart(2, '0')}-${lastDay}`;
  
  // G1: Total sales (including GST)
  const g1Stmt = db.prepare(`
    SELECT COALESCE(SUM(amount + gst_amount), 0) as total
    FROM business_transactions
    WHERE type = 'Income' AND date >= ? AND date <= ?
  `);
  const g1 = g1Stmt.get(startDate, endDate).total;
  
  // 1A: Total GST on sales
  const oneAStmt = db.prepare(`
    SELECT COALESCE(SUM(gst_amount), 0) as total
    FROM business_transactions
    WHERE type = 'Income' AND date >= ? AND date <= ?
  `);
  const oneA = oneAStmt.get(startDate, endDate).total;
  
  // G11: Non-capital purchases (operating expenses)
  const g11Stmt = db.prepare(`
    SELECT COALESCE(SUM(amount), 0) as total
    FROM business_transactions
    WHERE type = 'Expense' 
    AND category NOT IN ('Equipment Hire') 
    AND date >= ? AND date <= ?
  `);
  const g11 = g11Stmt.get(startDate, endDate).total;
  
  // G10: Capital purchases (equipment, etc.)
  const g10Stmt = db.prepare(`
    SELECT COALESCE(SUM(amount), 0) as total
    FROM business_transactions
    WHERE type = 'Expense' 
    AND category IN ('Equipment Hire') 
    AND date >= ? AND date <= ?
  `);
  const g10 = g10Stmt.get(startDate, endDate).total;
  
  // G18: Total GST on purchases
  const g18Stmt = db.prepare(`
    SELECT COALESCE(SUM(gst_amount), 0) as total
    FROM business_transactions
    WHERE type = 'Expense' AND date >= ? AND date <= ?
  `);
  const g18 = g18Stmt.get(startDate, endDate).total;
  
  return {
    quarter: quarter,
    year: year,
    startDate: startDate,
    endDate: endDate,
    G1: g1.toFixed(2),        // Total sales including GST
    G2: '0.00',               // Export sales (not applicable for construction)
    G3: '0.00',               // Other GST-free sales
    G10: g10.toFixed(2),      // Capital purchases
    G11: g11.toFixed(2),      // Non-capital purchases
    G18: g18.toFixed(2),      // GST on purchases
    '1A': oneA.toFixed(2),    // GST on sales
    netGST: (oneA - g18).toFixed(2)  // Amount to pay or refund
  };
}

// Get profit and loss statement for a period
function getProfitLoss(startDate, endDate) {
  // Total revenue
  const revenueStmt = db.prepare(`
    SELECT COALESCE(SUM(amount), 0) as total
    FROM business_transactions
    WHERE type = 'Income' AND date >= ? AND date <= ?
  `);
  const revenue = revenueStmt.get(startDate, endDate).total;
  
  // Cost of goods sold (Materials + Subcontractors)
  const cogsStmt = db.prepare(`
    SELECT COALESCE(SUM(amount), 0) as total
    FROM business_transactions
    WHERE type = 'Expense' 
    AND category IN ('Materials', 'Subcontractors')
    AND date >= ? AND date <= ?
  `);
  const cogs = cogsStmt.get(startDate, endDate).total;
  
  // Operating expenses (everything else)
  const opexStmt = db.prepare(`
    SELECT COALESCE(SUM(amount), 0) as total
    FROM business_transactions
    WHERE type = 'Expense' 
    AND category NOT IN ('Materials', 'Subcontractors')
    AND date >= ? AND date <= ?
  `);
  const opex = opexStmt.get(startDate, endDate).total;
  
  const grossProfit = revenue - cogs;
  const netProfit = grossProfit - opex;
  
  return {
    revenue: revenue.toFixed(2),
    cogs: cogs.toFixed(2),
    grossProfit: grossProfit.toFixed(2),
    operatingExpenses: opex.toFixed(2),
    netProfit: netProfit.toFixed(2)
  };
}

// Get transactions flagged for compliance review
function getComplianceAlerts() {
  // Transactions over $10,000 (cash reporting threshold)
  const largeTransactions = db.prepare(`
    SELECT * FROM business_transactions
    WHERE amount >= 10000
    ORDER BY date DESC
  `).all();
  
  // Payments over $75 without ABN
  const missingABN = db.prepare(`
    SELECT * FROM business_transactions
    WHERE type = 'Expense' 
    AND amount > 75 
    AND has_abn = 0
    ORDER BY date DESC
  `).all();
  
  return {
    largeTransactions: largeTransactions,
    missingABN: missingABN
  };
}

// Get all transactions (for export/backup)
function getAllPersonalTransactions() {
  return db.prepare('SELECT * FROM personal_transactions ORDER BY date DESC').all();
}

function getAllBusinessTransactions() {
  return db.prepare('SELECT * FROM business_transactions ORDER BY date DESC').all();
}

// Delete a transaction (for corrections)
function deletePersonalTransaction(id) {
  return db.prepare('DELETE FROM personal_transactions WHERE id = ?').run(id);
}

function deleteBusinessTransaction(id) {
  return db.prepare('DELETE FROM business_transactions WHERE id = ?').run(id);
}

// Export all functions for use in other files
module.exports = {
  initializeDatabase,
  addPersonalTransaction,
  getPersonalTransactionsByMonth,
  getPersonalCategorySummary,
  addBusinessTransaction,
  getBusinessTransactionsByMonth,
  getBASDataForQuarter,
  getProfitLoss,
  getComplianceAlerts,
  getAllPersonalTransactions,
  getAllBusinessTransactions,
  deletePersonalTransaction,
  deleteBusinessTransaction,
  db // Export database connection for direct queries if needed
};

// If this file is run directly (not imported), initialize the database
if (require.main === module) {
  initializeDatabase();
  console.log('\nDatabase is ready to use!');
  console.log('You can now start the Telegram bot with: npm start');
}
