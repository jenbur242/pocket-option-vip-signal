# Pocket Option Trading Bot

Automated trading bot for Pocket Option with Telegram signal integration and modern web interface.

## Features

- 🤖 Automated trading based on Telegram signals
- 📊 Martingale strategy with customizable parameters
- 🌐 Modern web dashboard with real-time updates
- 📈 Live trade monitoring and performance charts
- 🔄 Support for Demo and Real accounts
- ☁️ Railway deployment ready with persistent storage
- 💾 Automatic backups to Railway bucket storage

## Quick Start (Local)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
python api.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

4. Use the web dashboard to start the bot and monitor trades!

## Railway Deployment 🚀

### One-Click Deployment:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for Railway deployment"
   git push
   ```

2. **Deploy on Railway:**
   - Connect your GitHub repository to Railway
   - Railway will automatically detect and deploy the app
   - The web dashboard will be available at your Railway URL

### Environment Variables (Railway):

Set these in Railway Dashboard > Variables:
```
TRADE_AMOUNT=5.0
MULTIPLIER=2.5
IS_DEMO=true
INITIAL_BALANCE=10000.0
```

## Web Dashboard Features

### 🎮 Bot Control
- Start/Stop bot with one click
- Real-time status monitoring
- Connection status indicators

### 📊 Trading Overview
- Live balance display
- Win rate statistics
- Total trades counter
- Last signal received

### 📈 Performance Charts
- Balance over time visualization
- Trade history with results
- Win/loss ratio tracking

### 📋 Live Monitoring
- Real-time trade updates
- Live log streaming
- Recent trades list
- Automatic data refresh

### 💾 Data Management
- Create backups to Railway storage
- Persistent log storage
- Trade history in CSV format
- Session file management

## API Endpoints

- `GET /` - Web dashboard
- `GET /status` - Bot status
- `POST /start` - Start bot
- `POST /stop` - Stop bot
- `GET /trades` - Recent trades
- `GET /balance` - Current balance
- `GET /logs` - Live logs
- `POST /backup` - Create backup
- `GET /health` - Health check

## Configuration

The bot uses environment variables for configuration:

- **TRADE_AMOUNT**: Base trade amount (default: 5.0)
- **MULTIPLIER**: Martingale multiplier (default: 2.5)
- **IS_DEMO**: Use demo account (true/false)
- **INITIAL_BALANCE**: Starting balance for tracking

## Storage Structure (Railway)

```
/tmp/
├── logs/telegram/     # Trading logs
├── sessions/          # Session backups
├── csv/              # Trade history CSV
└── trades/           # Trade data
```

## Frontend Design

The web dashboard features:
- **Modern UI**: Built with Tailwind CSS
- **Responsive Design**: Works on all devices
- **Real-time Updates**: Auto-refresh every 5 seconds
- **Interactive Charts**: Chart.js for performance visualization
- **Glass Morphism**: Modern frosted glass effects
- **Dark Theme**: Easy on the eyes
- **Smooth Animations**: Professional transitions

## Railway Storage Integration

- **Persistent Logs**: All logs stored in Railway bucket
- **Automatic Backups**: Session and trade data backed up
- **CSV Exports**: Trade history downloadable
- **Session Management**: Telegram sessions stored safely

## Disclaimer

⚠️ This bot is for educational purposes. Trading involves risk. Always test with demo account first and never trade more than you can afford to lose.

## Support

For issues and questions:
- Check the live logs in the web dashboard
- Use the health check endpoint: `/health`
- Review Railway deployment logs
