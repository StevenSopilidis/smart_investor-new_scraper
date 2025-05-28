from pydantic import BaseModel
from typing import Optional

class GeneralNewsState(BaseModel):
    last_ts: str
    next_url: Optional[str] = None 