import pytest
from src.scraper import process_batch


@pytest.mark.asyncio
@pytest.mark.parametrize('execution_number', range(2))
async def test_batch_extraction(execution_number):
    input_data = {
        "Artbar": [
            # {
            #     "date": "2026-02-12",
            #     "url": "https://www.artbar.club/events/cze-vs-can",
            #     "actions": []
            # },
            # {
            #     "date": "2026-02-13",
            #     "url": "https://www.artbar.club/events/cze-vs-fra",
            #     "actions": []
            # },
            # {
            #     "date": "2026-02-13",
            #     "url": "https://www.eventlook.cz/udalosti/g-1-nter-brno-artbar-xzrnwo/",
            #     "actions": [],
            #     "image_selector": "span.wrapper > img"
            # },
            {
                "date": "2026-02-14",
                "url": "https://tootoot.fm/cs/events/69723fa66a0b507c25949d26",
                "image_selector": "div.main-img"
            }
        ]
    }

    results = await process_batch(input_data)

    assert "Artbar" in results
    artbar_events = results["Artbar"]
    assert len(artbar_events) == 1

    # # Event 1: CZE vs CAN
    # ev1 = next(e for e in artbar_events if "CZE vs CAN" in e["title"])
    # assert ev1["date"] == "2026-02-12"
    # assert "ARTBAR" in ev1["place"].upper()
    # assert ev1["image_url"].startswith(
    #     "https://static.wixstatic.com/media/5af6c7_5d96a76eebb745baba772d08d8fdf5b3")

    # # Event 2: CZE vs FRA
    # ev2 = next(e for e in artbar_events if "CZE vs FRA" in e["title"])
    # assert ev2["date"] == "2026-02-13"
    # assert "ARTBAR" in ev2["place"].upper()
    # assert ev2["image_url"].startswith(
    #     "https://static.wixstatic.com/media/5af6c7_a5f336ad43f54c67988df418fa7c54b0")

    # # Event 3: Eventlook G1nter
    # ev3 = next(e for e in artbar_events if "G1nter" in e["title"])
    # assert ev3["date"] == "2026-02-13"
    # assert "ARTBAR" in ev3["place"].upper()
    # assert "playboi-carti-5-png-etayja.png" in ev3["image_url"]

    # Event 4: Tootoot 13K Tour
    ev4 = next(e for e in artbar_events if "13K TOUR" in e["title"])
    assert ev4["date"] == "2026-02-14"
    assert "ARTBAR" in ev4["place"].upper()
    assert "https://ttcdn.b-cdn.net/images/Event/69723fa66a0b507c25949d26/c9823cd7-88b7-4d40-a45f-38a3c693808a.jpg" in ev4[
        "image_url"]
