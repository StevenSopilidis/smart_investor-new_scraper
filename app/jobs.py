from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager
from app.config import settings
from fastapi import FastAPI
from app.repo.state_repo import RedisStateRepo
from app.models.general_news_state import GeneralNewsState
from app.models.symbol_news_state import SymbolNewsState
import httpx
import logging

logger = logging.getLogger("uvicorn.error")
repo = RedisStateRepo()

async def scrape_general_api():
    connected = await repo.is_connected()
    if not connected:
        logger.error("Could not connect to redis repo")
        return
    
    state = await repo.load_general_news_state()
    last_ts = state.last_general_news_ts
    next_url = state.next_general_news_url
    
    max_ts = last_ts
    
    if next_url:
        url = next_url
    else:
        url = (
                "https://api.polygon.io/v2/reference/news"
                f"?order=asc"
                f"&limit={settings.GENERAL_NEWS_SCRAPE_LIMIT}"
                f"&sort=published_utc"
                f"&published_utc.gte={last_ts}"
                f"&apiKey={settings.API_KEY}"
        )
    
    pages_visited = 0
    
    async with httpx.AsyncClient() as client:
        while url and pages_visited < settings.GENERAL_NEWS_MAX_PAGES_TO_VISIT:
            try:
                pages_visited += 1
                
                # get data
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    break

                for item in results:
                    pub = item["published_utc"]
                    
                    if not max_ts or pub > max_ts:
                        max_ts = pub
                        
                    # TODO process data

                # prepare next page
                raw_next = data.get("next_url")
                if raw_next:
                    # re-attach apiKey if missing
                    joiner = "&" if "?" in raw_next else "?"
                    url = (
                        raw_next
                        if "apiKey=" in raw_next
                        else f"{raw_next}{joiner}apiKey={settings.API_KEY}"
                    )
                else:
                    url = None
                    next_url = None
                    break

                last_ts = max_ts
                
                if pages_visited >= settings.GENERAL_NEWS_MAX_PAGES_TO_VISIT:
                    next_url = url
            
            except httpx.RequestError as re:
                logger.error("Network error on page %d: %s", pages_visited, re)
                break
            except httpx.HTTPStatusError as he:
                logger.error(
                    "Bad response [%d] on page %d: %s",
                    he.response.status_code,
                    pages_visited,
                    he,
                )
                break
            except Exception as e:
                logger.exception("Unexpected error on page %d", pages_visited)
                break
        
        # update general news statep
        new_state = GeneralNewsState(
            last_general_news_ts=last_ts,
            next_general_news_url=next_url
        )
        await repo.set_general_news_state(new_state)
    

async def scrape_per_ticker_api(symbol: str):
    connected = await repo.is_connected()
    if not connected:
        logger.error("Could not connect to redis repo")
        return
    
    state = await repo.load_symbol_news_state(symbol)
    last_ts = state.last_symbol_news_ts
    next_url = state.next_symbol_news_url
    
    max_ts = last_ts
    
    if next_url:
        url = next_url
    else:
        url = (
                "https://api.polygon.io/v2/reference/news"
                f"?order=asc"
                f"&limit={settings.GENERAL_NEWS_SCRAPE_LIMIT}"
                f"&ticker={symbol}"
                f"&sort=published_utc"
                f"&published_utc.gte={last_ts}"
                f"&apiKey={settings.API_KEY}"
        )
    
    pages_visited = 0
    
    async with httpx.AsyncClient() as client:
        while url and pages_visited < settings.PER_TICKER_NEWS_SCRAPE_LIMIT:
            try:
                pages_visited += 1
                
                # get data
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    break

                for item in results:
                    pub = item["published_utc"]
                    
                    if not max_ts or pub > max_ts:
                        max_ts = pub
                        
                    # TODO process data

                # prepare next page
                raw_next = data.get("next_url")
                if raw_next:
                    # re-attach apiKey if missing
                    joiner = "&" if "?" in raw_next else "?"
                    url = (
                        raw_next
                        if "apiKey=" in raw_next
                        else f"{raw_next}{joiner}apiKey={settings.API_KEY}"
                    )
                else:
                    url = None
                    next_url = None
                    break

                last_ts = max_ts
                
                if pages_visited >= settings.PER_TICKER_NEWS_SCRAPE_LIMIT:
                    next_url = url
                
            except httpx.RequestError as re:
                logger.error("Network error on page %d: %s for symbol: %s", pages_visited, re, symbol)
                break
            except httpx.HTTPStatusError as he:
                logger.error(
                    "Bad response [%d] on page %d: %s for symbol: %s",
                    he.response.status_code,
                    pages_visited,
                    he,
                    symbol
                )
                break
            except Exception as e:
                logger.exception("Unexpected error on page %d for symbol: %s", pages_visited, symbol)
                break
        
        new_state = SymbolNewsState(
            symbol=symbol,
            last_symbol_news_ts=last_ts,
            next_symbol_news_url=next_url
        )
        await repo.set_symbol_news_state(new_state)

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