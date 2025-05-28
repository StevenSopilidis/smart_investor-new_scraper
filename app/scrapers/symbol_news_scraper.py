from typing import Optional
from app.config import settings
from app.scrapers.news_scraper import NewsScraper
from app.models.symbol_news_state import SymbolNewsState

class SymbolNewsScraper(NewsScraper):
    async def _load_state(self, symbol: Optional[str]):
        state = await self.repo.load_symbol_news_state(symbol)
        return (state.last_ts, state.next_url)
        
        
    async def _save_state(
        self, 
        last_ts: str, 
        next_url: str,
        symbol: Optional[str] = None, 
    ):
        await self.repo.set_symbol_news_state(SymbolNewsState(
            symbol=symbol,
            last_ts=last_ts,
            next_url= next_url
        ))
        
    def _build_url(
        self, 
        last_ts: str,
        symbol: Optional[str] = None,
    ):
        return (
            "https://api.polygon.io/v2/reference/news"
            f"?order=asc"
            f"&limit={self.limit}"
            f"&ticker={symbol}"
            f"&sort=published_utc"
            f"&published_utc.gte={last_ts}"
            f"&apiKey={settings.API_KEY}"
        )
                
    async def _process(
        self, 
        item: dict, 
        symbol: Optional[str] = None
    ):
        desc = item["description"]
        self.logger.info(f"Data: {desc[:10]}")