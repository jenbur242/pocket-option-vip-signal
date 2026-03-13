import os
import sys
import asyncio
import threading
from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import Optional

# Create FastAPI app
app = FastAPI(title="Pocket Option Trading Bot", version="1.0.0")

# Global bot task
bot_task = None
bot_thread = None

@app.get("/")
async def root():
    """Root endpoint for Railway health check"""
    return {
        "status": "running", 
        "message": "Pocket Option Trading Bot on Railway",
        "timestamp": datetime.now().isoformat(),
        "environment": "railway",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "pocket-option-bot"
    }

@app.get("/status")
async def status():
    """Status endpoint"""
    global bot_task
    
    bot_status = {
        "status": "ready",
        "message": "Bot is ready to start",
        "timestamp": datetime.now().isoformat(),
        "bot_running": False,
        "bot_task_id": None
    }
    
    if bot_task:
        if bot_task.done():
            if bot_task.exception():
                bot_status["status"] = "error"
                bot_status["message"] = "Bot crashed"
                bot_status["error"] = str(bot_task.exception())
            else:
                bot_status["status"] = "completed"
                bot_status["message"] = "Bot completed successfully"
        else:
            bot_status["status"] = "running"
            bot_status["message"] = "Bot is currently running"
            bot_status["bot_running"] = True
            bot_status["bot_task_id"] = str(id(bot_task))
    
    return bot_status

@app.get("/start")
async def start_bot():
    """Start the trading bot"""
    global bot_task, bot_thread
    
    try:
        if bot_task and not bot_task.done():
            return {
                "status": "already_running", 
                "message": "Bot is already running",
                "task_id": str(id(bot_task))
            }
        
        # Import and start the bot
        from main import main as bot_main
        
        # Start bot in background task
        bot_task = asyncio.create_task(bot_main())
        
        return {
            "status": "started", 
            "message": "Bot started successfully",
            "task_id": str(id(bot_task)),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/stop")
async def stop_bot():
    """Stop the trading bot"""
    global bot_task
    
    try:
        if bot_task and not bot_task.done():
            bot_task.cancel()
            return {
                "status": "stopped", 
                "message": "Bot stopped successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "not_running", 
                "message": "Bot was not running",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/restart")
async def restart_bot():
    """Restart the trading bot"""
    # First stop
    stop_result = await stop_bot()
    
    # Wait a moment
    await asyncio.sleep(1)
    
    # Then start
    start_result = await start_bot()
    
    return {
        "status": "restarted",
        "message": "Bot restart completed",
        "stop_result": stop_result,
        "start_result": start_result,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/endpoints")
async def list_endpoints():
    """List all available endpoints"""
    return {
        "status": "success",
        "endpoints": [
            {
                "path": "/",
                "method": "GET",
                "description": "Root endpoint - API info"
            },
            {
                "path": "/health",
                "method": "GET", 
                "description": "Health check endpoint"
            },
            {
                "path": "/status",
                "method": "GET",
                "description": "Bot status endpoint"
            },
            {
                "path": "/start",
                "method": "GET",
                "description": "Start the trading bot"
            },
            {
                "path": "/stop",
                "method": "GET",
                "description": "Stop the trading bot"
            },
            {
                "path": "/restart",
                "method": "GET",
                "description": "Restart the trading bot"
            },
            {
                "path": "/endpoints",
                "method": "GET",
                "description": "List all available endpoints"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/info")
async def api_info():
    """Get detailed API information"""
    return {
        "status": "success",
        "api": {
            "name": "Pocket Option Trading Bot API",
            "version": "1.0.0",
            "environment": "railway",
            "framework": "FastAPI",
            "language": "Python"
        },
        "bot": {
            "status": "ready" if not bot_task else ("running" if not bot_task.done() else "completed"),
            "task_id": str(id(bot_task)) if bot_task else None,
            "auto_start": False
        },
        "features": [
            "Telegram signal monitoring",
            "PocketOption trading integration",
            "Martingale strategy",
            "Real-time balance tracking",
            "Trade history logging"
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Pocket Option Bot API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
