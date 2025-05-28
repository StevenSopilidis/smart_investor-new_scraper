from typing import Optional
import httpx
import logging
from app.utils.page_fetcher import fetch_pages
from app.repo.state_repo import RedisStateRepo
from app.tokenizers.tokenizer import Tokenizer
from app.config import settings

class NewsScraper:
    def __init__(
        self, 
        repo: RedisStateRepo,
        limit: int,
        page_limit: int
    ):
        self.repo = repo
        self.limit = limit
        self.page_limit = page_limit
        self.logger = logging.getLogger("uvicorn.error")
        self.tokenizer = Tokenizer(settings.TOKENIZER,settings.MAX_TOKENS_LEN)
    
    async def run(self, symbol: Optional[str] = None):
        state = await self._load_state(symbol)
        last_ts, next_url = state
        url = next_url or self._build_url(last_ts, symbol)
        max_current_ts, next_to_fetch_url = None, None
        
        async with httpx.AsyncClient() as client:
            try:
                max_current_ts, next_to_fetch_url = await fetch_pages(
                    client,
                    url,
                    self.page_limit,
                    process_item= lambda item: self._process(item, symbol)
                )
            except httpx.RequestError as re:
                self.logger.error("Network error %s", re)
            except httpx.HTTPStatusError as he:
                self.logger.error(
                    "Bad response [%d] %s",
                    he.response.status_code,
                    he,
                )
            except Exception as e:
                self.logger.exception("Unexpected error: %s", e)
                
            await self._save_state(max_current_ts or last_ts, next_to_fetch_url, symbol=symbol)
        
        
    async def _load_state(self, symbol: Optional[str]): ...
    async def _save_state(
        self, 
        last_ts: str, 
        next_url: str,
        symbol: Optional[str] = None, 
    ): ...
    def _build_url(
        self, 
        last_ts: str,
        symbol: Optional[str] = None, 
    ): ...
    async def _process(
        self, 
        item: dict, 
        symbol: Optional[str] = None
    ): ...