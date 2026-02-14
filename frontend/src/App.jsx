import { useState } from "react"
import "./App.css"

function App() {
    const [url, setUrl] = useState("")
    const [htmlInput, setHtmlInput] = useState("")
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [copied, setCopied] = useState(false)

    const formatCzechDate = (dateStr) => {
        if (!dateStr) return null
        const match = dateStr.match(/(\d+)\.\s*(\d+)\./)
        if (!match) return dateStr

        const day = match[1].padStart(2, "0")
        const month = match[2].padStart(2, "0")
        const year = new Date().getFullYear()

        return `${year}-${month}-${day}`
    }

    const handleManualParse = () => {
        if (!htmlInput.trim()) return

        const parser = new DOMParser()
        const doc = parser.parseFromString(htmlInput, "text/html")

        const events = Array.from(doc.querySelectorAll('a[data-hook="ev-rsvp-button"]'))
            .map((btn) => {
                const container = btn.closest(".TYl3A7") || btn.closest(".LbqWhj") || btn.parentElement
                const dateEl = container ? container.querySelector('[data-hook="short-date"]') : null
                const rawDate = dateEl ? dateEl.textContent.trim() : null

                return {
                    date: formatCzechDate(rawDate),
                    url: btn.getAttribute("href"),
                }
            })
            .filter((event) => event.url !== null)

        const uniqueEvents = Array.from(new Map(events.map((e) => [e.url, e])).values())
        setResult(uniqueEvents)
    }

    const handleAutoScrape = async () => {
        if (!url.trim()) return
        setLoading(true)
        setResult(null)

        try {
            const response = await fetch("http://localhost:8000/scrape", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url }),
            })

            if (!response.ok) throw new Error("Scrape failed")

            const data = await response.json()
            setResult(data)
        } catch (err) {
            console.error(err)
            alert("Failed to scrape. Make sure the backend (FastAPI) is running on port 8000.")
        } finally {
            setLoading(false)
        }
    }

    const handleCopy = () => {
        if (!result) return
        navigator.clipboard.writeText(JSON.stringify(result, null, 4)).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        })
    }

    return (
        <div className="container">
            <h1>Party Scraper</h1>
            <p className="subtitle">Automated Event Intelligence</p>

            <div className="input-section">
                <div>
                    <div className="field-label">AUTOMATIC URL SCRAPE:</div>
                    <div style={{ display: "flex", gap: "1rem" }}>
                        <input type="text" placeholder="e.g., https://artbar.club/program/" value={url} onChange={(e) => setUrl(e.target.value)} />
                        <button onClick={handleAutoScrape} disabled={loading}>
                            {loading && <span className="loader"></span>}
                            {loading ? "Scraping..." : "Go"}
                        </button>
                    </div>
                </div>

                <div style={{ borderTop: "1px solid var(--border)", paddingTop: "1.5rem" }}>
                    <div className="field-label">OR MANUAL UL PARSE (ARTBAR):</div>
                    <textarea placeholder="Paste <ul>...</ul> here..." value={htmlInput} onChange={(e) => setHtmlInput(e.target.value)} />
                    <button className="secondary-btn" onClick={handleManualParse}>
                        Process Manual HTML
                    </button>
                </div>
            </div>

            {result && (
                <div className="results-section">
                    <div className="field-label result">
                        RESULT ARRAY:
                        <button className="copy-btn" onClick={handleCopy} style={{ background: copied ? "var(--success)" : "" }}>
                            {copied ? "Copied!" : "Copy to Clipboard"}
                        </button>
                    </div>
                    <textarea readOnly value={JSON.stringify(result, null, 4)} />
                </div>
            )}
        </div>
    )
}

export default App
