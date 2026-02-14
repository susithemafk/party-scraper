# 🥂 Party Scraper Hybrid Stack

A powerful event extraction tool combining Node.js for reliable web fetching and Python for advanced AI scraping.

## 🏗️ Architecture

1.  **Node.js Fetcher (Port 3001)**: Uses Puppeteer to load difficult websites and bypass CORS.
2.  **Python Scraper (Port 8000)**: Uses Crawl4AI and Gemini for intelligent data extraction.
3.  **React Frontend (Port 5173)**: Premium UI to control both engines.

## 🚀 How to Run (Three-Terminal Setup)

### 1. Start the HTML Fetcher (Node.js)

```powershell
# Open Terminal 1
cd backend-js
node server.js
```

### 2. Start the AI Scraper (Python)

```powershell
# Open Terminal 2
cd backend
..\venv\Scripts\python.exe main.py
```

### 3. Start the Frontend (React)

```powershell
# Open Terminal 3
cd frontend
pnpm dev
```

---

### How to run
on Frontend you can generate input.json to the root folder of the project.
Then when you activate virtual environment and run main.py it will read the input.json and generate output.json with the results.
`python main.py`

## 🛠️ Prerequisites

- **Node.js & pnpm**
- **Python 3.10+** (with `venv` configured)
- **Playwright Chromium**: `.\venv\Scripts\python.exe -m playwright install chromium`
- **Puppeteer Chrome**: From `backend-js`, run `npx puppeteer browsers install chrome`
- **Google Gemini API Key**: In the root `.env` file.

## 📁 Project Structure

- `/backend-js`: Node.js Puppeteer proxy for raw HTML fetching.
- `/backend`: Python FastAPI server for AI-managed extraction.
- `/frontend`: React visualization and logic center.
