// business-dashboard.js
// Business/ATO Compliance Dashboard - For Australian PTY LTD construction company

const express = require('express');
const db = require('./database');

const app = express();
const PORT = 3001;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Initialize database
db.initializeDatabase();

/**
 * HELPER FUNCTIONS
 */

// Get current Australian financial year
function getCurrentFinancialYear() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  
  // Australian FY starts July 1
  return month >= 7 ? year : year - 1;
}

// Get quarter based on month (Australian FY)
function getQuarterFromMonth(month) {
  if (month >= 7 && month <= 9) return 1;  // Q1: Jul-Sep
  if (month >= 10 && month <= 12) return 2; // Q2: Oct-Dec
  if (month >= 1 && month <= 3) return 3;   // Q3: Jan-Mar
  return 4;                                   // Q4: Apr-Jun
}

/**
 * API ENDPOINTS
 */

// Get BAS data for a quarter
app.get('/api/bas', (req, res) => {
  try {
    const year = parseInt(req.query.year) || getCurrentFinancialYear();
    const quarter = parseInt(req.query.quarter) || 1;
    
    const basData = db.getBASDataForQuarter(year, quarter);
    res.json(basData);
  } catch (error) {
    console.error('Error getting BAS data:', error);
    res.status(500).json({ error: 'Failed to get BAS data' });
  }
});

// Get profit and loss for a period
app.get('/api/profit-loss', (req, res) => {
  try {
    const startDate = req.query.startDate;
    const endDate = req.query.endDate;
    
    if (!startDate || !endDate) {
      return res.status(400).json({ error: 'Start and end dates required' });
    }
    
    const pl = db.getProfitLoss(startDate, endDate);
    res.json(pl);
  } catch (error) {
    console.error('Error getting P&L:', error);
    res.status(500).json({ error: 'Failed to get P&L statement' });
  }
});

// Get compliance alerts
app.get('/api/compliance', (req, res) => {
  try {
    const alerts = db.getComplianceAlerts();
    res.json(alerts);
  } catch (error) {
    console.error('Error getting compliance alerts:', error);
    res.status(500).json({ error: 'Failed to get compliance alerts' });
  }
});

// Get all business transactions
app.get('/api/transactions', (req, res) => {
  try {
    const year = parseInt(req.query.year);
    const month = parseInt(req.query.month);
    
    if (!year || !month) {
      // Return all transactions
      const transactions = db.getAllBusinessTransactions();
      return res.json(transactions);
    }
    
    const transactions = db.getBusinessTransactionsByMonth(year, month);
    res.json(transactions);
  } catch (error) {
    console.error('Error getting transactions:', error);
    res.status(500).json({ error: 'Failed to get transactions' });
  }
});

// Export to CSV
app.get('/api/export', (req, res) => {
  try {
    const transactions = db.getAllBusinessTransactions();
    
    let csv = 'ID,Date,Type,Category,Amount,GST Amount,Total,Has ABN,Description,Created At\n';
    
    transactions.forEach(t => {
      const total = parseFloat(t.amount) + parseFloat(t.gst_amount);
      csv += `${t.id},${t.date},${t.type},${t.category},${t.amount},${t.gst_amount},${total.toFixed(2)},${t.has_abn ? 'Yes' : 'No'},"${t.description}",${t.created_at}\n`;
    });
    
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=business_transactions.csv');
    res.send(csv);
  } catch (error) {
    console.error('Error exporting:', error);
    res.status(500).json({ error: 'Failed to export data' });
  }
});

// Get category summary for expenses
app.get('/api/expense-breakdown', (req, res) => {
  try {
    const startDate = req.query.startDate;
    const endDate = req.query.endDate;
    
    const stmt = db.db.prepare(`
      SELECT 
        category,
        SUM(amount) as total,
        SUM(gst_amount) as total_gst,
        COUNT(*) as count
      FROM business_transactions
      WHERE type = 'Expense'
      AND date >= ? AND date <= ?
      GROUP BY category
      ORDER BY total DESC
    `);
    
    const breakdown = stmt.all(startDate, endDate);
    res.json(breakdown);
  } catch (error) {
    console.error('Error getting expense breakdown:', error);
    res.status(500).json({ error: 'Failed to get expense breakdown' });
  }
});

