from app.models.polygon_api_data import PolygonApiData
from app.models.tokenizer_output import TokenizerOutput
from transformers import AutoTokenizer
import json

class Tokenizer:
    def __init__(self, tokenizer: str, max_len: int):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer)
        self.max_len = max_len
        
    def tokenize(self, data: PolygonApiData) -> TokenizerOutput:
        text = f"{data.title} {data.description} {''.join(data.keywords)}"
        enc = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_attention_mask=True,
            return_token_type_ids=False
        )
        
        return TokenizerOutput(
            input_ids= enc["input_ids"],
            attention_mask= enc["attention_mask"]
        )