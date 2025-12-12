import asyncio
import logging
from app.log_config import setup_logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from app.config import settings
from app.bot.handlers import router


setup_logging()
logger = logging.getLogger(__name__)

redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True 
)

storage = RedisStorage(redis=redis)

bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
dp = Dispatcher(storage=storage)

dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Controls the starting and stopping of background tasks.
    """
    logger.info("Starting up bot polling...")
    
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield  

    logger.info("Shutting down...")
    
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        logger.info("Bot polling stopped gracefully")

    await bot.session.close()
    
    await redis.aclose()
    
    logger.info("All connections closed. Bye!")


app = FastAPI(
    title="Abc Tech HR Bot",
    description="AI-Powered Recruiter Bot with Resume Parsing",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", status_code=200)
async def health_check():
    """
    A simple endpoint to check that the service is alive.
    """
    try:
        await redis.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "down"

    return {
        "status": "ok",
        "bot_mode": "polling",
        "redis": redis_status
    }