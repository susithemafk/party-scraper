import { useState } from "react"
import axios from "axios"

export const AiProcessor = ({ inputData = [], onComplete }) => {
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [progress, setProgress] = useState({ current: 0, total: 0 })
    const [copied, setCopied] = useState(false)

    const handleProcessAi = async () => {
        if (!inputData || inputData.length === 0) return

        setLoading(true)
        setResults([])
        setProgress({ current: 0, total: inputData.length })

        const processedResults = []

        for (let i = 0; i < inputData.length; i++) {
            const item = inputData[i]
            setProgress((p) => ({ ...p, current: i + 1 }))

            try {
                const response = await axios.post("http://localhost:8000/scrape", {
                    url: item.url,
                    date: item.date,
                })

                // Keep the venue info if present in item or response
                const processedItem = {
                    ...response.data,
                    venue: response.data.place || item.venue || "Unknown Venue"
                }

                processedResults.push(processedItem)
                setResults([...processedResults])
            } catch (err) {
                console.error(`Failed to process ${item.url}:`, err)
                processedResults.push({
                    url: item.url,
                    title: "Failed to extract",
                    date: item.date,
                    error: true
                })
                setResults([...processedResults])
            }
        }

        setLoading(false)
        if (onComplete) onComplete(processedResults)
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(JSON.stringify(results, null, 4)).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        })
    }

    return (
        <div className="scraper-section ai-processor" style={{ border: "1px solid var(--primary)", background: "rgba(192, 132, 252, 0.05)" }}>
            <h2 className="section-title">AI Content Processing</h2>
            <p className="description" style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
                Send found URLs to the Gemini extraction engine.
            </p>

            <div className="input-group">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                    <div className="field-label">
                        QUEUE: <span style={{ color: "#c084fc", fontWeight: "bold" }}>{inputData.length} events</span>
                    </div>
                    {results.length > 0 && (
                        <div style={{ fontSize: "0.8rem", color: "var(--success)" }}>
                            PROCESSED: {results.length}
                        </div>
                    )}
                </div>

                {loading && (
                    <div className="progress-bar-container" style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", marginBottom: "1rem", overflow: "hidden" }}>
                        <div
                            className="progress-bar-fill"
                            style={{
                                width: `${(progress.current / progress.total) * 100}%`,
                                height: "100%",
                                background: "var(--primary)",
                                transition: "width 0.3s ease"
                            }}
                        />
                    </div>
                )}

                <button
                    onClick={handleProcessAi}
                    disabled={loading || inputData.length === 0}
                    className="fetch-all-btn"
                    style={{
                        background: loading ? "var(--text-muted)" : "linear-gradient(135deg, #c084fc 0%, #a855f7 100%)",
                        width: "100%",
                        padding: "1rem"
                    }}
                >
                    {loading ? (
                        <>
                            ⚡ Extracting {progress.current} / {progress.total}...
                        </>
                    ) : (
                        "🚀 START FULL AI EXTRACTION"
                    )}
                </button>
            </div>

            {results.length > 0 && (
                <div className="results-section" style={{ marginTop: "2rem" }}>
                    <div className="field-label result" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span>LATEST RESULTS:</span>
                        <button className="copy-btn" onClick={handleCopy} style={{ background: copied ? "var(--success)" : "rgba(255,255,255,0.1)", fontSize: "0.7rem", padding: "4px 8px" }}>
                            {copied ? "Copied!" : "Copy JSON"}
                        </button>
                    </div>

                    <div className="results-grid" style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                        gap: "10px",
                        maxHeight: "300px",
                        overflowY: "auto",
                        padding: "10px",
                        background: "rgba(0,0,0,0.2)",
                        borderRadius: "8px"
                    }}>
                        {results.map((res, idx) => (
                            <div key={idx} style={{
                                padding: "8px",
                                background: res.error ? "rgba(239, 68, 68, 0.1)" : "rgba(255,255,255,0.05)",
                                border: res.error ? "1px solid #ef4444" : "1px solid rgba(255,255,255,0.1)",
                                borderRadius: "4px",
                                fontSize: "0.8rem"
                            }}>
                                <div style={{ fontWeight: "bold", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{res.title}</div>
                                <div style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>{res.date}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
