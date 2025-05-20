from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager
from app.config import settings
from fastapi import FastAPI


async def scrape_general_api():
    print("hallo")
    pass

async def scrape_per_ticker_api():
    pass

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_scrape_jobs()
    
    scheduler.start()
    print("---> Scheduler started")
    
    yield
    
    scheduler.shutdown(wait=False)
    print("---> Scheduler shut down")


def run_scrape_jobs():
    scheduler.add_job(
        scrape_general_api,
        IntervalTrigger(seconds=settings.GENERAL_NEWS_SCRAPE_INTERVAL.total_seconds()),
        id="scrape_general_news_job",
        max_instances=1,
        coalesce=True,
    )
    
    scheduler.add_job(
        scrape_per_ticker_api,
        IntervalTrigger(seconds=settings.PER_TICKER_SCRAPE_INTERVAL.total_seconds()),
        id="scrape_per_ticker_news_job",
        max_instances=1,
        coalesce=True,
    )