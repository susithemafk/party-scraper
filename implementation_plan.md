# Implementation Plan - Party Scraper Publisher

## Goal Description

Implement a Python-based scraper that takes a list of URLs for party events (grouped by venue), scrapes the content using **Crawl4AI**, and extracts structured event details using **Google Gemini**. The system will follow the simplified vision provided in `vize.md`.

## User Review Required

> [!IMPORTANT]
> **Gemini API Key**: You will need a valid Google Gemini API key. Please ensure you have one ready to put into the `.env` file.

> [!NOTE]
> **Input Format**: The application will expect a `input.json` file in the root directory with the manual entry structure defined in your vision.

## Proposed Changes

### Project Structure

The project will be structured as follows:

```text
party-scraper-publisher/
├── input.json            # Manual input file
├── .env                  # Environment variables (API Key)
├── requirements.txt      # Dependencies
├── main.py               # Entry point
└── src/
    ├── __init__.py
    ├── models.py         # Pydantic models (EventDetail)
    ├── scraper.py        # Crawl4AI logic
    └── extractor.py      # Gemini extraction logic
```

### 1. Project Initialization

- Create a virtual environment and install dependencies:
    - `crawl4ai` (for scraping)
    - `google-generativeai` (for Gemini)
    - `pydantic` (for data validation)
    - `python-dotenv` (for config)
    - `asyncio` (for async execution)
- Setup `.gitignore` and `.env`.

### 2. Data Models (`src/models.py`)

- Implement the `EventDetail` class using `pydantic`.
- Define the input schema (optional, but good for validation) to match the JSON structure: `Dict[str, List[EventInput]]`.

### 3. Extraction Logic (`src/extractor.py`)

- Initialize the Gemini client.
- Create a prompt that accepts the HTML/Markdown content from Crawl4AI.
- Use Gemini to extract the JSON matching `EventDetail` from the content.

### 4. Scraper Logic (`src/scraper.py`)

- Initialize `AsyncWebCrawler` from `crawl4ai`.
- Create a function to process a single URL:
    1.  Crawl the URL to get markdown/clean HTML.
    2.  Pass the content to the `extractor`.
    3.  Return the structured `EventDetail`.
- Implement a batch processor to handle the structure from `input.json`.

### 5. Main Execution (`main.py`)

- Load `input.json`.
- Iterate through venues and events.
- Run the scraper for each URL.
- Collect results.
- Output the final structured data (e.g., print to console or save to `output.json`).

## Verification Plan

### Automated Tests

- We will create a simple validation script that checks if `EventDetail` correctly validates a sample JSON.

### Manual Verification

1.  **Setup**: Install dependencies and add `GEMINI_API_KEY` to `.env`.
2.  **Input**: Create `input.json` with the example provided in `vize.md`.
3.  **Run**: Execute `python main.py`.
4.  **Verify**: Check that the output contains the extracted details (Title, Date, Time, Place, etc.) for the provided URL.
