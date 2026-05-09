const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const crypto = require('crypto');

const PORT = 8083;
const API_KEY = 'QPM55JoNnHSV7C7PllgNbTAxpzy9RaBjoKprgHuIE9GJUeQoVIGu69ICPnmBXp61';
const API_SECRET = 'BSOTWqsVsncRk13DMDJ2YDRQks8XvrajArQDPW2jY8sDwNtcgb5da8H3x6qF3hJk';
const PROXY = 'http://172.29.144.1:7897';

function sign(query) {
    return crypto.createHmac('sha256', API_SECRET).update(query).digest('hex');
}

function curl(url) {
    try {
        const cmd = `curl -s --proxy "${PROXY}" -H "X-MBX-APIKEY: ${API_KEY}" "${url}"`;
        const result = execSync(cmd, { timeout: 10000 });
        return JSON.parse(result.toString());
    } catch (e) {
        return { error: e.message };
    }
}

function getBalances() {
    const ts = Date.now();
    const query = `timestamp=${ts}`;
    const sig = sign(query);
    
    // Spot
    let spot = {};
    try {
        const data = curl(`https://api.binance.com/api/v3/account?${query}&signature=${sig}`);
        if (data.balances) {
            for (const b of data.balances) {
                const total = parseFloat(b.free) + parseFloat(b.locked);
                if (total > 0) {
                    spot[b.asset] = { free: parseFloat(b.free), locked: parseFloat(b.locked), total };
                }
            }
        }
    } catch (e) {}
    
    // Futures
    let futures = {};
    try {
        const data = curl(`https://fapi.binance.com/fapi/v2/balance?${query}&signature=${sig}`);
        if (Array.isArray(data)) {
            for (const b of data) {
                const bal = parseFloat(b.balance || 0);
                if (bal > 0) {
                    futures[b.asset] = { balance: bal, available: parseFloat(b.availableBalance || 0) };
                }
            }
        }
    } catch (e) {}
    
    // Margin
    let margin = {};
    try {
        const data = curl(`https://api.binance.com/sapi/v1/margin/account?${query}&signature=${sig}`);
        margin = {
            totalCollateralValue: parseFloat(data.totalCollateralValueInUSDT || 0),
            marginLevel: data.marginLevel || 'N/A'
        };
    } catch (e) {}
    
    return { spot, futures, margin };
}

function getTrades() {
    try {
        return JSON.parse(fs.readFileSync('/tmp/g12_plus_trades.json', 'utf8')).slice(-30);
    } catch (e) { return []; }
}

function getStats() {
    try {
        return JSON.parse(fs.readFileSync('/tmp/g12_daily_stats.json', 'utf8'));
    } catch (e) { return {}; }
}

const server = http.createServer((req, res) => {
    if (req.url === '/api/g12_data') {
        res.writeHead(200, {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'});
        const balances = getBalances();
        const data = { ...balances, trades: getTrades(), stats: getStats() };
        res.end(JSON.stringify(data));
    } else {
        const file = path.join('/home/goose/.openclaw/workspace/g12_webui', req.url === '/' ? 'index.html' : req.url);
        fs.readFile(file, (err, content) => {
            if (err) { res.writeHead(404); res.end('Not found'); return; }
            res.writeHead(200);
            res.end(content);
        });
    }
});

server.listen(PORT, () => console.log('Server on port ' + PORT));
