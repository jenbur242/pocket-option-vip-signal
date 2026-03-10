# Fix TRADE_AMOUNT on Railway - Step by Step

## 🎯 Problem
Bot is trading with $1 instead of $5 on Railway deployment.

## 🔍 Root Cause
Railway environment variable `TRADE_AMOUNT` is still set to `1`, not `5`.

## ✅ Solution (3 Simple Steps)

### Step 1: Open Railway Dashboard
1. Go to https://railway.app
2. Login to your account
3. Click on your project (pocket-option-bot)

### Step 2: Update Environment Variable
1. Click on your service/deployment
2. Click the **"Variables"** tab (top menu)
3. Find the variable named `TRADE_AMOUNT`
4. Click on the value (currently shows `1`)
5. Change it to `5`
6. Press Enter or click outside to save

### Step 3: Verify Deployment
1. Railway will automatically redeploy (wait 1-2 minutes)
2. Click "Deployments" tab
3. Click on the latest deployment
4. Check the logs - you should see:

```
🤖 POCKET OPTION TRADING BOT
============================================================
TRADE_AMOUNT (raw): 5
Initial Amount: $5.0
Multiplier: 2.5x
============================================================
```

## 🔍 How to Verify It's Working

### In Railway Logs:
Look for these lines when bot starts:
```
TRADE_AMOUNT (raw): 5          ← Should show 5, not 1
Initial Amount: $5.0           ← Should show $5.0, not $1.0
```

### When Placing a Trade:
```
💰 Trade Calculation:
   Base Amount: $5.0           ← Should be $5.0
   Multiplier: 2.5x
   Current Step: 0
   Calculated Amount: $5.00    ← First trade = $5.00
```

## ⚠️ Important Notes

1. **Railway doesn't read .env files** - It uses its own environment variables
2. **The .env.railway file is just documentation** - You must set variables in Railway Dashboard
3. **Changes require redeploy** - Railway auto-redeploys when you change variables
4. **Check the logs** - Always verify in deployment logs that the correct value is loaded

## 🐛 Still Not Working?

If you still see $1 after updating:

1. **Check Railway Variables Again**
   - Make sure `TRADE_AMOUNT` shows `5` (not `1`)
   - No quotes needed, just the number: `5`

2. **Force Redeploy**
   - Go to Deployments tab
   - Click "Redeploy" button

3. **Check Logs for Warnings**
   - Look for: `⚠️ WARNING: TRADE_AMOUNT not set in environment!`
   - Or: `⚠️ WARNING: TRADE_AMOUNT is set to 1.0`

4. **Run Diagnostic**
   - Add `railway_diagnostic.py` to your deployment
   - Run it to see exact environment values

## 📸 Visual Guide

```
Railway Dashboard
├── Your Project
│   ├── Service/Deployment
│   │   ├── Variables Tab ← Click here
│   │   │   ├── TRADE_AMOUNT: 1  ← Change this
│   │   │   │   └── Click value → Type 5 → Enter
│   │   │   ├── IS_DEMO: True
│   │   │   ├── MULTIPLIER: 2.5
│   │   │   └── ...
│   │   └── Deployments Tab ← Check logs here
```

## ✅ Success Checklist

- [ ] Opened Railway Dashboard
- [ ] Found Variables tab
- [ ] Changed TRADE_AMOUNT from 1 to 5
- [ ] Saved (auto-saves)
- [ ] Waited for redeploy
- [ ] Checked logs - shows "Initial Amount: $5.0"
- [ ] First trade placed with $5.00

## 🎉 Done!

Once you see `Initial Amount: $5.0` in the logs, your bot is correctly configured!
