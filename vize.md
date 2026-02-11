Aplikace pro shromáždění dat o akcích, diskotékách, párty.

Zjednodušený postup:

1. vstup manuálně vyplním a bude obsahovat název místa a pro každé místo URL a datum

```json
{
    "Artbar": [
        {
            "date": "2026-02-11",
            "url": "https://www.smsticket.cz/vstupenky/66140-living-room-deltawelle-de-drying-cactus-artbar-brno"
        }
    ],
    "Melodka": []
}
```

1. scraper projde jednotlivé URL a shromáždí data o akcích a vrátí výstup

```python
	class EventDetail(BaseModel):
		title: str = Field(..., description="Název akce/párty")
		date: str = Field(..., description="Datum akce ve formátu RRRR-MM-DD")
		time: str = Field(..., description="Čas začátku akce")
		place: str = Field(..., description="Název klubu/místa konání")
		price: Optional[str] = Field(None, description="Cena vstupného")
		description: str = Field(..., description="Stručný popis akce")
		image_url: Optional[str] = Field(None, description="URL hlavního obrázku/plakátu")
```
