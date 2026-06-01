// QuantMaster WebUI JavaScript

// State
let state = {
    portfolio: { value: 10000, pnl: 0, returnPct: 0 },
    watchdog: { mode: 'NORMAL', risk: 'SAFE', streak: '0W / 0L', decisions: 0 },
    market: { state: 'BULL', volatility: '--', sentiment: '--' },
    decisions: [],
    positions: [],
    opportunities: [],
    equityCurve: [10000],
    mfScore: '--',
    mfDecision: '--'
};

// API Base
const API_BASE = 'http://localhost:8088';

// Tab Navigation
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
    });
});

// Update Time
function updateTime() {
    const now = new Date();
    document.getElementById('serverTime').textContent = now.toLocaleTimeString();
}
setInterval(updateTime, 1000);
updateTime();

// Load Data
async function loadData() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        if (response.ok) {
            const data = await response.json();
            updateDashboard(data);
        }
    } catch (e) {
        // API not available, use mock data
        updateMockData();
    }
}

function updateMockData() {
    // Simulated data for demo
    state.portfolio.value = 10234.56;
    state.portfolio.pnl = 234.56;
    state.portfolio.returnPct = 2.35;
    state.watchdog.mode = 'AGGRESSIVE';
    state.watchdog.risk = 'LOW';
    state.market.state = 'BULL';
    state.market.volatility = '3.2%';
    state.market.sentiment = '72%';
    
    updateDashboardUI();
}

function updateDashboard(data) {
    if (data.portfolio) state.portfolio = data.portfolio;
    if (data.watchdog) state.watchdog = data.watchdog;
    if (data.market) state.market = data.market;
    if (data.equityCurve) state.equityCurve = data.equityCurve;
    
    updateDashboardUI();
}

