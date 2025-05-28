from pydantic import BaseModel
from typing import List

class TokenizerOutput(BaseModel):
    input_ids: List[int]
    attention_mask: List[int]