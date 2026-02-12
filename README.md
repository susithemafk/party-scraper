# Party Scraper Publisher

A Python based tool to scrape party event details from URLs and extract structured data using Google Gemini.

## Setup

1.  **Install Dependencies**:

```bash
py -3.12 -m venv venv
.\venv\Scripts\activate
where.exe python
pip install -r ./requirements.txt
```

_Note: You may need to run `playwright install` or similar if Crawl4AI requires it, depending on your system._

2.  **Environment Variables**:

- Rename `.env` (or create one) and add your Gemini API Key:

```
GEMINI_API_KEY=your_actual_api_key
```

1.  **Input Data**:

- Edit `input.json` to add the venues and URLs you want to scrape.

```json
{
    "VenueName": [{ "date": "2026-01-01", "url": "https://..." }]
}
```

## Usage

Run the main script:

```bash
python main.py
```

Results will be saved to `output.json`.

## Python usage

To use Python in venv you need to activate it first:

```bash
.\venv\Scripts\activate
```

To deactivate it:

```bash
deactivate
```

## Testing

```bash
py -3.12 -m pytest -s -vv .\tests\test_extraction.py
```

-s: prints stdout
-vv: verbose verbose

execution_number is to run test multiple times
