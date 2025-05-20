from pydantic import BaseModel
from typing import Optional

class GeneralNewsState(BaseModel):
    last_general_news_ts: str
    next_general_news_url: Optional[str] = None 