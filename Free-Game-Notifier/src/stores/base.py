from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class FreeGame:
    title: str
    description: str
    store: str
    url: str
    image_url: Optional[str] = None
    original_price: Optional[str] = None
    end_date: Optional[datetime] = None
    
    def __hash__(self):
        return hash((self.title, self.store))
    
    def __eq__(self, other):
        if isinstance(other, FreeGame):
            return self.title == other.title and self.store == other.store
        return False


class BaseStore(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def get_free_games(self) -> list[FreeGame]:
        pass
