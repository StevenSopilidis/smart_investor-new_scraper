from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager
from app.config import settings
from fastapi import FastAPI
from app.repo.state_repo import RedisStateRepo
from app.models.general_news_state import GeneralNewsState
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
    last_general_news_ts = state.last_general_news_ts
    next_general_news_url = state.next_general_news_url
    
    max_ts = last_general_news_ts
    
    if next_general_news_url:
        url = next_general_news_url
    else:
        url = (
                "https://api.polygon.io/v2/reference/news"
                f"?order=asc"
                f"&limit={settings.GENERAL_NEWS_SCRAPE_LIMIT}"
                f"&sort=published_utc"
                f"&published_utc.gte={last_general_news_ts}"
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
                    next_general_news_url = None
                    break

                last_general_news_ts = max_ts
                
                if pages_visited >= settings.GENERAL_NEWS_MAX_PAGES_TO_VISIT:
                    next_general_news_url = url
            
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
        
        # update general news state
        new_state = GeneralNewsState(
            last_general_news_ts=last_general_news_ts,
            next_general_news_url=next_general_news_url
        )
        await repo.set_general_news_state(new_state)
    

async def scrape_per_ticker_api():
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
    
    scheduler.add_job(
        scrape_per_ticker_api,
        IntervalTrigger(seconds=settings.PER_TICKER_SCRAPE_INTERVAL.total_seconds()),
        id="scrape_per_ticker_news_job",
        max_instances=1,
        coalesce=True,
    )