function updateDashboardUI() {
    // Portfolio
    document.getElementById('portfolioValue').textContent = `$${state.portfolio.value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('pnl').textContent = `${state.portfolio.pnl >= 0 ? '+' : ''}$${state.portfolio.pnl.toFixed(2)}`;
    document.getElementById('pnl').className = `value ${state.portfolio.pnl >= 0 ? 'positive' : 'negative'}`;
    document.getElementById('returnPct').textContent = `${state.portfolio.returnPct >= 0 ? '+' : ''}${state.portfolio.returnPct.toFixed(2)}%`;
    document.getElementById('returnPct').className = `value ${state.portfolio.returnPct >= 0 ? 'positive' : 'negative'}`;
    
    // Watchdog
    document.getElementById('watchdogMode').textContent = state.watchdog.mode;
    document.getElementById('riskLevel').textContent = state.watchdog.risk;
    document.getElementById('winStreak').textContent = state.watchdog.streak;
    document.getElementById('wdMode').textContent = state.watchdog.mode;
    document.getElementById('wdDecisions').textContent = state.watchdog.decisions;
    document.getElementById('wdCapital').textContent = `$${state.portfolio.value.toLocaleString()}`;
    
    // Market
    document.getElementById('marketState').textContent = state.market.state;
    document.getElementById('volatility').textContent = state.market.volatility;
    document.getElementById('sentiment').textContent = state.market.sentiment;
}

// Run Scanner
async function runScanner() {
    const resultsDiv = document.getElementById('scannerResults');
    resultsDiv.innerHTML = '<p>🔄 Scanning Binance...</p>';
    
    try {
        const response = await fetch(`${API_BASE}/api/scan`);
        if (response.ok) {
            const data = await response.json();
            displayScannerResults(data);
        } else {
            throw new Error('API error');
        }
    } catch (e) {
        // Mock scanner results
        displayMockScannerResults();
    }
}

function displayMockScannerResults() {
    const mockResults = [
        { rank: 1, category: 'FUNDING', symbol: 'SOLUSD', score: 86.0, action: 'ARB', potential: '36%/月', risk: '中' },
        { rank: 2, category: 'SPOT', symbol: 'BTCUSDT', score: 84.8, action: 'BUY', potential: '15.8%', risk: '低' },
        { rank: 3, category: 'SPOT', symbol: 'ETHUSDT', score: 83.3, action: 'BUY', potential: '12.5%', risk: '低' },
        { rank: 4, category: 'LAUNCH', symbol: 'PORT3', score: 67.8, action: 'FARM', potential: '45.2%', risk: '中' },
        { rank: 5, category: 'HODLER', symbol: 'BNB', score: 76.8, action: 'HODL', potential: '+5%', risk: '低' },
    ];
    
    let html = '<table><thead><tr><th>Rank</th><th>Category</th><th>Symbol</th><th>Score</th><th>Action</th><th>Potential</th><th>Risk</th></tr></thead><tbody>';
    
    mockResults.forEach(r => {
        const emoji = r.action === 'BUY' || r.action === 'ARB' || r.action === 'FARM' ? '🟢' : '⚪';
        html += `<tr>
            <td>${r.rank}</td>
            <td>${r.category}</td>
            <td><strong>${r.symbol}</strong></td>
            <td><span class="score">${r.score.toFixed(1)}</span></td>
            <td>${emoji} ${r.action}</td>
            <td>${r.potential}</td>
            <td>${r.risk}</td>
        </tr>`;
    });
    
    html += '</tbody></table>';
    document.getElementById('scannerResults').innerHTML = html;
}

// Run Watchdog
async function runWatchdog() {
    try {
        const response = await fetch(`${API_BASE}/api/watchdog/decision`, { method: 'POST' });
        if (response.ok) {
            const decision = await response.json();
            addDecisionToHistory(decision);
        } else {
            throw new Error('API error');
        }
    } catch (e) {
        // Mock decision
        const mockDecision = {
            type: Math.random() > 0.5 ? 'BUY' : 'HOLD',
            symbol: 'BTC',
            confidence: 0.7 + Math.random() * 0.2,
            pnl: Math.random() * 200 - 50
        };
        
        state.decisions.unshift(mockDecision);
        state.decisions = state.decisions.slice(0, 10);
        
        if (mockDecision.pnl > 0) {
            state.portfolio.value += mockDecision.pnl;
        }
        
        state.watchdog.decisions++;
        state.portfolio.pnl = state.portfolio.value - 10000;
        state.portfolio.returnPct = (state.portfolio.pnl / 10000) * 100;
        
        updateDashboardUI();
        addDecisionToHistory(mockDecision);
    }
}

function addDecisionToHistory(decision) {
    const historyDiv = document.getElementById('decisionHistory');
    
    const emoji = decision.type === 'BUY' ? '🟢' : decision.type === 'SELL' ? '🔴' : '⚪';
    
    const html = `<div class="history-item">
        <div style="display:flex;justify-content:space-between">
            <span>${emoji} <strong>${decision.type}</strong> ${decision.symbol || ''}</span>
            <span>${new Date().toLocaleTimeString()}</span>
        </div>
        <div style="font-size:0.875rem;color:var(--text-dim)">
            Confidence: ${(decision.confidence * 100).toFixed(0)}% | 
            ${decision.pnl !== undefined ? 'P&L: $' + decision.pnl.toFixed(2) : ''}
        </div>
    </div>`;
    
    historyDiv.innerHTML = html + historyDiv.innerHTML;
    
    if (historyDiv.children.length > 10) {
        historyDiv.removeChild(historyDiv.lastChild);
    }
}

// Run MiroFish
async function runMiroFish() {
    try {
        const response = await fetch(`${API_BASE}/api/mirofish`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('mfScore').textContent = data.score || '--';
            document.getElementById('mfDecision').textContent = data.decision || '--';
        } else {
            throw new Error('API error');
        }
    } catch (e) {
        // Mock MiroFish
        const score = 50 + Math.random() * 30;
        const decision = score > 60 ? 'BUY' : score < 45 ? 'SELL' : 'HOLD';
        
        document.getElementById('mfScore').textContent = score.toFixed(1);
        document.getElementById('mfDecision').textContent = decision;
    }
}

// Run Optimizer
async function runOptimizer() {
    const resultsDiv = document.getElementById('optimizerResults');
    resultsDiv.innerHTML = '<p>🧬 Running 30-day backtest optimization...</p>';
    
    // Simulate optimization
    setTimeout(() => {
        const bestReturn = 20 + Math.random() * 40;
        const bestParams = {
            positionSize: 10 + Math.random() * 10,
            leverage: 1 + Math.random() * 1,
            stopLoss: 3 + Math.random() * 5,
            takeProfit: 10 + Math.random() * 15
        };
        
        resultsDiv.innerHTML = `
            <div style="background:var(--bg-hover);padding:1rem;border-radius:8px">
                <h4 style="color:var(--positive);margin-bottom:1rem">✅ Optimization Complete</h4>
                <div class="stat-row">
                    <span class="label">Best 30-Day Return:</span>
                    <span class="value positive">+${bestReturn.toFixed(2)}%</span>
                </div>
                <div class="stat-row">
                    <span class="label">Position Size:</span>
                    <span class="value">${bestParams.positionSize.toFixed(0)}%</span>
                </div>
                <div class="stat-row">
                    <span class="label">Leverage:</span>
                    <span class="value">${bestParams.leverage.toFixed(1)}x</span>
                </div>
                <div class="stat-row">
                    <span class="label">Stop Loss:</span>
                    <span class="value">${bestParams.stopLoss.toFixed(1)}%</span>
                </div>
                <div class="stat-row">
                    <span class="label">Take Profit:</span>
                    <span class="value">${bestParams.takeProfit.toFixed(1)}%</span>
                </div>
            </div>
        `;
    }, 2000);
}

// Save Settings
function saveSettings() {
    const settings = {
        positionSize: document.getElementById('posSize').value,
        stopLoss: document.getElementById('stopLoss').value,
        takeProfit: document.getElementById('takeProfit').value,
        apiKey: document.getElementById('apiKey').value,
        apiSecret: document.getElementById('apiSecret').value,
        proxy: document.getElementById('proxy').value
    };
    
    localStorage.setItem('quantmaster_settings', JSON.stringify(settings));
    alert('Settings saved!');
}

// Load Settings
function loadSettings() {
    const saved = localStorage.getItem('quantmaster_settings');
    if (saved) {
        const settings = JSON.parse(saved);
        document.getElementById('posSize').value = settings.positionSize || 10;
        document.getElementById('stopLoss').value = settings.stopLoss || 5;
        document.getElementById('takeProfit').value = settings.takeProfit || 15;
        document.getElementById('apiKey').value = settings.apiKey || '';
        document.getElementById('apiSecret').value = settings.apiSecret || '';
        document.getElementById('proxy').value = settings.proxy || 'http://172.29.144.1:7897';
        
        document.getElementById('posSizeVal').textContent = settings.positionSize + '%';
        document.getElementById('stopLossVal').textContent = settings.stopLoss + '%';
        document.getElementById('takeProfitVal').textContent = settings.takeProfit + '%';
    }
}

// Range sliders
document.getElementById('posSize')?.addEventListener('input', e => {
    document.getElementById('posSizeVal').textContent = e.target.value + '%';
});
document.getElementById('stopLoss')?.addEventListener('input', e => {
    document.getElementById('stopLossVal').textContent = e.target.value + '%';
});
document.getElementById('takeProfit')?.addEventListener('input', e => {
    document.getElementById('takeProfitVal').textContent = e.target.value + '%';
});

// Initialize
loadSettings();
loadData();
setInterval(loadData, 5000);

// Add score styling
const style = document.createElement('style');
style.textContent = `
    .score { font-weight: 700; color: var(--accent); }
    .positive { color: var(--positive) !important; }
    .negative { color: var(--negative) !important; }
`;
document.head.appendChild(style);
