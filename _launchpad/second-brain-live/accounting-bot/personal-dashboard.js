// personal-dashboard.js
// Personal Finance Dashboard - Web interface for viewing personal transactions

const express = require('express');
const db = require('./database');
const path = require('path');

const app = express();
const PORT = 3000;

// Middleware to parse JSON
app.use(express.json());
app.use(express.static('public'));

// Initialize database
db.initializeDatabase();

/**
 * HELPER FUNCTIONS
 */

// Get current month and year
function getCurrentPeriod() {
  const now = new Date();
  return {
    year: now.getFullYear(),
    month: now.getMonth() + 1
  };
}

// Get last 6 months for trend analysis
function getLastSixMonths() {
  const months = [];
  const now = new Date();
  
  for (let i = 5; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.push({
      year: date.getFullYear(),
      month: date.getMonth() + 1,
      monthName: date.toLocaleString('default', { month: 'short' }),
      label: `${date.toLocaleString('default', { month: 'short' })} ${date.getFullYear()}`
    });
  }
  
  return months;
}

/**
 * API ENDPOINTS
 */

// Get summary for current month
app.get('/api/summary', (req, res) => {
  try {
    const { year, month } = req.query.year && req.query.month 
      ? { year: parseInt(req.query.year), month: parseInt(req.query.month) }
      : getCurrentPeriod();
    
    const transactions = db.getPersonalTransactionsByMonth(year, month);
    
    // Calculate totals
    const income = transactions
      .filter(t => t.category === 'Income')
      .reduce((sum, t) => sum + t.amount, 0);
    
    const expenses = transactions
      .filter(t => t.category !== 'Income')
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);
    
    const balance = income - expenses;
    
    // Category breakdown
    const categoryBreakdown = db.getPersonalCategorySummary(year, month);
    
    res.json({
      year,
      month,
      monthName: new Date(year, month - 1).toLocaleString('default', { month: 'long' }),
      income: income.toFixed(2),
      expenses: expenses.toFixed(2),
      balance: balance.toFixed(2),
      transactionCount: transactions.length,
      categoryBreakdown: categoryBreakdown.map(c => ({
        category: c.category,
        total: parseFloat(c.total).toFixed(2),
        count: c.count
      }))
    });
  } catch (error) {
    console.error('Error getting summary:', error);
    res.status(500).json({ error: 'Failed to get summary' });
  }
});

// Get all transactions for a month
app.get('/api/transactions', (req, res) => {
  try {
    const { year, month } = req.query.year && req.query.month
      ? { year: parseInt(req.query.year), month: parseInt(req.query.month) }
      : getCurrentPeriod();
    
    const transactions = db.getPersonalTransactionsByMonth(year, month);
    
    res.json(transactions.map(t => ({
      ...t,
      amount: parseFloat(t.amount).toFixed(2)
    })));
  } catch (error) {
    console.error('Error getting transactions:', error);
    res.status(500).json({ error: 'Failed to get transactions' });
  }
});

// Get trend data for last 6 months
app.get('/api/trend', (req, res) => {
  try {
    const months = getLastSixMonths();
    
    const trendData = months.map(m => {
      const transactions = db.getPersonalTransactionsByMonth(m.year, m.month);
      
      const income = transactions
        .filter(t => t.category === 'Income')
        .reduce((sum, t) => sum + t.amount, 0);
      
      const expenses = transactions
        .filter(t => t.category !== 'Income')
        .reduce((sum, t) => sum + Math.abs(t.amount), 0);
      
      return {
        label: m.label,
        income: income.toFixed(2),
        expenses: expenses.toFixed(2),
        balance: (income - expenses).toFixed(2)
      };
    });
    
    res.json(trendData);
  } catch (error) {
    console.error('Error getting trend:', error);
    res.status(500).json({ error: 'Failed to get trend data' });
  }
});

