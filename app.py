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
auto_start_enabled = True  # Set to False to disable auto-start

@app.on_event("startup")
async def startup_event():
    """Auto-start bot when server starts"""
    if auto_start_enabled:
        log_message("Auto-starting bot on server startup...")
        try:
            from main import main as bot_main
            bot_task = asyncio.create_task(bot_main())
            log_message(f"Bot auto-started successfully with task ID: {id(bot_task)}")
        except Exception as e:
            log_message(f"Failed to auto-start bot: {str(e)}")
    else:
        log_message("Auto-start is disabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on server shutdown"""
    log_message("Server shutting down...")
    if bot_task and not bot_task.done():
        bot_task.cancel()
        log_message("Bot task cancelled")

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
    
    # Check if dashboard exists and is readable
    try:
        if os.path.exists(dashboard_path) and os.path.getsize(dashboard_path) > 0:
            return FileResponse(dashboard_path, media_type="text/html")
    except Exception as e:
        print(f"Error accessing dashboard: {e}")
    
    # Fallback to JSON if dashboard doesn't exist or has issues
    return {
        "status": "running", 
        "message": "Pocket Option Trading Bot API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": "railway",
        "note": "Dashboard not available - using JSON endpoint"
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
        "bot_task_done": bot_task.done() if bot_task else None,
        "auto_start_enabled": auto_start_enabled
    }

@app.get("/autostart")
async def get_autostart():
    """Get auto-start status"""
    return {
        "auto_start_enabled": auto_start_enabled,
        "message": "Auto-start is " + ("enabled" if auto_start_enabled else "disabled")
    }

@app.post("/autostart")
async def toggle_autostart():
    """Toggle auto-start on/off"""
    global auto_start_enabled
    auto_start_enabled = not auto_start_enabled
    log_message(f"Auto-start {'enabled' if auto_start_enabled else 'disabled'} via API")
    return {
        "auto_start_enabled": auto_start_enabled,
        "message": f"Auto-start {'enabled' if auto_start_enabled else 'disabled'} successfully"
    }

@app.get("/health")
async def health():
    """Health check endpoint - always returns success"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_running": bot_task is not None and not bot_task.done(),
        "service": "pocket-option-trading-bot"
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
