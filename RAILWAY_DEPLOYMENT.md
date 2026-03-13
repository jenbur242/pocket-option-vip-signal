# Railway Deployment Guide for Pocket Option Trading Bot

## Files Created for Railway Deployment

1. **app.py** - FastAPI web server for Railway
2. **Procfile** - Railway process configuration
3. **railway.json** - Railway deployment settings
4. **requirements.txt** - Python dependencies
5. **.env.example** - Environment variables template

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Railway deployment files"
git push origin main
```

### 2. Connect Railway to GitHub
1. Go to [Railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python project

### 3. Configure Environment Variables
In Railway dashboard, add these environment variables:

#### Required Variables:
```
TRADE_AMOUNT=5.0
MULTIPLIER=2.5
IS_DEMO=true
```

#### Optional Variables (if not hardcoded):
```
API_ID=34506083
API_HASH=5676893fa1c0fe15eca5dbbceb3ab6a2
PHONE_NUMBER=+12428018500
STRING_SESSION=your_session_string_here
SSID_DEMO=your_demo_ssid_here
SSID_REAL=your_real_ssid_here
```

### 4. Deploy
1. Click "Deploy" button
2. Railway will build and deploy your app
3. Wait for deployment to complete

### 5. Test Deployment
Once deployed, test these endpoints:
- `https://your-app.railway.app/` - Status check
- `https://your-app.railway.app/health` - Health check
- `https://your-app.railway.app/start` - Start the bot
- `https://your-app.railway.app/status` - Check bot status
- `https://your-app.railway.app/stop` - Stop the bot

## Troubleshooting

### Common Issues:

1. **Build Fails** - Check requirements.txt for incompatible packages
2. **Runtime Error** - Check Railway logs for missing environment variables
3. **Bot Crashes** - Check `/status` endpoint for error messages
4. **Port Issues** - Railway automatically sets PORT variable

### Railway Logs:
- Go to your project dashboard
- Click "Logs" tab
- Check for error messages during startup

### Memory Issues:
- Railway provides 512MB RAM by default
- Monitor memory usage in logs
- Upgrade plan if needed

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | App status and info |
| `/health` | GET | Health check |
| `/start` | GET | Start trading bot |
| `/stop` | GET | Stop trading bot |
| `/status` | GET | Check bot status |

## Security Notes

- Never commit real credentials to GitHub
- Use Railway environment variables for sensitive data
- Railway provides SSL certificates automatically
- Monitor logs for any authentication issues

## Performance

- Bot runs in background task
- Web server remains responsive
- Automatic restarts on crashes
- Health checks for monitoring

## Support

If deployment fails:
1. Check Railway logs first
2. Verify all environment variables are set
3. Ensure requirements.txt is correct
4. Check this guide for common issues
