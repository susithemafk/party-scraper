import React, { useEffect } from "react"
import { useScraper } from "../hooks/useScraper"
import { ParserFunc, ScrapedItem } from "../types"

interface ScraperSectionProps {
    title: string
    defaultUrl: string
    parserFunc: ParserFunc
    triggerFetch?: number
    onResult?: (title: string, items: ScrapedItem[] | null) => void
}

export const ScraperSection: React.FC<ScraperSectionProps> = ({ title, defaultUrl, parserFunc, triggerFetch, onResult }) => {
    const {
        url,
        setUrl,
        result,
        loading,
        copied,
        filterPast,
        setFilterPast,
        onlyToday,
        setOnlyToday,
        maxResults,
        setMaxResults,
        handleFetchAndParse,
        handleCopy,
    } = useScraper(parserFunc, defaultUrl)

    useEffect(() => {
        if (triggerFetch && triggerFetch > 0) {
            handleFetchAndParse()
        }
    }, [triggerFetch, handleFetchAndParse])

    useEffect(() => {
        if (onResult) {
            onResult(title, result)
        }
    }, [result, onResult, title])

    return (
        <div className="scraper-section">
            <h2 className="section-title">{title}</h2>

            <div className="input-group">
                <div className="field-label">AUTOMATIC URL:</div>
                <div style={{ display: "flex", gap: "1rem", marginBottom: "0.8rem" }}>
                    <input type="text" placeholder="Enter website URL..." value={url} onChange={(e) => setUrl(e.target.value)} />
                </div>

                <div className="filter-controls">
                    <label>
                        <input type="checkbox" checked={filterPast} onChange={(e) => setFilterPast(e.target.checked)} />
                        Hide Past Events
                    </label>
                    <label>
                        <input type="checkbox" checked={onlyToday} onChange={(e) => setOnlyToday(e.target.checked)} />
                        Only Today
                    </label>
                    <label>
                        <span>Max results:</span>
                        <input
                            type="number"
                            value={maxResults}
                            onChange={(e) => setMaxResults(parseInt(e.target.value) || 0)}
                        />
                    </label>
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
