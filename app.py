import os
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

app = FastAPI(title="Pocket Option Trading Bot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot task
bot_task = None

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": f"Validation error: {str(exc)}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": f"Internal server error: {str(exc)}"}
    )

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

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "status": "success",
        "message": "API is working correctly",
        "timestamp": datetime.now().isoformat(),
        "bot_task_exists": bot_task is not None,
        "bot_task_done": bot_task.done() if bot_task else None
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_running": bot_task is not None and not bot_task.done()
    }

def log_message(message: str):
    """Simple logging function"""
    print(f"[BOT] {datetime.now().isoformat()} - {message}")

@app.get("/start")
async def start_bot():
    """Start the trading bot"""
    global bot_task
    try:
        if bot_task and not bot_task.done():
            return {"status": "already_running", "message": "Bot is already running"}
        
        # Test import first
        try:
            from main import main as bot_main
            log_message("Successfully imported main bot function")
        except ImportError as e:
            return {"status": "error", "message": f"Cannot import main bot: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Import error: {str(e)}"}
        
        # Start bot in background task
        try:
            bot_task = asyncio.create_task(bot_main())
            return {
                "status": "started", 
                "message": "Bot started successfully",
                "task_id": str(id(bot_task))
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to start bot: {str(e)}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}

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
