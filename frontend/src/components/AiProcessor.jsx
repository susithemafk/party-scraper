import { useState } from "react"
import axios from "axios"

export const AiProcessor = () => {
    const [jsonInput, setJsonInput] = useState("")
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [progress, setProgress] = useState({ current: 0, total: 0 })
    const [copied, setCopied] = useState(false)

    const handleProcessAi = async () => {
        let items = []
        try {
            items = JSON.parse(jsonInput)
            if (!Array.isArray(items)) throw new Error("Input must be a JSON array")
        } catch (err) {
            alert("Invalid JSON input. Please paste an array of objects like [{url, date}, ...]")
            return
        }

        setLoading(true)
        setResults([])
        setProgress({ current: 0, total: items.length })

        const processedResults = []

        for (let i = 0; i < items.length; i++) {
            const item = items[i]
            setProgress((p) => ({ ...p, current: i + 1 }))

            try {
                const response = await axios.post("http://localhost:8000/scrape", {
                    url: item.url,
                    date: item.date,
                })
                processedResults.push(response.data)
                // Use functional update to show results appearing one by one
                setResults([...processedResults])
            } catch (err) {
                console.error(`Failed to process ${item.url}:`, err)
                processedResults.push({ url: item.url, error: "Failed to extract" })
                setResults([...processedResults])
            }
        }

        setLoading(false)
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(JSON.stringify(results, null, 4)).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        })
    }

    return (
        <div className="scraper-section ai-processor">
            <h2 className="section-title">AI Data Processor</h2>
            <p className="description" style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
                Paste a JSON array of event objects (e.g. from the output of the Fetchers above) to extract detailed information using Gemini AI.
            </p>

            <div className="input-group">
                <div className="field-label">INPUT JSON ARRAY:</div>
                <textarea
                    placeholder='[{"url": "...", "date": "..."}, ...]'
                    value={jsonInput}
                    onChange={(e) => setJsonInput(e.target.value)}
                    style={{ height: "150px", fontFamily: "monospace", fontSize: "12px" }}
                />

                <button
                    onClick={handleProcessAi}
                    disabled={loading || !jsonInput.trim()}
                    style={{ background: "linear-gradient(135deg, #c084fc 0%, #a855f7 100%)", marginTop: "1rem" }}
                >
                    {loading ? (
                        <>
                            <span className="loader"></span>
                            Processing {progress.current} / {progress.total}...
                        </>
                    ) : (
                        "Start AI Extraction"
                    )}
                </button>
            </div>

            {results.length > 0 && (
                <div className="results-section" style={{ marginTop: "2rem" }}>
                    <div className="field-label result">
                        PROCESSED RESULTS ({results.length}):
                        <button className="copy-btn" onClick={handleCopy} style={{ background: copied ? "var(--success)" : "" }}>
                            {copied ? "Copied!" : "Copy to Clipboard"}
                        </button>
                    </div>
                    <textarea readOnly value={JSON.stringify(results, null, 4)} style={{ height: "300px" }} />
                </div>
            )}
        </div>
    )
}
