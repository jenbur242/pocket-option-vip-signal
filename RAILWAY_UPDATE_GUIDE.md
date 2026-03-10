# How to Update TRADE_AMOUNT on Railway

## ⚠️ Important: Railway uses Environment Variables, not .env files

The `.env.railway` file is just a **reference**. Railway reads from its own environment variables dashboard.

## 🔧 Steps to Update TRADE_AMOUNT on Railway:

### Method 1: Railway Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Open https://railway.app
   - Select your project

2. **Open Variables Tab**
   - Click on your service
   - Click "Variables" tab

3. **Update TRADE_AMOUNT**
   - Find `TRADE_AMOUNT` variable
   - Change value from `1` to `5`
   - Click "Save" or it auto-saves

4. **Redeploy**
   - Railway will automatically redeploy
   - Or click "Redeploy" button if needed

5. **Verify in Logs**
   - Check deployment logs
   - Should see: `Initial Amount: $5.0`

### Method 2: Railway CLI

```bash
# Install Railway CLI (if not installed)
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Set variable
railway variables set TRADE_AMOUNT=5

# Redeploy
railway up
```

### Method 3: Git Push (Not Recommended for Variables)

Environment variables should be set in Railway Dashboard, not in code.

## 📋 Current Railway Variables Should Be:

```
SSID_DEMO=42["auth",{"session":"8kmju1f41cibg1vg5pihe37d7u","isDemo":1,...}]
SSID_REAL=42["auth",{"session":"a:4:{...}","isDemo":0,...}]
TELEGRAM_API_ID=28375707
TELEGRAM_API_HASH=cf54e727df04363575f8ee9f120be2c9
TELEGRAM_PHONE=+12427272924
TRADE_AMOUNT=5          ← Change this from 1 to 5
IS_DEMO=True
MULTIPLIER=2.5
MARTINGALE_STEP=0
```

## ✅ Verification

After updating and redeploying, check the logs:

```
🤖 POCKET OPTION TRADING BOT
============================================================
Channels: 2 channels
  - Test (ID: 3531425979)
  - David Cooper | Private signals (ID: 2420379150)
Account: DEMO
Initial Amount: $5.0        ← Should show $5.0 now
Multiplier: 2.5x
============================================================
```

When placing a trade:
```
💰 Trade Calculation:
   Base Amount: $5.0        ← Should show $5.0
   Multiplier: 2.5x
   Current Step: 0
   Calculated Amount: $5.00  ← First trade will be $5.00
```

## 🎯 Quick Fix

**Fastest way:**
1. Go to Railway Dashboard
2. Variables tab
3. Change `TRADE_AMOUNT` from `1` to `5`
4. Wait for auto-redeploy (or click Redeploy)
5. Done! ✅

## 📝 Note

The `.env.railway` file in your repository is just documentation. Railway doesn't read it. You must set variables in the Railway Dashboard.
