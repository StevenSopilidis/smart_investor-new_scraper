import aioredis
from app.config import settings
from app.models.general_news_state import GeneralNewsState
import logging

class RedisStateRepo:
    def __init__(self):
        self._redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        self._logger = logging.getLogger("uvicorn.error")

        
    async def is_connected(self) -> bool:
        try:
            pong = await self._redis.ping()
            if pong is True:
                self._logger.info("connected to redis successfully")
            return pong is True
        except Exception as e:
            self._logger.error(f"could not connect to redis {e}")
            return False
        
    async def load_general_news_state(self) -> GeneralNewsState:
        pipe = self._redis.pipeline()
        pipe.get("general_news:last_ts")
        pipe.get("general_news:next_url")
        last_ts, next_url = await pipe.execute()
        
        if last_ts is None:
            last_ts = "1970-01-01T00:00:00Z"
            
        return GeneralNewsState(
            last_general_news_ts=last_ts,
            next_general_news_url=next_url
        )
    
    async def set_general_news_state(self, state: GeneralNewsState):
        pipe = self._redis.pipeline()
        
        pipe.set("general_news:last_ts", state.last_general_news_ts)
        if state.next_general_news_url:
            pipe.set("general_news:next_url", state.next_general_news_url)
        else:
            pipe.delete("general_news:next_url")
        await pipe.execute()            
        