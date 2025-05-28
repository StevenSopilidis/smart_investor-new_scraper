from pydantic import BaseModel
from typing import List

class PolygonApiData(BaseModel):
    title: str
    description: str
    keywords: List[str]
    
def extract_data(data: dict) -> PolygonApiData:
    api_data = PolygonApiData(
        title= data["title"],
        description= data["description"],
        keywords= data["keywords"] if "keywords" in data.keys() else [],
    )
    
    return api_data