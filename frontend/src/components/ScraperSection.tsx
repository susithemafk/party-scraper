import React from "react"
import { useScraper } from "../hooks/useScraper"
import { ParserFunc, ScrapedItem } from "../types"

interface ScraperSectionProps {
    title: string
    defaultUrl: string
    parserFunc: ParserFunc
}

export const ScraperSection: React.FC<ScraperSectionProps> = ({ title, defaultUrl, parserFunc }) => {
    const { url, setUrl, result, loading, copied, handleFetchAndParse, handleCopy } = useScraper(parserFunc, defaultUrl)

    return (
        <div className="scraper-section">
            <h2 className="section-title">{title}</h2>

            <div className="input-group">
                <div className="field-label">AUTOMATIC URL:</div>
                <div style={{ display: "flex", gap: "1rem", marginBottom: "0.8rem" }}>
                    <input type="text" placeholder="Enter website URL..." value={url} onChange={(e) => setUrl(e.target.value)} />
                </div>
                <div className="button-group">
                    <button onClick={handleFetchAndParse} disabled={loading} style={{ flex: 1 }}>
                        {loading && <span className="loader"></span>}
                        Fetch & Find
                    </button>
                </div>
            </div>

            {result && (
                <div className="results-section">
                    <div className="field-label result">
                        RESULT ARRAY: {result.length}
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
