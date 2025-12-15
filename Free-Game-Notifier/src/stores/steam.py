import aiohttp
from bs4 import BeautifulSoup
from typing import Optional
from .base import BaseStore, FreeGame


class SteamStore(BaseStore):
    SEARCH_URL = "https://store.steampowered.com/search/"
    
    @property
    def name(self) -> str:
        return "Steam"
    
    async def get_free_games(self) -> list[FreeGame]:
        free_games = []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "maxprice": "free",
                    "specials": "1",
                    "cc": "us"
                }
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cookie": "birthtime=0; mature_content=1"
                }
                
                async with session.get(self.SEARCH_URL, params=params, headers=headers) as response:
                    if response.status != 200:
                        print(f"Steam search returned status {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    search_results = soup.select("#search_resultsRows a.search_result_row")
                    
                    for result in search_results[:20]:
                        free_game = await self._parse_search_result(result, session)
                        if free_game:
                            free_games.append(free_game)
        
        except Exception as e:
            print(f"Error fetching Steam games: {e}")
        
        return free_games
    
    async def _parse_search_result(self, result, session: aiohttp.ClientSession) -> Optional[FreeGame]:
        try:
            url = result.get("href", "")
            if not url:
                return None
            
            title_elem = result.select_one(".title")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Game"
            
            discount_pct_elem = result.select_one(".discount_pct")
            if not discount_pct_elem:
                return None
            
            discount_text = discount_pct_elem.get_text(strip=True)
            if "-100%" not in discount_text:
                return None
            
            original_price = None
            discount_elem = result.select_one(".discount_original_price")
            if discount_elem:
                original_price = discount_elem.get_text(strip=True)
            
            if not original_price:
                return None
            
            final_price_elem = result.select_one(".discount_final_price")
            if final_price_elem:
                final_price = final_price_elem.get_text(strip=True).lower()
                if "free" not in final_price and final_price != "$0.00":
                    return None
            
            image_elem = result.select_one("img")
            image_url = image_elem.get("src") if image_elem else None
            
            description = f"Originally {original_price} - Now 100% OFF!"
            
            return FreeGame(
                title=title,
                description=description,
                store=self.name,
                url=url,
                image_url=image_url,
                original_price=original_price,
                end_date=None
            )
        
        except Exception as e:
            print(f"Error parsing Steam result: {e}")
            return None
