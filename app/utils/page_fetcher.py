import httpx
from typing import Callable, Awaitable, Tuple
from app.config import settings

async def fetch_pages(
    client: httpx.AsyncClient, 
    initial_url: str,
    page_limit: int,
    process_item: Callable[[dict], Awaitable[None]]
) -> Tuple[str, str]:
    """
    Function that fetches data in pages
    
    Parameters
    -----
        client: client that will be used to fetch data
        initial_url: initial url from which we start fetching
        page_limit: max number of pages we will fetch per job call
        process_item: callback that will process results we got
        
    Returns:
    -----
        max_ts, next_url: max timestamp inquired and next_url to fetch in next job turn
    """
    url = initial_url
    pages = 0
    max_ts = None
    next_url = None

    while url and pages < page_limit:
        pages += 1
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        
        results = data.get("results", [])
        if not results:
            break

        for item in results:
            pub = item["published_utc"]
            max_ts = pub if not max_ts or pub > max_ts else max_ts
            await process_item(item)

        raw_next = data.get("next_url")
        if raw_next:
            joiner = "&" if "?" in raw_next else "?"
            next_url = raw_next if "apiKey=" in raw_next else f"{raw_next}{joiner}apiKey={settings.API_KEY}"
            url = next_url
        else:
            url = None
            
    joiner = "&" if "?" in next_url else "?"
    url = (
        next_url
        if "apiKey=" in next_url
        else f"{next_url}{joiner}apiKey={settings.API_KEY}"
    )

    return max_ts, url