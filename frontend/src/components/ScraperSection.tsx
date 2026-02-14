import React, { useEffect } from "react"
import { useScraper } from "../hooks/useScraper"
import { ParserFunc, ScrapedItem } from "../types"

interface ScraperSectionProps {
    title: string
    defaultUrl: string
    parserFunc: ParserFunc
    triggerFetch?: number
    onResult?: (title: string, items: ScrapedItem[] | null) => void
    onlyToday: boolean
    setOnlyToday: (val: boolean) => void
}

export const ScraperSection: React.FC<ScraperSectionProps> = ({
    title,
    defaultUrl,
    parserFunc,
    triggerFetch,
    onResult,
    onlyToday,
    setOnlyToday
}) => {
    const {
        url,
        setUrl,
        htmlInput,
        setHtmlInput,
        result,
        loading,
        copied,
        filterPast,
        setFilterPast,
        maxResults,
        setMaxResults,
        handleFetchAndParse,
        handleManualParse,
        handleCopy,
    } = useScraper(parserFunc, defaultUrl, onlyToday, setOnlyToday)

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

    const isEmpty = result !== null && result.length === 0 && !loading

    return (
        <div className={`scraper-section ${isEmpty ? "empty-result" : ""}`}>
            <h2 className="section-title">{title}</h2>

            <div className="input-group">
                <div className="field-label">AUTOMATIC URL:</div>
                <div style={{ display: "flex", gap: "1rem", marginBottom: "0.8rem" }}>
                    <input type="text" placeholder="Enter website URL..." value={url} onChange={(e) => setUrl(e.target.value)} />
                </div>

                <div className="field-label">OR PASTE HTML:</div>
                <textarea
                    placeholder="Paste website source code here if automatic fetch fails..."
                    value={htmlInput}
                    onChange={(e) => setHtmlInput(e.target.value)}
                    className="manual-html-textarea"
                />

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
                    <button
                        onClick={handleManualParse}
                        disabled={!htmlInput.trim()}
                        className="secondary-button"
                        style={{ flex: 1 }}
                    >
                        Parse Manual HTML
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