/**
 * SERVE HTML DASHBOARD
 */
app.get('/', (req, res) => {
  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business/ATO Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #1e3c72;
        }
        
        h1 {
            color: #1e3c72;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .ato-badge {
            display: inline-block;
            background: #1e3c72;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid #eee;
        }
        
        .tab {
            padding: 15px 30px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.1em;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #1e3c72;
            border-bottom-color: #1e3c72;
            font-weight: 600;
        }
        
        .tab:hover {
            color: #1e3c72;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        select, .btn {
            padding: 12px 20px;
            border: 2px solid #1e3c72;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            background: white;
        }
        
        .btn {
            background: #1e3c72;
            color: white;
            transition: all 0.3s;
        }
        
        .btn:hover {
            background: #2a5298;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(30, 60, 114, 0.4);
        }
        
        .bas-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .bas-card {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .bas-card.refund {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .bas-card.payable {
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }
        
        .bas-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        
        .bas-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .bas-code {
            font-size: 0.8em;
            opacity: 0.8;
            margin-top: 5px;
        }
        
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #1e3c72;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 8px;
        }
        
        .info-box h3 {
            color: #1e3c72;
            margin-bottom: 10px;
        }
        
        .info-box p {
            color: #555;
            line-height: 1.6;
        }
        
        .alert-box {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 8px;
        }
        
        .alert-box.danger {
            background: #f8d7da;
            border-left-color: #dc3545;
        }
        
        .alert-box h3 {
            color: #856404;
            margin-bottom: 10px;
        }
        
        .alert-box.danger h3 {
            color: #721c24;
        }
        
        .pl-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        
        .pl-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #dee2e6;
        }
        
        .pl-row.total {
            border-top: 3px solid #1e3c72;
            border-bottom: 3px solid #1e3c72;
            font-weight: bold;
            font-size: 1.2em;
            margin-top: 10px;
        }
        
        .pl-label {
            color: #333;
        }
        
        .pl-value {
            color: #1e3c72;
            font-weight: 600;
        }
        
        .pl-value.negative {
            color: #dc3545;
        }
        
        table {
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        
        th {
            background: #1e3c72;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .compliance-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #ffc107;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .compliance-item.critical {
            border-left-color: #dc3545;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
            color: #666;
        }
        
        .chart-container {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
        }
        
        @media (max-width: 768px) {
            .tabs {
                flex-direction: column;
            }
            
            .bas-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>💼 Business Dashboard</h1>
            <p class="subtitle">ATO-Compliant Financial Management for PTY LTD Construction Company</p>
            <span class="ato-badge">🇦🇺 Australian Tax Office Compliant</span>
        </header>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('bas')">BAS Reporting</button>
            <button class="tab" onclick="showTab('profitloss')">Profit & Loss</button>
            <button class="tab" onclick="showTab('compliance')">Compliance</button>
            <button class="tab" onclick="showTab('transactions')">Transactions</button>
        </div>
        
        <!-- BAS REPORTING TAB -->
        <div id="bas" class="tab-content active">
            <div class="controls">
                <label>Financial Year:</label>
                <select id="fySelect"></select>
                <label>Quarter:</label>
                <select id="quarterSelect">
                    <option value="1">Q1 (Jul-Sep)</option>
                    <option value="2">Q2 (Oct-Dec)</option>
                    <option value="3">Q3 (Jan-Mar)</option>
                    <option value="4">Q4 (Apr-Jun)</option>
                </select>
                <button class="btn" onclick="loadBAS()">Load BAS Data</button>
                <button class="btn" onclick="exportData()">📊 Export CSV</button>
            </div>
            
            <div class="info-box">
                <h3>📋 About BAS (Business Activity Statement)</h3>
                <p>
                    The BAS is a form submitted to the ATO to report and pay GST, PAYG instalments, PAYG withholding, 
                    and other taxes. As a PTY LTD construction company, you must report quarterly or monthly depending on 
                    your turnover. This dashboard automatically calculates all required fields from your transactions.
                </p>
            </div>
            
            <div id="basData" class="loading">Select a quarter to view BAS data</div>
            
            <div class="chart-container" style="display: none;" id="expenseChart">
                <h3>Expense Breakdown by Category</h3>
                <canvas id="expenseBreakdownChart"></canvas>
            </div>
        </div>
        
        <!-- PROFIT & LOSS TAB -->
        <div id="profitloss" class="tab-content">
            <div class="controls">
                <label>Start Date:</label>
                <input type="date" id="plStartDate">
                <label>End Date:</label>
                <input type="date" id="plEndDate">
                <button class="btn" onclick="loadProfitLoss()">Generate Report</button>
            </div>
            
            <div class="info-box">
                <h3>📊 Profit & Loss Statement</h3>
                <p>
                    Shows your business's financial performance over a specific period. Essential for tax preparation 
                    and business decision-making. Revenue minus expenses equals your net profit (or loss).
                </p>
            </div>
            
            <div id="plData" class="loading">Select a date range to generate P&L statement</div>
        </div>
        
        <!-- COMPLIANCE TAB -->
        <div id="compliance" class="tab-content">
            <button class="btn" onclick="loadCompliance()">🔍 Check Compliance</button>
            
            <div class="alert-box">
                <h3>⚠️ ATO Compliance Requirements</h3>
                <p>
                    • Transactions over $10,000 must be reported to AUSTRAC<br>
                    • Payments over $75 require ABN from suppliers (or withhold 47%)<br>
                    • Keep records for 5 years<br>
                    • Lodge BAS on time to avoid penalties<br>
                    • Report all cash transactions accurately
                </p>
            </div>
            
            <div id="complianceData" class="loading">Click "Check Compliance" to scan for issues</div>
        </div>
        
        <!-- TRANSACTIONS TAB -->
        <div id="transactions" class="tab-content">
            <div class="controls">
                <label>Month:</label>
                <select id="txMonthSelect"></select>
                <label>Year:</label>
                <select id="txYearSelect"></select>
                <button class="btn" onclick="loadTransactions()">Load Transactions</button>
            </div>
            
            <div id="transactionsData" class="loading">Select a month to view transactions</div>
        </div>
    </div>
    
    <script>
        let expenseChart = null;
        
        // Initialize selectors
        function initializeSelectors() {
            const currentFY = getCurrentFinancialYear();
            
            // Financial year selector
            const fySelect = document.getElementById('fySelect');
            for (let i = 0; i < 5; i++) {
                const fy = currentFY - i;
                const option = document.createElement('option');
                option.value = fy;
                option.textContent = \`FY \${fy}-\${(fy + 1).toString().substr(2)}\`;
                if (i === 0) option.selected = true;
                fySelect.appendChild(option);
            }
            
            // Month and year selectors for transactions
            const months = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ];
            
            const txMonthSelect = document.getElementById('txMonthSelect');
            const now = new Date();
            months.forEach((month, index) => {
                const option = document.createElement('option');
                option.value = index + 1;
                option.textContent = month;
                if (index === now.getMonth()) option.selected = true;
                txMonthSelect.appendChild(option);
            });
            
            const txYearSelect = document.getElementById('txYearSelect');
            for (let i = 0; i < 5; i++) {
                const year = now.getFullYear() - i;
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                if (i === 0) option.selected = true;
                txYearSelect.appendChild(option);
            }
            
            // Set default P&L dates (current financial year)
            const fyStart = new Date(currentFY, 6, 1); // July 1
            const fyEnd = new Date(currentFY + 1, 5, 30); // June 30
            document.getElementById('plStartDate').valueAsDate = fyStart;
            document.getElementById('plEndDate').valueAsDate = fyEnd;
        }
        
        function getCurrentFinancialYear() {
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            return month >= 7 ? year : year - 1;
        }
        
        // Tab switching
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }
        
        // Load BAS data
        async function loadBAS() {
            const year = document.getElementById('fySelect').value;
            const quarter = document.getElementById('quarterSelect').value;
            
            document.getElementById('basData').innerHTML = '<div class="loading">Loading BAS data...</div>';
            
            try {
                const response = await fetch(\`/api/bas?year=\${year}&quarter=\${quarter}\`);
                const data = await response.json();
                
                const netGST = parseFloat(data.netGST);
                const isRefund = netGST < 0;
                
                document.getElementById('basData').innerHTML = \`
                    <div class="bas-grid">
                        <div class="bas-card">
                            <div class="bas-label">Total Sales</div>
                            <div class="bas-value">$\${data.G1}</div>
                            <div class="bas-code">G1 (inc. GST)</div>
                        </div>
                        <div class="bas-card">
                            <div class="bas-label">GST on Sales</div>
                            <div class="bas-value">$\${data['1A']}</div>
                            <div class="bas-code">1A</div>
                        </div>
                        <div class="bas-card">
                            <div class="bas-label">Capital Purchases</div>
                            <div class="bas-value">$\${data.G10}</div>
                            <div class="bas-code">G10</div>
                        </div>
                        <div class="bas-card">
                            <div class="bas-label">Non-Capital Purchases</div>
                            <div class="bas-value">$\${data.G11}</div>
                            <div class="bas-code">G11</div>
                        </div>
                        <div class="bas-card">
                            <div class="bas-label">GST on Purchases</div>
                            <div class="bas-value">$\${data.G18}</div>
                            <div class="bas-code">G18</div>
                        </div>
                        <div class="bas-card \${isRefund ? 'refund' : 'payable'}">
                            <div class="bas-label">\${isRefund ? 'GST Refund' : 'GST Payable'}</div>
                            <div class="bas-value">$\${Math.abs(netGST).toFixed(2)}</div>
                            <div class="bas-code">Net GST</div>
                        </div>
                    </div>
                    
                    <div class="\${isRefund ? 'info-box' : 'alert-box'}">
                        <h3>\${isRefund ? '✅ GST Refund Due' : '💰 GST Payment Required'}</h3>
                        <p>
                            Period: \${data.startDate} to \${data.endDate}<br>
                            \${isRefund 
                                ? \`The ATO owes you $\${Math.abs(netGST).toFixed(2)} because you paid more GST on purchases than you collected on sales.\`
                                : \`You need to pay $\${netGST} to the ATO for GST collected on sales minus GST paid on purchases.\`
                            }
                        </p>
                    </div>
                \`;
                
                // Load expense breakdown chart
                await loadExpenseBreakdown(data.startDate, data.endDate);
                
            } catch (error) {
                console.error('Error loading BAS:', error);
                document.getElementById('basData').innerHTML = '<div class="alert-box danger"><h3>Error</h3><p>Failed to load BAS data</p></div>';
            }
        }
        
        // Load expense breakdown
        async function loadExpenseBreakdown(startDate, endDate) {
            try {
                const response = await fetch(\`/api/expense-breakdown?startDate=\${startDate}&endDate=\${endDate}\`);
                const data = await response.json();
                
                document.getElementById('expenseChart').style.display = 'block';
                
                const ctx = document.getElementById('expenseBreakdownChart').getContext('2d');
                
                if (expenseChart) {
                    expenseChart.destroy();
                }
                
                const colors = [
                    '#1e3c72', '#2a5298', '#11998e', '#38ef7d', '#ee0979',
                    '#ff6a00', '#667eea', '#764ba2', '#f093fb', '#4facfe'
                ];
                
                expenseChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.map(d => d.category),
                        datasets: [{
                            label: 'Amount ($)',
                            data: data.map(d => parseFloat(d.total)),
                            backgroundColor: colors.slice(0, data.length),
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return '$' + value.toLocaleString();
                                    }
                                }
                            }
                        }
                    }
                });
            } catch (error) {
                console.error('Error loading expense breakdown:', error);
            }
        }
        
        // Load Profit & Loss
        async function loadProfitLoss() {
            const startDate = document.getElementById('plStartDate').value;
            const endDate = document.getElementById('plEndDate').value;
            
            if (!startDate || !endDate) {
                alert('Please select both start and end dates');
                return;
            }
            
            document.getElementById('plData').innerHTML = '<div class="loading">Generating P&L statement...</div>';
            
            try {
                const response = await fetch(\`/api/profit-loss?startDate=\${startDate}&endDate=\${endDate}\`);
                const data = await response.json();
                
                const netProfit = parseFloat(data.netProfit);
                const isProfit = netProfit >= 0;
                
                document.getElementById('plData').innerHTML = \`
                    <div class="pl-section">
                        <h2>Profit & Loss Statement</h2>
                        <p style="color: #666; margin-bottom: 20px;">Period: \${startDate} to \${endDate}</p>
                        
                        <div class="pl-row">
                            <span class="pl-label">Revenue</span>
                            <span class="pl-value">$\${data.revenue}</span>
                        </div>
                        
                        <div class="pl-row">
                            <span class="pl-label">Less: Cost of Goods Sold</span>
                            <span class="pl-value negative">($\${data.cogs})</span>
                        </div>
                        
                        <div class="pl-row" style="font-weight: 600;">
                            <span class="pl-label">Gross Profit</span>
                            <span class="pl-value">$\${data.grossProfit}</span>
                        </div>
                        
                        <div class="pl-row">
                            <span class="pl-label">Less: Operating Expenses</span>
                            <span class="pl-value negative">($\${data.operatingExpenses})</span>
                        </div>
                        
                        <div class="pl-row total">
                            <span class="pl-label">Net \${isProfit ? 'Profit' : 'Loss'}</span>
                            <span class="pl-value \${isProfit ? '' : 'negative'}">
                                \${isProfit ? '$' + data.netProfit : '($' + Math.abs(netProfit).toFixed(2) + ')'}
                            </span>
                        </div>
                    </div>
                    
                    <div class="\${isProfit ? 'info-box' : 'alert-box danger'}">
                        <h3>\${isProfit ? '✅ Profitable Period' : '⚠️ Loss Period'}</h3>
                        <p>
                            \${isProfit 
                                ? \`Your business made a profit of $\${data.netProfit} during this period.\`
                                : \`Your business had a loss of $\${Math.abs(netProfit).toFixed(2)} during this period.\`
                            }
                        </p>
                    </div>
                \`;
            } catch (error) {
                console.error('Error loading P&L:', error);
                document.getElementById('plData').innerHTML = '<div class="alert-box danger"><h3>Error</h3><p>Failed to generate P&L statement</p></div>';
            }
        }
        
        // Load compliance alerts
        async function loadCompliance() {
            document.getElementById('complianceData').innerHTML = '<div class="loading">Checking compliance...</div>';
            
            try {
                const response = await fetch('/api/compliance');
                const data = await response.json();
                
                let html = '';
                
                // Large transactions (>$10,000)
                if (data.largeTransactions.length > 0) {
                    html += \`
                        <div class="alert-box danger">
                            <h3>🚨 Large Transactions (>$10,000)</h3>
                            <p>These transactions must be reported to AUSTRAC:</p>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Type</th>
                                    <th>Category</th>
                                    <th>Amount</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                    \`;
                    
                    data.largeTransactions.forEach(t => {
                        const total = parseFloat(t.amount) + parseFloat(t.gst_amount);
                        html += \`
                            <tr>
                                <td>\${t.date}</td>
                                <td>\${t.type}</td>
                                <td>\${t.category}</td>
                                <td>$\${total.toFixed(2)}</td>
                                <td>\${t.description}</td>
                            </tr>
                        \`;
                    });
                    
                    html += '</tbody></table>';
                } else {
                    html += '<div class="info-box"><h3>✅ No Large Transactions</h3><p>No transactions over $10,000 found.</p></div>';
                }
                
                // Missing ABN
                if (data.missingABN.length > 0) {
                    html += \`
                        <div class="alert-box" style="margin-top: 30px;">
                            <h3>⚠️ Missing ABN Records</h3>
                            <p>Payments over $75 without ABN may require 47% withholding:</p>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Category</th>
                                    <th>Amount</th>
                                    <th>Description</th>
                                    <th>Withholding (47%)</th>
                                </tr>
                            </thead>
                            <tbody>
                    \`;
                    
                    data.missingABN.forEach(t => {
                        const withholding = parseFloat(t.amount) * 0.47;
                        html += \`
                            <tr>
                                <td>\${t.date}</td>
                                <td>\${t.category}</td>
                                <td>$\${parseFloat(t.amount).toFixed(2)}</td>
                                <td>\${t.description}</td>
                                <td>$\${withholding.toFixed(2)}</td>
                            </tr>
                        \`;
                    });
                    
                    html += '</tbody></table>';
                } else {
                    html += '<div class="info-box" style="margin-top: 30px;"><h3>✅ ABN Compliance</h3><p>All applicable payments have ABN records.</p></div>';
                }
                
                document.getElementById('complianceData').innerHTML = html;
                
            } catch (error) {
                console.error('Error loading compliance:', error);
                document.getElementById('complianceData').innerHTML = '<div class="alert-box danger"><h3>Error</h3><p>Failed to check compliance</p></div>';
            }
        }
        
        // Load transactions
        async function loadTransactions() {
            const month = document.getElementById('txMonthSelect').value;
            const year = document.getElementById('txYearSelect').value;
            
            document.getElementById('transactionsData').innerHTML = '<div class="loading">Loading transactions...</div>';
            
            try {
                const response = await fetch(\`/api/transactions?year=\${year}&month=\${month}\`);
                const data = await response.json();
                
                if (data.length === 0) {
                    document.getElementById('transactionsData').innerHTML = '<div class="info-box"><h3>No Transactions</h3><p>No transactions found for this period.</p></div>';
                    return;
                }
                
                let html = \`
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Type</th>
                                <th>Category</th>
                                <th>Amount</th>
                                <th>GST</th>
                                <th>Total</th>
                                <th>ABN</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                \`;
                
                data.forEach(t => {
                    const total = parseFloat(t.amount) + parseFloat(t.gst_amount);
                    html += \`
                        <tr>
                            <td>\${t.date}</td>
                            <td>\${t.type}</td>
                            <td>\${t.category}</td>
                            <td>$\${parseFloat(t.amount).toFixed(2)}</td>
                            <td>$\${parseFloat(t.gst_amount).toFixed(2)}</td>
                            <td>$\${total.toFixed(2)}</td>
                            <td>\${t.has_abn ? '✅' : (parseFloat(t.amount) > 75 && t.type === 'Expense' ? '❌' : 'N/A')}</td>
                            <td>\${t.description}</td>
                        </tr>
                    \`;
                });
                
                html += '</tbody></table>';
                
                document.getElementById('transactionsData').innerHTML = html;
                
            } catch (error) {
                console.error('Error loading transactions:', error);
                document.getElementById('transactionsData').innerHTML = '<div class="alert-box danger"><h3>Error</h3><p>Failed to load transactions</p></div>';
            }
        }
        
        // Export data
        function exportData() {
            window.location.href = '/api/export';
        }
        
        // Initialize on load
        initializeSelectors();
    </script>
</body>
</html>
  `;
  
  res.send(html);
});

/**
 * START SERVER
 */
app.listen(PORT, () => {
  console.log('='.repeat(50));
  console.log('✅ Business/ATO Dashboard is running!');
  console.log('📊 Open your browser to: http://localhost:' + PORT);
  console.log('='.repeat(50));
});

module.exports = app;
