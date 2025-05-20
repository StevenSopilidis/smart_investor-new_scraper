from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from datetime import timedelta

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    PROJECT_NAME: str = "news_scraper"
    VERSION: str = "0.1.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8080
    DEBUG: bool = True
    
    API_KEY: str
    
    PER_TICKER_SCRAPE_INTERVAL: timedelta = Field(
        default=timedelta(minutes=10),
        description="Interval between scraping news per symbol"
    )
    PER_TICKER_NEWS_SCRAPE_LIMIT: int = 10
    
    GENERAL_NEWS_SCRAPE_INTERVAL: timedelta = Field(
        default=timedelta(seconds=10),
        description="Interval between scraping general news"   
    )
    GENERAL_NEWS_MAX_PAGES_TO_VISIT : int = 30
    GENERAL_NEWS_SCRAPE_LIMIT: int = 10
    
settings = Settings()