// Export to CSV
app.get('/api/export', (req, res) => {
  try {
    const transactions = db.getAllPersonalTransactions();
    
    // Create CSV content
    let csv = 'ID,Date,Amount,Category,Description,Payment Method,Created At\n';
    
    transactions.forEach(t => {
      csv += `${t.id},${t.date},${t.amount},${t.category},"${t.description}",${t.payment_method},${t.created_at}\n`;
    });
    
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=personal_transactions.csv');
    res.send(csv);
  } catch (error) {
    console.error('Error exporting:', error);
    res.status(500).json({ error: 'Failed to export data' });
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
    <title>Personal Finance Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
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
            border-bottom: 3px solid #667eea;
        }
        
        h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        
        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .month-selector {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .month-selector select {
            padding: 10px 15px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            background: white;
        }
        
        .btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        .btn:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card.income {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .card.expense {
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }
        
        .card.balance {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .card-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        
        .card-value {
            font-size: 2.2em;
            font-weight: bold;
        }
        
        .card-count {
            font-size: 0.8em;
            opacity: 0.8;
            margin-top: 5px;
        }
        
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #333;
            font-weight: 600;
        }
        
        .transactions-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
        }
        
        .section-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #333;
        }
        
        .transaction-filters {
            margin-bottom: 20px;
        }
        
        .search-box {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
        }
        
        .transactions-table {
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #667eea;
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
        
        .amount-positive {
            color: #11998e;
            font-weight: bold;
        }
        
        .amount-negative {
            color: #ee0979;
            font-weight: bold;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
            color: #666;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        @media (max-width: 768px) {
            .charts-section {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.8em;
            }
            
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>💰 Personal Finance Dashboard</h1>
            <p class="subtitle">Track your income and expenses</p>
        </header>
        
        <div class="controls">
            <div class="month-selector">
                <label>View:</label>
                <select id="monthSelect"></select>
                <select id="yearSelect"></select>
                <button class="btn" onclick="loadData()">Update</button>
            </div>
            <button class="btn" onclick="exportData()">📊 Export to CSV</button>
        </div>
        
        <div class="summary-cards">
            <div class="card income">
                <div class="card-label">Total Income</div>
                <div class="card-value" id="totalIncome">$0.00</div>
                <div class="card-count" id="incomeCount">0 transactions</div>
            </div>
            <div class="card expense">
                <div class="card-label">Total Expenses</div>
                <div class="card-value" id="totalExpenses">$0.00</div>
                <div class="card-count" id="expenseCount">0 transactions</div>
            </div>
            <div class="card balance">
                <div class="card-label">Balance</div>
                <div class="card-value" id="balance">$0.00</div>
                <div class="card-count" id="totalCount">0 total</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">Category Breakdown</div>
                <canvas id="categoryChart"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">6-Month Trend</div>
                <canvas id="trendChart"></canvas>
            </div>
        </div>
        
        <div class="transactions-section">
            <div class="section-title">Recent Transactions</div>
            <div class="transaction-filters">
                <input type="text" class="search-box" id="searchBox" placeholder="Search transactions..." onkeyup="filterTransactions()">
            </div>
            <div class="transactions-table">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Category</th>
                            <th>Description</th>
                            <th>Payment</th>
                            <th>Amount</th>
                        </tr>
                    </thead>
                    <tbody id="transactionsBody">
                        <tr><td colspan="5" class="loading">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        let allTransactions = [];
        let categoryChart = null;
        let trendChart = null;
        
        // Initialize month and year selectors
        function initializeSelectors() {
            const now = new Date();
            const currentMonth = now.getMonth() + 1;
            const currentYear = now.getFullYear();
            
            // Populate months
            const months = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ];
            
            const monthSelect = document.getElementById('monthSelect');
            months.forEach((month, index) => {
                const option = document.createElement('option');
                option.value = index + 1;
                option.textContent = month;
                if (index + 1 === currentMonth) option.selected = true;
                monthSelect.appendChild(option);
            });
            
            // Populate years (last 5 years)
            const yearSelect = document.getElementById('yearSelect');
            for (let i = 0; i < 5; i++) {
                const year = currentYear - i;
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                if (i === 0) option.selected = true;
                yearSelect.appendChild(option);
            }
        }
        
        // Load all data
        async function loadData() {
            const month = document.getElementById('monthSelect').value;
            const year = document.getElementById('yearSelect').value;
            
            try {
                await Promise.all([
                    loadSummary(year, month),
                    loadTransactions(year, month),
                    loadTrend()
                ]);
            } catch (error) {
                console.error('Error loading data:', error);
                alert('Failed to load data. Please try again.');
            }
        }
        
        // Load summary data
        async function loadSummary(year, month) {
            const response = await fetch(\`/api/summary?year=\${year}&month=\${month}\`);
            const data = await response.json();
            
            document.getElementById('totalIncome').textContent = '$' + data.income;
            document.getElementById('totalExpenses').textContent = '$' + data.expenses;
            document.getElementById('balance').textContent = '$' + data.balance;
            document.getElementById('totalCount').textContent = data.transactionCount + ' total';
            
            // Update category chart
            updateCategoryChart(data.categoryBreakdown);
        }
        
        // Load transactions
        async function loadTransactions(year, month) {
            const response = await fetch(\`/api/transactions?year=\${year}&month=\${month}\`);
            allTransactions = await response.json();
            
            displayTransactions(allTransactions);
        }
        
        // Display transactions in table
        function displayTransactions(transactions) {
            const tbody = document.getElementById('transactionsBody');
            
            if (transactions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="no-data">No transactions found</td></tr>';
                return;
            }
            
            tbody.innerHTML = transactions.map(t => \`
                <tr>
                    <td>\${t.date}</td>
                    <td>\${t.category}</td>
                    <td>\${t.description}</td>
                    <td>\${t.payment_method}</td>
                    <td class="\${parseFloat(t.amount) >= 0 ? 'amount-positive' : 'amount-negative'}">
                        $\${t.amount}
                    </td>
                </tr>
            \`).join('');
        }
        
        // Filter transactions
        function filterTransactions() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            
            const filtered = allTransactions.filter(t => 
                t.description.toLowerCase().includes(searchTerm) ||
                t.category.toLowerCase().includes(searchTerm) ||
                t.payment_method.toLowerCase().includes(searchTerm)
            );
            
            displayTransactions(filtered);
        }
        
        // Load trend data
        async function loadTrend() {
            const response = await fetch('/api/trend');
            const data = await response.json();
            
            updateTrendChart(data);
        }
        
        // Update category chart
        function updateCategoryChart(categoryBreakdown) {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            
            if (categoryChart) {
                categoryChart.destroy();
            }
            
            const colors = [
                '#11998e', '#ee0979', '#667eea', '#f093fb', '#4facfe',
                '#43e97b', '#fa709a', '#30cfd0', '#a8edea', '#fed6e3'
            ];
            
            categoryChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: categoryBreakdown.map(c => c.category),
                    datasets: [{
                        data: categoryBreakdown.map(c => Math.abs(parseFloat(c.total))),
                        backgroundColor: colors.slice(0, categoryBreakdown.length),
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        // Update trend chart
        function updateTrendChart(trendData) {
            const ctx = document.getElementById('trendChart').getContext('2d');
            
            if (trendChart) {
                trendChart.destroy();
            }
            
            trendChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: trendData.map(d => d.label),
                    datasets: [
                        {
                            label: 'Income',
                            data: trendData.map(d => parseFloat(d.income)),
                            borderColor: '#11998e',
                            backgroundColor: 'rgba(17, 153, 142, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Expenses',
                            data: trendData.map(d => parseFloat(d.expenses)),
                            borderColor: '#ee0979',
                            backgroundColor: 'rgba(238, 9, 121, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
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
        }
        
        // Export data
        function exportData() {
            window.location.href = '/api/export';
        }
        
        // Initialize on page load
        initializeSelectors();
        loadData();
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
  console.log('✅ Personal Finance Dashboard is running!');
  console.log('📊 Open your browser to: http://localhost:' + PORT);
  console.log('='.repeat(50));
});

module.exports = app;
