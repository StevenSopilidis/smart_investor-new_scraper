from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager
from app.config import settings
from fastapi import FastAPI
from app.repo.state_repo import RedisStateRepo
from app.models.general_news_state import GeneralNewsState
from app.models.symbol_news_state import SymbolNewsState
from app.utils.page_fetcher import fetch_pages
from app.scrapers.general_news_scraper import GeneralNewsScraper
from app.scrapers.symbol_news_scraper import SymbolNewsScraper
import httpx
import logging

repo = RedisStateRepo()
general_scraper = GeneralNewsScraper(
    repo, 
    settings.GENERAL_NEWS_SCRAPE_LIMIT, 
    settings.GENERAL_NEWS_MAX_PAGES_TO_VISIT
)
symbol_scraper = SymbolNewsScraper(
    repo,
    settings.PER_TICKER_NEWS_SCRAPE_LIMIT,
    settings.PER_TICKER_MAX_PAGES_TO_VISIT
)
logger = logging.getLogger("uvicorn.error")


async def scrape_general_api():
    await general_scraper.run()
    pass
    

async def scrape_per_ticker_api(symbol: str):
    await symbol_scraper.run(symbol)
    pass
    

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_scrape_jobs()
    
    scheduler.start()
    logger.info("Scheduler started")
    
    yield
    
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")


def run_scrape_jobs():
    scheduler.add_job(
        scrape_general_api,
        IntervalTrigger(seconds=settings.GENERAL_NEWS_SCRAPE_INTERVAL.total_seconds()),
        id="scrape_general_news_job",
        max_instances=1,
        coalesce=True,
    )
    # TODO get all active symbols from symbol manager service
    
    symbols = {"NVDA"}
    for symbol in symbols:
        scheduler.add_job(
            scrape_per_ticker_api,
            IntervalTrigger(seconds=settings.PER_TICKER_SCRAPE_INTERVAL.total_seconds()),
            id=f"scrape_{symbol}_news_job",
            max_instances=1,
            coalesce=True,
            args=[symbol]
        )