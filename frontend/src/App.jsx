import { useState } from "react"
import axios from "axios"
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

    const parseHtmlAndSetResult = (htmlString) => {
        console.log(htmlString)
        const parser = new DOMParser()
        const doc = parser.parseFromString(htmlString, "text/html")

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

    const handleManualParse = () => {
        if (!htmlInput.trim()) return
        parseHtmlAndSetResult(htmlInput)
    }

    // Uses the NEW /fetch-html endpoint + Axios + Client-side finding
    const handleFetchAndParse = async () => {
        if (!url.trim()) return
        setLoading(true)
        setResult(null)

        try {
            const response = await axios.post("http://localhost:3001/fetch-html", { url })
            const html = response.data.html
            parseHtmlAndSetResult(html)
        } catch (err) {
            console.error(err)
            const msg = err.response?.data?.detail || err.message
            alert(`Fetch failed: ${msg}`)
        } finally {
            setLoading(false)
        }
    }

    // Original AI-based scraping
    const handleAiScrape = async () => {
        if (!url.trim()) return
        setLoading(true)
        setResult(null)

        try {
            const response = await axios.post("http://localhost:8000/scrape", { url })
            setResult(response.data)
        } catch (err) {
            console.error(err)
            const msg = err.response?.data?.detail || err.message
            alert(`AI Scrape failed: ${msg}`)
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
                    <div className="field-label">AUTOMATIC URL:</div>
                    <div style={{ display: "flex", gap: "1rem", marginBottom: "0.8rem" }}>
                        <input type="text" placeholder="e.g., https://artbar.club/program/" value={url} onChange={(e) => setUrl(e.target.value)} />
                    </div>
                    <div className="button-group">
                        <button onClick={handleFetchAndParse} disabled={loading} style={{ flex: 1 }}>
                            {loading && <span className="loader"></span>}
                            Fetch & Find (JS Library)
                        </button>
                        <button
                            onClick={handleAiScrape}
                            disabled={loading}
                            style={{ flex: 1, background: "linear-gradient(135deg, #c084fc 0%, #a855f7 100%)" }}
                        >
                            {loading && <span className="loader"></span>}
                            AI Data Extraction (Gemini)
                        </button>
                    </div>
                </div>

                <div style={{ borderTop: "1px solid var(--border)", paddingTop: "1.5rem" }}>
                    <div className="field-label">MANUAL UL PARSE:</div>
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
