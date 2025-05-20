from pydantic import BaseModel
from typing import Optional

class SymbolNewsState(BaseModel):
    symbol: str
    last_symbol_news_ts: str
    next_symbol_news_url: Optional[str] = None 