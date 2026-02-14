const express = require("express")
const puppeteer = require("puppeteer")
const cors = require("cors")

const app = express()
const port = 3001 // Using 3001 to avoid conflict with Python backend

app.use(cors())
app.use(express.json())

// --- Pure HTML Fetcher Endpoint ---
app.post("/fetch-html", async (req, res) => {
    const { url } = req.body
    if (!url) return res.status(400).json({ error: "URL is required" })

    console.log(`[Fetcher] Requesting HTML for: ${url}`)

    let browser
    try {
        browser = await puppeteer.launch({
            headless: "new",
            args: ["--no-sandbox", "--disable-setuid-sandbox"],
        })
        const page = await browser.newPage()

        // Emulate a real browser to bypass basic bot detection
        await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        // Wait for network to be idle to ensure dynamic content is loaded
        await page.goto(url, { waitUntil: "networkidle2", timeout: 60000 })

        const html = await page.content()
        await browser.close()

        console.log(`[Fetcher] Successfully retrieved ${html.length} characters`)
        res.json({ html })
    } catch (error) {
        if (browser) await browser.close()
        console.error(`[Fetcher] Error: ${error.message}`)
        res.status(500).json({ error: error.message })
    }
})

app.get("/health", (req, res) => res.json({ status: "ok" }))

app.listen(port, () => {
    console.log(`HTML Fetcher (Node.js) running at http://localhost:${port}`)
})
