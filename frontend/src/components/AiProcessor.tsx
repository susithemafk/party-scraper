import React, { useState } from "react"
import axios from "axios"
import { ScrapedItem, ProcessedResult } from "../types"

interface AiProcessorProps {
    inputData?: ScrapedItem[]
}

export const AiProcessor: React.FC<AiProcessorProps> = ({ inputData = [] }) => {
    const [results, setResults] = useState<ProcessedResult[]>([])
    const [loading, setLoading] = useState<boolean>(false)
    const [progress, setProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 })
    const [copied, setCopied] = useState<boolean>(false)

    const testApi = async () => {
        try {
            const response = await axios.get("http://localhost:8000/health")
            console.log("API Test Response:", response.data)
        } catch (err) {
            console.error("API Test Error:", err)
        }
    }

    const testScrape = async () => {
        try {
            const response = await axios.post("http://localhost:8000/scrape", {
                date: "2026-02-14",
                url: "https://www.artbar.club/events/cze-vs-sui",
            })
            console.log("Test Scrape Response:", response.data)
        } catch (err) {
            console.error("Test Scrape Error:", err)
        }
    }

    const handleProcessAi = async () => {
        if (!inputData || inputData.length === 0) return

        setLoading(true)
        setResults([])
        setProgress({ current: 0, total: inputData.length })

        const processedResults: ProcessedResult[] = []

        for (let i = 0; i < inputData.length; i++) {
            const item = inputData[i]
            setProgress((p) => ({ ...p, current: i + 1 }))

            try {
                const response = await axios.post("http://localhost:8000/scrape", {
                    url: item.url,
                    date: item.date,
                })
                processedResults.push(response.data)
                setResults([...processedResults])
            } catch (err: any) {
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
            <button onClick={testApi} style={{ marginBottom: "1rem" }}>
                Test API Connection
            </button>
            <button onClick={testScrape} style={{ marginBottom: "1rem", marginLeft: "1rem" }}>
                Test Scrape Function
            </button>

            <h2 className="section-title">AI Data Processor</h2>
            <p className="description" style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
                This section automatically collects events found by the fetchers above and uses Gemini AI to extract full details.
            </p>

            <div className="input-group">
                <div className="field-label">
                    READY TO PROCESS: <span style={{ color: "#c084fc" }}>{inputData.length} items</span>
                </div>

                {inputData.length > 0 && (
                    <div className="items-preview">
                        {inputData.map((item, idx) => (
                            <div key={idx} className="preview-row">
                                {item.date} - {item.url}
                            </div>
                        ))}
                    </div>
                )}

                <button
                    onClick={handleProcessAi}
                    disabled={loading || inputData.length === 0}
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
