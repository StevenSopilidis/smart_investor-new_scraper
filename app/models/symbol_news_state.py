from pydantic import BaseModel
from typing import Optional

class SymbolNewsState(BaseModel):
    symbol: str
    last_ts: str
    next_url: Optional[str] = None 