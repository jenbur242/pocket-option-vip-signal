import asyncio
import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "running", "message": "Pocket Option Trading Bot on Railway"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/start")
async def start_bot():
    try:
        # Import and start the main bot
        from main import main as bot_main
        # Run bot in background
        asyncio.create_task(bot_main())
        return {"status": "bot_started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
