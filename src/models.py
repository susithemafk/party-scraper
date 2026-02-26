"""
Models - Pydantic data models for the party scraper.
Reused from src/models.py
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class EventDetail(BaseModel):
    title: str = Field(..., description="Název akce/párty")
    date: Optional[str] = Field(None, description="Datum akce ve formátu RRRR-MM-DD")
    time: Optional[str] = Field(None, description="Čas začátku akce")
    place: Optional[str] = Field(None, description="Název klubu/místa konání")
    price: Optional[str] = Field(None, description="Cena vstupného")
    description: Optional[str] = Field(None, description="Stručný popis akce")
    image_url: Optional[str] = Field(None, description="URL hlavního obrázku/plakátu")


class ScrapedItem(BaseModel):
    url: str
    date: Optional[str] = None
