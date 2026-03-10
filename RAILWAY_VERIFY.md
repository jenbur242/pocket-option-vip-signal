# Railway Environment Variable Verification

## 🔍 Step-by-Step Verification

### Step 1: Check Railway Dashboard

1. Go to https://railway.app
2. Open your project
3. Click on your service
4. Click **"Variables"** tab
5. Take a screenshot or note down EXACTLY what you see for `TRADE_AMOUNT`

**What do you see?**
- [ ] TRADE_AMOUNT = 1
- [ ] TRADE_AMOUNT = 5
- [ ] TRADE_AMOUNT = "5"
- [ ] TRADE_AMOUNT = '5'
- [ ] TRADE_AMOUNT doesn't exist

### Step 2: Check Railway Logs

1. Click **"Deployments"** tab
2. Click on the latest deployment
3. Look for these lines in the logs:

```
🔍 DEBUG: TRADE_AMOUNT environment variable = '?'
```

**What does it show?**
- Write down the exact value: _______________

### Step 3: Common Issues

#### Issue 1: Variable has quotes
❌ Wrong: `TRADE_AMOUNT = "5"` or `TRADE_AMOUNT = '5'`
✅ Correct: `TRADE_AMOUNT = 5`

**Fix:** Remove quotes in Railway Dashboard

#### Issue 2: Variable name is wrong
❌ Wrong: `TRADEAMOUNT`, `Trade_Amount`, `trade_amount`
✅ Correct: `TRADE_AMOUNT` (exact case)

**Fix:** Delete wrong variable, add correct one

#### Issue 3: Variable not saved
Sometimes Railway doesn't save the change.

**Fix:** 
1. Delete the variable completely
2. Add it again: `TRADE_AMOUNT` = `5`
3. Force redeploy

#### Issue 4: Old deployment still running
Railway might be running an old deployment.

**Fix:**
1. Go to Deployments tab
2. Click "Redeploy" on latest
3. Or make a small change and push to git

### Step 4: Force Update Method

If nothing works, try this:

1. **Delete the variable:**
   - Go to Variables tab
   - Find TRADE_AMOUNT
   - Click the X or delete button
   - Confirm deletion

2. **Add it fresh:**
   - Click "New Variable"
   - Name: `TRADE_AMOUNT`
   - Value: `5`
   - Save

3. **Force redeploy:**
   - Go to Deployments
   - Click "Redeploy"

4. **Check logs:**
   - Look for: `TRADE_AMOUNT environment variable = '5'`

### Step 5: Alternative - Use Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Check current value
railway variables

# Delete old variable
railway variables delete TRADE_AMOUNT

# Set new variable
railway variables set TRADE_AMOUNT=5

# Verify
railway variables

# Redeploy
railway up
```

### Step 6: Nuclear Option - Environment File

If Railway variables are not working, we can hardcode it temporarily:

Edit `telegram/main.py` line 41:
```python
# Temporary hardcode for Railway
def get_trade_amount():
    """Get current trade amount from environment"""
    amount = os.getenv('TRADE_AMOUNT', '5.0')  # Changed default to 5.0
    return float(amount)
```

This makes the default 5.0 instead of 1.0.

## 🐛 Debugging Checklist

- [ ] Checked Railway Variables tab - TRADE_AMOUNT exists
- [ ] Value is exactly `5` (no quotes, no spaces)
- [ ] Variable name is exactly `TRADE_AMOUNT` (case-sensitive)
- [ ] Redeployed after changing variable
- [ ] Checked logs for `TRADE_AMOUNT environment variable = '5'`
- [ ] Checked logs for `Initial Amount: $5.0`
- [ ] Checked logs for `Base Amount (from .env): $5.00`

## 📸 What to Share

If still not working, share:

1. **Screenshot of Railway Variables tab** showing TRADE_AMOUNT
2. **Railway logs** showing these lines:
   ```
   🔍 DEBUG: TRADE_AMOUNT environment variable = '?'
   TRADE_AMOUNT (raw): ?
   Initial Amount: $?
   ```
3. **Deployment status** - Is it the latest deployment?

## ⚡ Quick Test

Add this to your Railway service and run it:

```bash
echo $TRADE_AMOUNT
```

This will show you exactly what Railway sees.

Or add a new file `test_env.py`:
```python
import os
print(f"TRADE_AMOUNT = {os.getenv('TRADE_AMOUNT', 'NOT SET')}")
```

Then in Railway, run:
```bash
python test_env.py
```
