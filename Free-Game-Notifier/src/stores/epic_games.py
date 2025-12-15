import aiohttp
from datetime import datetime
from typing import Optional
from .base import BaseStore, FreeGame


class EpicGamesStore(BaseStore):
    API_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    
    @property
    def name(self) -> str:
        return "Epic Games Store"
    
    async def get_free_games(self) -> list[FreeGame]:
        free_games = []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "locale": "en-US",
                    "country": "US",
                    "allowCountries": "US"
                }
                
                async with session.get(self.API_URL, params=params) as response:
                    if response.status != 200:
                        print(f"Epic Games API returned status {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    elements = data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
                    
                    for game in elements:
                        if self._is_currently_free(game):
                            free_game = self._parse_game(game)
                            if free_game:
                                free_games.append(free_game)
        
        except Exception as e:
            print(f"Error fetching Epic Games: {e}")
        
        return free_games
    
    def _is_currently_free(self, game: dict) -> bool:
        promotions = game.get("promotions")
        if not promotions:
            return False
        
        promotional_offers = promotions.get("promotionalOffers", [])
        
        for offer_group in promotional_offers:
            for offer in offer_group.get("promotionalOffers", []):
                discount_percentage = offer.get("discountSetting", {}).get("discountPercentage", 0)
                if discount_percentage == 0:
                    start_date = offer.get("startDate")
                    end_date = offer.get("endDate")
                    
                    if start_date and end_date:
                        now = datetime.utcnow()
                        start = datetime.fromisoformat(start_date.replace("Z", "+00:00")).replace(tzinfo=None)
                        end = datetime.fromisoformat(end_date.replace("Z", "+00:00")).replace(tzinfo=None)
                        
                        if start <= now <= end:
                            return True
        
        return False
    
    def _parse_game(self, game: dict) -> Optional[FreeGame]:
        try:
            title = game.get("title", "Unknown Game")
            description = game.get("description", "No description available")
            
            slug = game.get("productSlug") or game.get("urlSlug") or ""
            if game.get("offerType") == "BUNDLE":
                url = f"https://store.epicgames.com/en-US/bundles/{slug}"
            else:
                url = f"https://store.epicgames.com/en-US/p/{slug}"
            
            image_url = None
            key_images = game.get("keyImages", [])
            for img in key_images:
                if img.get("type") in ["Thumbnail", "OfferImageWide", "DieselStoreFrontWide"]:
                    image_url = img.get("url")
                    break
            if not image_url and key_images:
                image_url = key_images[0].get("url")
            
            original_price = None
            price_info = game.get("price", {}).get("totalPrice", {})
            if price_info:
                original = price_info.get("originalPrice", 0)
                if original > 0:
                    original_price = f"${original / 100:.2f}"
            
            end_date = None
            promotions = game.get("promotions", {})
            promotional_offers = promotions.get("promotionalOffers", [])
            for offer_group in promotional_offers:
                for offer in offer_group.get("promotionalOffers", []):
                    if offer.get("discountSetting", {}).get("discountPercentage") == 0:
                        end_str = offer.get("endDate")
                        if end_str:
                            end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00")).replace(tzinfo=None)
                            break
            
            return FreeGame(
                title=title,
                description=description[:200] + "..." if len(description) > 200 else description,
                store=self.name,
                url=url,
                image_url=image_url,
                original_price=original_price,
                end_date=end_date
            )
        
        except Exception as e:
            print(f"Error parsing Epic game: {e}")
            return None
