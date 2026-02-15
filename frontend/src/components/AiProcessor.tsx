import React, { useState } from "react"
import { ScrapedItem } from "../types"

interface AiProcessorProps {
    inputData?: (ScrapedItem & { venue?: string })[]
    onComplete?: (results: Record<string, any[]>) => void
}

export const AiProcessor: React.FC<AiProcessorProps> = ({ inputData = [], onComplete }) => {
    const [results, setResults] = useState<Record<string, any[]>>({}) // Dictionary format
    const [loading, setLoading] = useState<boolean>(false)
    const [progress, setProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 })
    const [copied, setCopied] = useState<boolean>(false)

    const handleProcessAi = async () => {
        if (!inputData || inputData.length === 0) return

        setLoading(true)
        setResults({}) // Clear as dictionary
        setProgress({ current: 0, total: inputData.length })

        // Group inputData back to { Venue: [events] } for the backend
        const batchData: Record<string, { url: string; date: string | null }[]> = {}
        inputData.forEach(item => {
            const venue = item.venue || "Other"
            if (!batchData[venue]) batchData[venue] = []
            batchData[venue].push({ url: item.url, date: item.date })
        })

        let itemsCount = 0
        const currentResults: Record<string, any[]> = {}

        try {
            const response = await fetch("http://localhost:8000/scrape-batch-stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(batchData),
            })

            if (!response.body) throw new Error("No response body")

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ""

            while (true) {
                const { value, done } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split("\n")
                buffer = lines.pop() || ""

                for (const line of lines) {
                    if (!line.trim()) continue
                    try {
                        const chunk = JSON.parse(line) // Format: { "Venue": [event] }
                        const venueName = Object.keys(chunk)[0]
                        const eventData = chunk[venueName][0]

                        if (!currentResults[venueName]) currentResults[venueName] = []
                        currentResults[venueName].push(eventData)

                        setResults({ ...currentResults })
                        itemsCount++
                        setProgress(p => ({ ...p, current: itemsCount }))
                    } catch (e) {
                        console.error("Failed to parse stream line:", e)
                    }
                }
            }
        } catch (err) {
            console.error("Streaming failed:", err)
            alert("Extraction failed. Check if the backend is running.")
        } finally {
            setLoading(false)
            if (onComplete && Object.keys(currentResults).length > 0) {
                onComplete(currentResults)
            }
        }
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(JSON.stringify(results, null, 4)).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        })
    }

    const flatResults = Object.values(results).flat()

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
                    {flatResults.length > 0 && (
                        <div style={{ fontSize: "0.8rem", color: "var(--success)" }}>
                            PROCESSED: {flatResults.length}
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

            {flatResults.length > 0 && (
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
                        {flatResults.map((res: any, idx: number) => (
                            <div key={idx} style={{
                                padding: "8px",
                                background: res.error ? "rgba(239, 68, 68, 0.1)" : "rgba(255,255,255,0.05)",
                                border: res.error ? "1px solid #ef4444" : "1px solid rgba(255,255,255,0.1)",
                                borderRadius: "4px",
                                fontSize: "0.8rem"
                            }}>
                                <div style={{ fontWeight: "bold", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{res.title || "Processing..."}</div>
                                <div style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>{res.date}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
