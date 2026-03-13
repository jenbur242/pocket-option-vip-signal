import os
import sys
from fastapi import FastAPI
from datetime import datetime

# Create FastAPI app
app = FastAPI(title="Pocket Option Trading Bot", version="1.0.0")

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
    return {
        "status": "ready",
        "message": "Bot is ready to start",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Pocket Option Bot API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
