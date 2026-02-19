Let's recreate this application so the frontend nor backend doesn't have to be running.
Create a new folder called "party-scraper-backend-full". In this folder there will be main.py for running the script. The logic will be in "party-scraper-backend-full/src" folder. Each part of logic will have its own file in the "src" folder. The main.py will import these files and run the them.

Application will have this logic:

1. ensure everything is installed and set up correctly (playwright, env, python packages, etc.)
2. take a list of scrapers with their custom parser's logic (each in their own file in the "src/parsers" folder) and scrape the HTML of each website as in @app.post("/fetch-html") and the parse the HTML as in useScraper hook.

```ts
const VENUES = [
  {
    title: "Bobyhall",
    url: "https://bobyhall.cz/program-bobyhall/",
    baseUrl: "https://bobyhall.cz/",
    parser: bobyhallParser,
  },
  {
    title: "Fraktal",
    url: "https://ra.co/clubs/224489/events",
    baseUrl: "https://ra.co/",
    parser: raParser,
  },
  {
    title: "pul.pit",
    url: "https://ra.co/clubs/206733/events",
    baseUrl: "https://ra.co/",
    parser: raParser,
  },
  {
    title: "Metro Music Bar",
    url: "https://www.metromusic.cz/program/",
    baseUrl: "https://www.metromusic.cz/",
    parser: metroParser,
  },
  {
    title: "První patro",
    url: "https://patrobrno.cz/",
    baseUrl: "https://patrobrno.cz/",
    parser: patroParser,
  },
  {
    title: "Perpetuum",
    url: "https://www.perpetuumklub.cz/program/",
    baseUrl: "https://www.perpetuumklub.cz/",
    parser: perpetuumParser,
  },
  {
    title: "Fléda",
    url: "https://www.fleda.cz/program/",
    baseUrl: "https://www.fleda.cz/",
    parser: fledaParser,
  },
  {
    title: "Sono Music Club",
    url: "https://www.sono.cz/program/",
    baseUrl: "https://www.sono.cz/",
    parser: sonoParser,
  },
  {
    title: "Kabinet Múz",
    url: "https://www.kabinetmuz.cz/program",
    baseUrl: "https://www.kabinetmuz.cz/",
    parser: kabinetParser,
  },
  {
    title: "Artbar",
    url: "https://www.artbar.club/shows",
    baseUrl: "https://www.artbar.club/",
    parser: artbarParser,
  },
]
```

3. after all the data is scraped and parsed, it will be saved to a JSON file in the "temp" folder. The file will be named "fetched-events.json". Events will be formatted as an array of objects, each object will have the following structure:

```json
{
    "Artbar": [
        {
            "url": "https://www.fairplay.events/en/caramel-and-petrofski-krest-2026-f4a1",
            "date": "2026-02-19"
        },
        ...
    ],
    ...
}
```

4. run AI scraper for each of the URL as in @app.post("/scrape-batch-stream") and save the results to "temp/processed-events.json" in the following format:

```json
{
  "Artbar": [
    {
      "title": "CARAMEL & PETROFSKI",
      "date": "2026-02-19",
      "time": "20:00",
      "place": "ARTBAR, Brno-st\u0159ed",
      "price": "CZK 200 - CZK 250",
      "description": "Chladn\u00e1 cela bez oken jako alegorie um\u00edraj\u00edc\u00edho vztahu dvou lid\u00ed. Nedok\u00e1\u017e\u00ed spolu \u017e\u00edt, z\u00e1rove\u0148 ale jeden nen\u00ed schopen opustit toho druh\u00e9ho. \nPo singlu _TESCO nominovan\u00e9ho na cenu APOLLO_ v kategorii singl roku **vyd\u00e1vaj\u00ed Brn\u011bn\u0161t\u00ed smutn\u00ed kluci Caramel spolu s Petrofskim dal\u0161\u00ed spole\u010dn\u00fd projekt s videoklipem.**\nP\u0159ij\u010fte na jedine\u010dn\u00fd **dvojit\u00fd k\u0159est do ArtBaru** a za\u017eijte **multi\u017e\u00e1nrov\u00fd ve\u010der** na vln\u00e1ch synth-popu a novoromantismu v kontrastu se syrov\u00fdm post punkem a indie rockem.",
      "image_url": "https://www.fairplay.events/_next/image?url=https%3A%2F%2Fstorage.googleapis.com%2Ffairplay-qrcodes%2Fevents%2Ff9ddf60f-7d46-4c81-afd3-d9d3a8da00e8.webp&w=750&q=75"
    }
  ]
}
```

5. use html2image in python to create images from the HTML of each event following this tutorial:

```plaintext
If you don't want your project to depend on wkhtmltopdf, like other Python modules use, I recommend html2image.

You can get it using the pip install html2image command. A web browser shall also be installed on your machine (Chrome/Chromium or Edge for now).

Once installed, you can take a screenshot of an HTML string like so:

from html2image import Html2Image
hti = Html2Image()

html = '<h1> A title </h1> Some text.'
css = 'body {background: red;}'

# screenshot an HTML string (css is optional)
hti.screenshot(html_str=html, css_str=css, save_as='page.png')
```

6. save the images to "temp/images" folder with the following structure:

```plaintext
temp/
    images/
        Artbar/
            caramel-petrofski.png
            ...
        Bobyhall/
            ...
        ...
```

7. that is all. 

CRITICAL! 
follow already implemented logic, parsers, url parsers, etc. as much as possible. Do not change the logic if it's not necessary. The goal is to make the application work without the need of running the frontend or backend separately, not to change the logic of the application.


CRITICAL!
create tests for each part of the logic with example input and expected output. 

CRITICAL!
filter venues for only today before using crawl4ai. 

CRITICAL!
always run python static analysis after editing a python file. 

CRITICAL!
always first enter the virtual environment using `.\venv\Scripts\activate` before running any python command.

