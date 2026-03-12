# Session Management System

## Overview

The Pocket Option Trading Bot now includes an automatic session management system that handles Telegram sessions securely and efficiently.

## Features

### 🔄 Automatic Session Cleanup
- **24-Hour Expiration**: Sessions automatically expire after 24 hours of inactivity
- **Background Service**: Runs cleanup every hour to remove expired sessions
- **Safe Deletion**: Only removes expired sessions, active sessions remain intact

### 📱 .env File Only Configuration
- **No Hardcoded Credentials**: All Telegram credentials come from `.env` file only
- **Secure Storage**: Phone, API ID, and API Hash stored in environment variables
- **Error Handling**: Clear error messages if `.env` is not configured

### 🗂️ Session Tracking
- **Session Registry**: Tracks all session files with creation and access times
- **File Monitoring**: Monitors session file sizes and existence
- **Activity Logging**: Records all cleanup activities for debugging

### 🌐 Railway & Local Storage
- **Dual Storage**: Data stored both locally and for Railway deployment
- **Cleanup Logs**: All cleanup activities logged to `cleanup_log.json`
- **Session Tracker**: Session metadata stored in `session_tracker.json`

## File Structure

```
├── session_cleanup.py      # Session cleanup service
├── startup.py              # Main startup script
├── session_tracker.json    # Session metadata (auto-created)
├── cleanup_log.json        # Cleanup activity log (auto-created)
├── po_vip_testing.session # Telegram session file (user-created)
└── .env                    # Environment configuration
```

## Environment Variables (.env)

Required Telegram credentials:
```env
TELEGRAM_API_ID=28375707
TELEGRAM_API_HASH=cf54e727df04363575f8ee9f120be2c9
TELEGRAM_PHONE=+12427272924
```

## Usage

### Starting the Bot

```bash
# Start all services (recommended)
python startup.py

# Or start individually
python session_cleanup.py &  # Background cleanup
python api_server.py          # API server
```

### Session Management Commands

```bash
# Check session status
python session_cleanup.py status

# Manual cleanup
python session_cleanup.py cleanup

# Register a session
python session_cleanup.py register po_vip_testing.session +12427272924

# Update session access time
python session_cleanup.py update po_vip_testing.session
```

### Frontend Features

- **Session Status Display**: View all active sessions and expiration times
- **Manual Cleanup Button**: Clean expired sessions from the web interface
- **Browser Storage**: Sessions cached in browser for faster loading
- **OTP Management**: Create and restore sessions with OTP verification

## Session Lifecycle

1. **Creation**: User creates session via OTP verification
2. **Registration**: Session automatically registered with cleanup system
3. **Active Period**: Session remains active for 24 hours from last access
4. **Expiration**: Session marked as expired after 24 hours
5. **Cleanup**: Expired sessions automatically deleted during next cleanup cycle

## Security Features

- **No Hardcoded Credentials**: All credentials from `.env` file only
- **Automatic Expiration**: Sessions expire after 24 hours for security
- **Secure Storage**: Session files stored securely with proper permissions
- **Activity Tracking**: All session activities logged for audit

## Railway Deployment

The system works seamlessly on Railway with:
- **Environment Variables**: Use Railway environment variables for credentials
- **Persistent Storage**: Session data stored in Railway's persistent storage
- **Auto-Cleanup**: Sessions automatically cleaned up even on Railway
- **Logs**: Cleanup logs available in Railway logs

## Troubleshooting

### Session Not Working
1. Check `.env` file has correct Telegram credentials
2. Verify session file exists: `po_vip_testing.session`
3. Check session status: `python session_cleanup.py status`

### Cleanup Not Running
1. Check if cleanup service is running
2. Restart with: `python startup.py`
3. Manual cleanup: `python session_cleanup.py cleanup`

### Frontend Issues
1. Clear browser storage and refresh
2. Check API server is running
3. Verify `.env` configuration

## API Endpoints

- `GET /api/sessions/status` - Get session status
- `POST /api/sessions/cleanup` - Manual cleanup
- `GET /api/telegram/check-session` - Check Telegram session
- `POST /api/telegram/send-code` - Send OTP code
- `POST /api/telegram/verify-otp` - Verify OTP and create session

## Benefits

✅ **Security**: No hardcoded credentials, automatic expiration
✅ **Convenience**: Auto-cleanup, browser storage for fast loading  
✅ **Reliability**: Background service, dual storage, activity logging
✅ **Flexibility**: Manual cleanup options, session status monitoring
✅ **Deployment Ready**: Works on Railway and local environments
