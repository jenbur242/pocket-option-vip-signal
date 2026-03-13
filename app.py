import os
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
from datetime import datetime

app = FastAPI(title="Pocket Option Trading Bot", version="1.0.0")

# Global bot task
bot_task = None

@app.get("/")
async def root():
    """Serve dashboard HTML or return API info"""
    dashboard_path = "dashboard.html"
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path, media_type="text/html")
    
    # Fallback to JSON if dashboard doesn't exist
    return {
        "status": "running", 
        "message": "Pocket Option Trading Bot on Railway",
        "timestamp": datetime.now().isoformat(),
        "environment": "railway"
    }

@app.get("/api")
async def api_info():
    """API info endpoint"""
    return {
        "status": "running", 
        "message": "Pocket Option Trading Bot on Railway",
        "timestamp": datetime.now().isoformat(),
        "environment": "railway"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_running": bot_task is not None and not bot_task.done()
    }

@app.get("/start")
async def start_bot():
    global bot_task
    try:
        if bot_task and not bot_task.done():
            return {"status": "already_running", "message": "Bot is already running"}
        
        # Import and start the bot
        from main import main as bot_main
        
        # Start bot in background task
        bot_task = asyncio.create_task(bot_main())
        
        return {
            "status": "started", 
            "message": "Bot started successfully",
            "task_id": str(id(bot_task))
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/stop")
async def stop_bot():
    global bot_task
    try:
        if bot_task and not bot_task.done():
            bot_task.cancel()
            return {"status": "stopped", "message": "Bot stopped"}
        else:
            return {"status": "not_running", "message": "Bot was not running"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/status")
async def status():
    global bot_task
    if bot_task:
        if bot_task.done():
            if bot_task.exception():
                return {
                    "status": "error", 
                    "message": "Bot crashed",
                    "error": str(bot_task.exception())
                }
            else:
                return {"status": "completed", "message": "Bot completed successfully"}
        else:
            return {"status": "running", "message": "Bot is currently running"}
    else:
        return {"status": "stopped", "message": "Bot is not running"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Pocket Option Bot API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
